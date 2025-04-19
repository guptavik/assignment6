from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
from google import genai
import re
import json

# Optional: import log from agent if shared, else define locally
try:
    from main import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class PerceptionResult(BaseModel):
    user_input: str
    intent: str = "unknown"  # Default value
    entities: List[str] = []
    tool_hint: Optional[str] = None


def extract_perception(user_input: str) -> PerceptionResult:
    """Extracts intent, entities, and tool hints using LLM"""

    prompt = f"""
You are an AI that extracts structured facts from user input.

Input: "{user_input}"

Return the response as a Python dictionary with keys:
- intent: (brief phrase about what the user wants)
- entities: a list of strings representing keywords or values (e.g., ["INDIA", "ASCII"])
- tool_hint: (name of the MCP tool that might be useful, if any)

Output only the dictionary on a single line. Do NOT wrap it in ```json or other formatting. Ensure `entities` is a list of strings, not a dictionary.
If you're not sure about any field, use an empty string for intent, empty list for entities, and null for tool_hint.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        raw = response.text.strip()
        log("perception", f"LLM output: {raw}")

        # Strip Markdown backticks if present
        clean = re.sub(r"^```json|```$", "", raw.strip(), flags=re.MULTILINE).strip()

        try:
            # First try to parse as JSON
            try:
                parsed = json.loads(clean.replace("null", "None"))
            except json.JSONDecodeError:
                # If JSON parsing fails, try eval
                clean = clean.replace("null", "None")
                parsed = eval(clean)
        except Exception as e:
            log("perception", f"⚠️ Failed to parse cleaned output: {e}")
            # Return with defaults
            return PerceptionResult(
                user_input=user_input,
                intent="unknown",
                entities=[],
                tool_hint=None
            )

        # Fix common issues
        if isinstance(parsed.get("entities"), dict):
            parsed["entities"] = list(parsed["entities"].values())
        
        # Ensure intent has a default value
        if "intent" not in parsed or parsed["intent"] is None:
            parsed["intent"] = "unknown"
            
        # Ensure entities has a default value
        if "entities" not in parsed or parsed["entities"] is None:
            parsed["entities"] = []

        return PerceptionResult(user_input=user_input, **parsed)

    except Exception as e:
        log("perception", f"⚠️ Extraction failed: {e}")
        return PerceptionResult(
            user_input=user_input,
            intent="unknown",
            entities=[],
            tool_hint=None
        )
