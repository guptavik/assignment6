import os
import asyncio
import datetime
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

# Import the four components
from perception import extract_perception, PerceptionResult
from memory_simple import MemoryManagerSimple, MemoryItem
from decision import generate_plan
from action import execute_tool, parse_function_call

# Global session ID for this agent run
SESSION_ID = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

# Setup logging
def log(stage: str, msg: str):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [{stage}] {msg}")

# Load environment variables
load_dotenv()

async def main():
    log("agent", "Starting agent execution...")
    
    # Initialize memory manager
    memory = MemoryManagerSimple()
    
    try:
        # Create MCP server connection
        log("agent", "Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["example2.py"],
            cwd="."
        )

        async with stdio_client(server_params) as (read, write):
            log("agent", "Connection established, creating session...")
            async with ClientSession(read, write) as session:
                log("agent", "Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                log("agent", "Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                log("agent", f"Successfully retrieved {len(tools)} tools")

                # Format tool descriptions
                tools_description = []
                for i, tool in enumerate(tools):
                    try:
                        params = tool.inputSchema
                        desc = getattr(tool, 'description', 'No description available')
                        name = getattr(tool, 'name', f'tool_{i}')
                            
                        # Format the input schema
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
                    except Exception as e:
                        log("agent", f"Error processing tool {i}: {e}")
                        tools_description.append(f"{i+1}. Error processing tool")
                
                tools_description_str = "\n".join(tools_description)
                
                # Add system knowledge to memory
                memory.add(MemoryItem(
                    text="The agent has access to various mathematical tools including arithmetic operations, ASCII conversion, and exponential calculations.",
                    type="system",
                    session_id=SESSION_ID,
                    tags=["system", "tools"]
                ))
                
                # The main agent loop
                query = input("User query: ")
                
                max_iterations = 5
                iteration = 0
                
                while iteration < max_iterations:
                    log("agent", f"\n--- Iteration {iteration + 1} ---")
                    
                    # 1. PERCEPTION: Extract intent and entities from user query
                    perception_result = extract_perception(query)
                    log("agent", f"Perception: Intent={perception_result.intent}, Entities={perception_result.entities}")
                    
                    # Store user query in memory
                    memory.add(MemoryItem(
                        text=query,
                        type="query",
                        session_id=SESSION_ID,
                        tags=["user_input"]
                    ))
                    
                    # 2. MEMORY: Retrieve relevant memories
                    retrieved_memories = memory.retrieve(
                        query=query,
                        top_k=3,
                        session_filter=SESSION_ID
                    )
                    log("agent", f"Retrieved {len(retrieved_memories)} relevant memories")
                    
                    # 3. DECISION: Generate a plan based on perception and memory
                    plan = generate_plan(
                        perception=perception_result,
                        memory_items=retrieved_memories,
                        tool_descriptions=tools_description_str
                    )
                    log("agent", f"Decision plan: {plan}")
                    
                    # 4. ACTION: Execute the plan
                    if plan.startswith("FUNCTION_CALL:"):
                        # Execute the function call
                        tool_result = await execute_tool(session, tools, plan)
                        
                        # Store the result in memory
                        memory.add(MemoryItem(
                            text=f"Tool {tool_result.tool_name} returned: {tool_result.result}",
                            type="tool_output",
                            tool_name=tool_result.tool_name,
                            user_query=query,
                            session_id=SESSION_ID,
                            tags=["tool_output", tool_result.tool_name]
                        ))
                        
                        # Format for next iteration
                        result_str = str(tool_result.result)
                        print(f"Tool result: {result_str}")
                        
                        # Prepare for next iteration
                        query = f"Previous step: Used {tool_result.tool_name} with {tool_result.arguments} and got {result_str}. What should I do next?"
                        
                    elif plan.startswith("FINAL_ANSWER:"):
                        final_answer = plan.split(":", 1)[1].strip()
                        log("agent", f"Final answer: {final_answer}")
                        print(f"\nFinal answer: {final_answer}")
                        
                        # Store the final answer in memory
                        memory.add(MemoryItem(
                            text=f"Final answer for query '{query}': {final_answer}",
                            type="fact",
                            user_query=query,
                            session_id=SESSION_ID,
                            tags=["final_answer"]
                        ))
                        
                        # Paint the answer if it contains a number
                        try:
                            # Check if the answer contains a number in square brackets
                            import re
                            match = re.search(r'\[(.*?)\]', final_answer)
                            if match:
                                number_text = match.group(1)
                                log("agent", f"Painting the final answer: {number_text}")
                                
                                # Open Paint
                                result = await session.call_tool("open_paint")
                                log("agent", result.content[0].text)
                                
                                # Wait for Paint to be fully maximized
                                await asyncio.sleep(1)
                                
                                # Draw a rectangle
                                result = await session.call_tool(
                                    "draw_rectangle",
                                    arguments={
                                        "x1": 780,
                                        "y1": 380,
                                        "x2": 1140,
                                        "y2": 700
                                    }
                                )
                                log("agent", result.content[0].text)
                                
                                # Add text
                                result = await session.call_tool(
                                    "add_text_in_paint",
                                    arguments={
                                        "text": number_text
                                    }
                                )
                                log("agent", result.content[0].text)
                        except Exception as e:
                            log("agent", f"Error painting the answer: {e}")
                            
                        break
                    else:
                        log("agent", f"Unexpected response format: {plan}")
                        break
                    
                    iteration += 1

    except Exception as e:
        log("agent", f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())