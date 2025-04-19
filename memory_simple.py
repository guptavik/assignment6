import os
from typing import List, Optional, Literal
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv
from google import genai

# Optional: import log from agent if shared, else define locally
try:
    from main import log
except ImportError:
    import datetime as dt
    def log(stage: str, msg: str):
        now = dt.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class MemoryItem(BaseModel):
    text: str
    type: Literal["preference", "tool_output", "fact", "query", "system"] = "fact"
    timestamp: Optional[str] = None
    tool_name: Optional[str] = None
    user_query: Optional[str] = None
    tags: List[str] = []
    session_id: Optional[str] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.now().isoformat()
        super().__init__(**data)


class MemoryManagerSimple:
    def __init__(self):
        self.data: List[MemoryItem] = []

    def add(self, item: MemoryItem):
        """Add a memory item to storage"""
        self.data.append(item)
        log("memory", f"Added memory item: {item.type} - {item.text[:50]}...")

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        type_filter: Optional[str] = None,
        tag_filter: Optional[List[str]] = None,
        session_filter: Optional[str] = None
    ) -> List[MemoryItem]:
        """Retrieve relevant memory items based on semantic similarity to query"""
        if len(self.data) == 0:
            return []
            
        # Apply filters
        filtered_data = self.data.copy()
        
        # Filter by type
        if type_filter:
            filtered_data = [item for item in filtered_data if item.type == type_filter]
            
        # Filter by tag
        if tag_filter:
            filtered_data = [
                item for item in filtered_data 
                if any(tag in item.tags for tag in tag_filter)
            ]
            
        # Filter by session
        if session_filter:
            filtered_data = [item for item in filtered_data if item.session_id == session_filter]
        
        if len(filtered_data) == 0:
            return []
            
        # If we have 3 or fewer items after filtering, return all of them
        if len(filtered_data) <= top_k:
            return filtered_data
            
        # Use Gemini to rank items by relevance
        try:
            memory_texts = [f"Memory {i}: {item.text}" for i, item in enumerate(filtered_data)]
            prompt = f"""
            Given the following memory items and a query, return the indices of the {top_k} most relevant memory items for the query.
            Only return the indices, separated by commas. For example: "1,4,7"
            
            Query: {query}
            
            Memory items:
            {"\n".join(memory_texts)}
            """
            
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            
            indices_text = response.text.strip()
            log("memory", f"Relevance ranking response: {indices_text}")
            
            # Parse indices - handle common formats
            import re
            indices = []
            
            # Try to extract numbers from the response
            numbers = re.findall(r'\d+', indices_text)
            for num in numbers[:top_k]:
                try:
                    index = int(num)
                    if 0 <= index < len(filtered_data):
                        indices.append(index)
                except ValueError:
                    continue
                    
            # If no valid indices found, return the most recent items
            if not indices:
                return filtered_data[-top_k:]
                
            # Return the memories corresponding to the selected indices
            return [filtered_data[i] for i in indices]
                
        except Exception as e:
            log("memory", f"Error ranking memories: {e}")
            # Fallback: return the most recent memories
            return filtered_data[-top_k:]

    def bulk_add(self, items: List[MemoryItem]):
        """Add multiple memory items at once"""
        for item in items:
            self.add(item)