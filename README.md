# AI Agent with Four-Component Architecture

This repository contains an implementation of an intelligent agent that uses a modular four-component architecture (Perception, Memory, Decision, Action) to solve tasks using tools.

## Architecture Overview

The agent follows a modular architecture with four main components:

1. **Perception**: Analyzes user input to extract intent, entities, and tool hints
2. **Memory**: Stores and retrieves relevant information from past interactions
3. **Decision**: Makes decisions on what actions to take based on perception and memory
4. **Action**: Executes actions using available tools

This architecture enables the agent to:
- Understand complex user requests
- Break them down into logical steps
- Execute appropriate tools in sequence
- Remember past actions and results
- Provide final answers

## Components

### Perception (`perception.py`)
- Extracts structured information from user input using LLM
- Identifies intent (what the user wants to achieve)
- Identifies entities (key objects, values, or concepts)
- Suggests relevant tools that might help

### Memory (`memory_simple.py`)
- Stores user inputs, tool outputs, and system knowledge
- Retrieves relevant memories based on the current context
- Uses semantic search to find the most relevant memories
- Maintains session context for multi-turn conversations

### Decision (`decision.py`)
- Makes decisions on what tools to call or what answers to provide
- Uses perception and memory to inform decisions
- Generates structured output in FUNCTION_CALL or FINAL_ANSWER format
- Plans multi-step solutions with fallbacks for handling errors

### Action (`action.py`)
- Executes tool calls based on the decision component's output
- Parses function call parameters into appropriate formats
- Handles tool execution and result processing
- Provides structured output for further processing

## Getting Started

### Prerequisites
- Python 3.8+
- Required packages:
  ```
  pip install mcp google-generativeai pydantic dotenv numpy faiss-cpu
  ```
- A valid API key for Google's Gemini model (stored in `.env` file)

### Setup
1. Clone this repository
2. Create a `.env` file in the root directory with:
   ```
   GEMINI_API_KEY=your_api_key_here
   EMAIL_ADDRESS=your_email_here
   ```
3. Ensure `example2.py` is in the same directory

### Running the Agent
To run the agent, simply execute:
```
python agent.py
```

When prompted with "User query:", enter your query. Examples include:
- "Find the ASCII values of characters in INDIA and then return sum of exponentials of those values."
- "What's 5+7?"
- "Draw a rectangle in Paint."

## Example Use Cases

### Math Operations
The agent can perform complex mathematical operations by breaking them down into steps. For example, when asked to "Find the ASCII values of characters in INDIA and then return sum of exponentials of those values", it will:
1. Use perception to understand the request
2. Use memory to check for similar past queries
3. Use decision to determine the step-by-step plan
4. Use action to call the appropriate tools in sequence
5. Present the final result and visualize it

### Visual Output
The agent can visualize results using Microsoft Paint:
1. It opens Paint using the `open_paint` tool
2. Draws a rectangle using the `draw_rectangle` tool
3. Adds text to the drawing using the `add_text_in_paint` tool

## Architecture Benefits

1. **Modularity**: Each component can be improved or replaced independently
2. **Robustness**: Better error handling with fallbacks at each stage
3. **Extensibility**: Easy to add new tools or capabilities
4. **Transparency**: Clear separation of concerns makes the system more understandable
5. **Context Awareness**: Memory system maintains context across multiple turns

## Usage Notes

- The agent is designed to work with the MCP (Multi-Component Protocol) framework
- It uses Gemini for natural language understanding and decision making
- The agent maintains a session memory that persists throughout the conversation
- Maximum 4 iterations per query to prevent infinite loops

## Future Improvements

- Add more tools and capabilities
- Implement a proper UI instead of console-based interaction
- Improve error handling and recovery
- Add support for multi-modal inputs (images, audio)
- Implement more sophisticated memory management

## Current Prompt Evaluation
 
You are a Prompt Evaluation Assistant.

You will receive a prompt written by a student. Your job is to review this prompt and assess how well it supports structured, step-by-step reasoning in an LLM (e.g., for math, logic, planning, or tool use).

Evaluate the prompt on the following criteria:

1. ✅ Explicit Reasoning Instructions  
   - Does the prompt tell the model to reason step-by-step?  
   - Does it include instructions like “explain your thinking” or “think before you answer”?

2. ✅ Structured Output Format  
   - Does the prompt enforce a predictable output format (e.g., FUNCTION_CALL, JSON, numbered steps)?  
   - Is the output easy to parse or validate?

3. ✅ Separation of Reasoning and Tools  
   - Are reasoning steps clearly separated from computation or tool-use steps?  
   - Is it clear when to calculate, when to verify, when to reason?

4. ✅ Conversation Loop Support  
   - Could this prompt work in a back-and-forth (multi-turn) setting?  
   - Is there a way to update the context with results from previous steps?

5. ✅ Instructional Framing  
   - Are there examples of desired behavior or “formats” to follow?  
   - Does the prompt define exactly how responses should look?

6. ✅ Internal Self-Checks  
   - Does the prompt instruct the model to self-verify or sanity-check intermediate steps?

7. ✅ Reasoning Type Awareness  
   - Does the prompt encourage the model to tag or identify the type of reasoning used (e.g., arithmetic, logic, lookup)?

8. ✅ Error Handling or Fallbacks  
   - Does the prompt specify what to do if an answer is uncertain, a tool fails, or the model is unsure?

9. ✅ Overall Clarity and Robustness  
   - Is the prompt easy to follow?  
   - Is it likely to reduce hallucination and drift?

---

Respond with a structured review in this format:

```json
{
  "explicit_reasoning": true,
  "structured_output": true,
  "tool_separation": true,
  "conversation_loop": true,
  "instructional_framing": true,
  "internal_self_checks": false,
  "reasoning_type_awareness": false,
  "fallbacks": false,
  "overall_clarity": "Excellent structure, but could improve with self-checks and error fallbacks."
}
