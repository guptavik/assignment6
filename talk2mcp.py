import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
from concurrent.futures import TimeoutError
from functools import partial
import json

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

max_iterations = 5
last_response = None
iteration = 0
iteration_response = []

async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        print("LLM generation completed")
        return response
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise

def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

async def main():
    reset_state()  # Reset at the start of main
    print("Starting main execution...")
    try:
        # Create a single MCP server connection
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["example2.py"]
        )

        try:
            async with stdio_client(server_params) as (read, write):
                print("Connection established, creating session...")
                async with ClientSession(read, write) as session:
                    print("Session created, initializing...")
                    await session.initialize()
                
                    # Get available tools
                    print("Requesting tool list...")
                    tools_result = await session.list_tools()
                    tools = tools_result.tools
                    print(f"Successfully retrieved {len(tools)} tools")

                    # Create system prompt with available tools
                    print("Creating system prompt...")
                    print(f"Number of tools: {len(tools)}")
                    
                    try:
                        # First, let's inspect what a tool object looks like
                        tools_description = []
                        for i, tool in enumerate(tools):
                            try:
                                # Get tool properties
                                params = tool.inputSchema
                                desc = getattr(tool, 'description', 'No description available')
                                name = getattr(tool, 'name', f'tool_{i}')
                                
                                # Format the input schema in a more readable way
                                if 'properties' in params:
                                    param_details = []
                                    for param_name, param_info in params['properties'].items():
                                        param_type = param_info.get('type', 'unknown')
                                        param_details.append(f"{param_name}: {param_type}")
                                    params_str = ', '.join(param_details)
                                else:
                                    params_str = 'no parameters'

                                tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                                tools_description.append(tool_desc)
                                print(f"Added description for tool: {tool_desc}")
                            except Exception as e:
                                print(f"Error processing tool {i}: {e}")
                                tools_description.append(f"{i+1}. Error processing tool")
                        
                        tools_description = "\n".join(tools_description)
                        print("Successfully created tools description")
                    except Exception as e:
                        print(f"Error creating tools description: {e}")
                        tools_description = "Error loading tools"
                    
                    print("Created system prompt...")

                    system_prompt = f"""You are a Math Problem Solving Agent that uses structured, step-by-step reasoning to solve mathematical problems. You have access to various mathematical tools.

                    Available tools:
                    {tools_description}

                    You MUST follow these sequential steps for every problem:
                    1. FIRST use show_reasoning to explain your approach (MANDATORY before any calculation)
                    2. THEN perform calculations using other tools
                    3. THEN verify results with the verify tool when appropriate
                    4. THEN use any visualization or output tools (like paint_the_number_in_rectangle)
                    5. FINALLY provide the final answer


                    1. For showing reasoning (MUST BE CALLED FIRST): 
                    FUNCTION_CALL: {{"name": "show_reasoning", "params": {{"steps": ["step1", "step2", "step3"]}}}}

                    2. For function calls:  
                    FUNCTION_CALL: {{"name": "function_name", "params": {{"param1": value1, "param2": value2}}}}

                    3. For Calculations:
                    FUNCTION_CALL: {{"name": "calculate", "params": {{"expression": "2 + 2"}}}}

                    4. For Verifications:
                    FUNCTION_CALL: {{"name": "verify", "params": {{"expression": "2 + 2", "expected": 4}}}}

                    5. For final answers:  
                    FINAL_ANSWER: {{"result": number}}

                    INSTRUCTIONS:
                    1. For each problem, follow these steps:
                    - FIRST: use show_reasoning to explain your approach (MANDATORY before any calculation)
                    - SECOND: Break down the solution into clear, logical steps
                    - THIRD: Verify each step before proceeding
                    - FOURTH: Use tools only when necessary and process all returned values
                    - FIFTH: Double-check your final answer

                    2. Response Format:
                    You must respond with EXACTLY ONE line in one of these formats:
                    - FUNCTION_CALL: function_name|param1|param2|...
                    - FINAL_ANSWER: [number]

                    3. Error Handling:
                    - If a tool fails, retry with the same parameters once
                    - If still failing, use an alternative approach
                    - If uncertain about a step, mark it with [UNCERTAIN] and explain why

                    4. Self-Verification:
                    - After each calculation, verify the result makes sense
                    - Check for common errors (e.g., unit mismatches, sign errors)
                    - Ensure all tool outputs are properly processed

                    5. Conversation Flow:
                    - Each response builds on previous steps
                    - Maintain context of previous calculations
                    - Update your approach based on new information

                    Error Handling Examples:
                    - FUNCTION_CALL: {{"name": "show_reasoning", "params": {{"steps": ["[UNCERTAIN] Attempting calculation", "Will retry if fails"]}}}}
                    - FUNCTION_CALL: {{"name": "calculate", "params": {{"expression": "invalid"}}}}
                    - FUNCTION_CALL: {{"name": "calculate", "params": {{"expression": "invalid"}}}}  

                    Verification Examples:
                    - FUNCTION_CALL: {{"name": "show_reasoning", "params": {{"steps": ["Checking unit consistency", "Verifying sign", "Validating range"]}}}}
                    - FUNCTION_CALL: {{"name": "verify", "params": {{"expression": "result > 0", "expected": true}}}}                  

                    Examples:
                    - FUNCTION_CALL: {{"name": "show_reasoning", "params": {{"steps": ["step1", "step2", "step3"]}}}}
                    - FUNCTION_CALL: {{"name": "calculate", "params": {{"expression": "2 + 2"}}}}
                    - FUNCTION_CALL: {{"name": "verify", "params": {{"expression": "2 + 2", "expected": 4}}}}
                    - FUNCTION_CALL: {{"name": "add", "params": {{"a": 5, "b": 3}}}}
                    - FUNCTION_CALL: {{"name": "strings_to_chars_to_int", "params": {{"input": "INDIA"}}}}
                    - FUNCTION_CALL: {{"name": "paint_the_number_in_rectangle", "params": {{"text": "INDIA", "x": 780, "y": 380, "width": 1140, "height": 700}}}}
                    - FUNCTION_CALL: {{"name": "send_email", "params": {{"to": "vikas.gupta@pillir.io", "subject": "Hello", "body": "Hello from the other side"}}}}
                    - FINAL_ANSWER: {{"result": 42}}      


                    Important Rules:
                    - All parameters must be valid JSON
                    - Validate JSON structure before sending
                    - When a function returns multiple values, you need to process all of them
                    - Only give FINAL_ANSWER when you have completed all necessary calculations
                    - Do not repeat function calls with the same parameters
                    - Verify each calculation step before proceeding
                    - If a tool fails, retry once with the same parameters
                    - If still failing, use an alternative approach or mark with [ERROR]
                    - Check for common errors (unit mismatches, sign errors, overflow)
                    - Tag each step with its reasoning type [ARITHMETIC], [LOGIC], [LOOKUP]
                    - If uncertain about a result, mark it with [UNCERTAIN]

                    DO NOT include any explanations or additional text.
                    Your entire response should be a single line starting with either FUNCTION_CALL: or FINAL_ANSWER:"""                

                    #query = """Find the ASCII values of characters in INDIA and then return sum of exponentials of those values. """
                    query = """Find the ASCII values of characters in INDIA and then get sum of exponentials of those values and paint the number in the rectangle with coordinates (780, 380, 1140, 700) in paint. Send an email to vikas.gupta@pillir.io with the subject "Final Answer" and the body includes the number. """
                    print("Starting iteration loop...")
                    
                    # Use global iteration variables
                    global iteration, last_response
                    
                    while iteration < max_iterations:
                        print(f"\n--- Iteration {iteration + 1} ---")
                        if last_response is None:
                            current_query = query
                        else:
                            current_query = current_query + "\n\n" + " ".join(iteration_response)
                            current_query = current_query + "  What should I do next?"

                        # Get model's response with timeout
                        print("Preparing to generate LLM response...")
                        prompt = f"{system_prompt}\n\nQuery: {current_query}"
                        try:
                            response = await generate_with_timeout(client, prompt)
                            response_text = response.text.strip()
                            print(f"LLM Response: {response_text}")
                            
                            # Find the FUNCTION_CALL line in the response
                            for line in response_text.split('\n'):
                                line = line.strip()
                                if line.startswith("FUNCTION_CALL:"):
                                    response_text = line
                                    break
                            
                        except Exception as e:
                            print(f"Failed to get LLM response: {e}")
                            break


                        if response_text.startswith("FUNCTION_CALL:"):
                            try:
                                _, json_str = response_text.split(":", 1)
                                function_data = json.loads(json_str.strip())
                                func_name = function_data["name"]
                                params = function_data["params"]
                            except json.JSONDecodeError as e:
                                print(f"Invalid JSON format: {e}")
                                # Handle error appropriately
                            
                            #print(f"\nDEBUG: Raw function info: {function_info}")
                            #print(f"DEBUG: Split parts: {parts}")
                            print(f"DEBUG: Function name: {func_name}")
                            print(f"DEBUG: Raw parameters: {params}")
                            
                            try:
                                # Find the matching tool to get its input schema
                                tool = next((t for t in tools if t.name == func_name), None)
                                if not tool:
                                    print(f"DEBUG: Available tools: {[t.name for t in tools]}")
                                    raise ValueError(f"Unknown tool: {func_name}")

                                print(f"DEBUG: Found tool: {tool.name}")
                                print(f"DEBUG: Tool schema: {tool.inputSchema}")

                                # Prepare arguments according to the tool's input schema
                                arguments = {}
                                schema_properties = tool.inputSchema.get('properties', {})
                                print(f"DEBUG: Schema properties: {schema_properties}")

                                for param_name, param_info in schema_properties.items():
                                    if not params:  # Check if we have enough parameters
                                        raise ValueError(f"Not enough parameters provided for {func_name}")
                                        
                                    # value = params.pop(0)  # Get and remove the first parameter
                                    value = params[param_name]
                                    param_type = param_info.get('type', 'string')
                                    
                                    print(f"DEBUG: Converting parameter {param_name} with value {value} to type {param_type}")
                                    
                                    # Convert the value to the correct type based on the schema
                                    if param_type == 'integer':
                                        arguments[param_name] = int(value)
                                    elif param_type == 'number':
                                        arguments[param_name] = float(value)
                                    elif param_type == 'array':
                                        # Handle array input
                                        if isinstance(value, str):
                                            # If value is a string, split and convert
                                            value = value.strip('[]').split(',')
                                            if func_name == 'show_reasoning':
                                                # For show_reasoning, keep strings as is
                                                arguments[param_name] = [x.strip() for x in value]
                                            else:
                                                # For other tools, convert to integers
                                                arguments[param_name] = [int(x.strip()) for x in value]
                                        elif isinstance(value, list):
                                            if func_name == 'show_reasoning':
                                                # For show_reasoning, keep strings as is
                                                arguments[param_name] = value
                                            else:
                                                # For other tools, ensure elements are integers
                                                arguments[param_name] = [int(x) if isinstance(x, (int, float, str)) else x for x in value]
                                        else:
                                            arguments[param_name] = [value]
                                    else:
                                        arguments[param_name] = str(value)

                                print(f"DEBUG: Final arguments: {arguments}")
                                print(f"DEBUG: Calling tool {func_name}")
                                
                                result = await session.call_tool(func_name, arguments=arguments)
                                print(f"DEBUG: Raw result: {result}")
                                
                                # Get the full result content
                                if hasattr(result, 'content'):
                                    print(f"DEBUG: Result has content attribute")
                                    # Handle multiple content items
                                    if isinstance(result.content, list):
                                        iteration_result = [
                                            item.text if hasattr(item, 'text') else str(item)
                                            for item in result.content
                                        ]
                                    else:
                                        iteration_result = str(result.content)
                                else:
                                    print(f"DEBUG: Result has no content attribute")
                                    iteration_result = str(result)
                                    
                                print(f"DEBUG: Final iteration result: {iteration_result}")
                                
                                # Format the response based on result type
                                if isinstance(iteration_result, list):
                                    result_str = f"[{', '.join(iteration_result)}]"
                                else:
                                    result_str = str(iteration_result)
                                
                                iteration_response.append(
                                    f"In the {iteration + 1} iteration you called {func_name} with {arguments} parameters, "
                                    f"and the function returned {result_str}."
                                )
                                last_response = iteration_result

                            except Exception as e:
                                print(f"DEBUG: Error details: {str(e)}")
                                print(f"DEBUG: Error type: {type(e)}")
                                import traceback
                                traceback.print_exc()
                                iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                                break

                        elif response_text.startswith("FINAL_ANSWER:"):
                            print("\n=== Agent Execution Complete ===")

                            break

                        iteration += 1
        except ExceptionGroup as eg:
            print(f"TaskGroup error: {eg}")
            for exc in eg.exceptions:
                print(f"Sub-exception: {exc}")
            raise  # Re-raise if needed            

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    asyncio.run(main())
    
    