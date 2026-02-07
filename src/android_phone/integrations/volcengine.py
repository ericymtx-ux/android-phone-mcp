import os
import httpx
import json
import logging
from typing import Optional, Dict, Any, List
from .prompt import COMPUTER_USE_DOUBAO
from .parser import parse_action_from_text

logger = logging.getLogger(__name__)

class VolcengineGUIClient:
    """
    Client for Volcengine GUI Agent API.
    """
    
    API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions" # Use Chat API as per updated docs logic
    
    def __init__(self, api_key: Optional[str] = None, model: str = "doubao-seed-1-6-vision-250815"):
        self.api_key = api_key or os.environ.get("ARK_API_KEY")
        self.model = model
        self.history: List[Dict[str, Any]] = [] # Conversation history
        
    def reset_session(self):
        """Clear conversation history."""
        self.history = []
        logger.info("Volcengine session history cleared.")

    def _prune_history_images(self, history: List[Dict[str, Any]], max_images: int = 4) -> List[Dict[str, Any]]:
        """
        Prune images from history to ensure total images <= max_images.
        Keeps the most recent images.
        
        Args:
            history: The list of history messages (User/Assistant).
            max_images: Maximum number of images to keep in history (excluding the current new message).
        """
        # Deep copy to avoid modifying original history if needed, 
        # but here we might just create a new list of messages.
        # Actually, we should probably construct a new list where older images are removed.
        
        pruned_history = []
        
        # Count images from the end
        image_count = 0
        
        # Iterate backwards
        for msg in reversed(history):
            new_msg = msg.copy()
            if msg["role"] == "user" and isinstance(msg["content"], list):
                # Check for image_url
                has_image = any(item.get("type") == "image_url" for item in msg["content"])
                
                if has_image:
                    if image_count < max_images:
                        image_count += 1
                        # Keep image
                        pruned_history.insert(0, new_msg)
                    else:
                        # Remove image, keep text
                        new_content = [item for item in msg["content"] if item.get("type") != "image_url"]
                        new_msg["content"] = new_content
                        pruned_history.insert(0, new_msg)
                else:
                    pruned_history.insert(0, new_msg)
            else:
                pruned_history.insert(0, new_msg)
                
        return pruned_history

    def _prune_history_turns(self, history: List[Dict[str, Any]], max_turns: int = 10) -> List[Dict[str, Any]]:
        """
        Prune older conversation turns to keep context within limits, 
        but always try to preserve the latest context.
        """
        # A turn consists of user + assistant message usually.
        # Simple implementation: keep last N messages
        if len(history) > max_turns * 2:
            return history[-(max_turns * 2):]
        return history

    def ask(self, instruction: str, image_b64: str) -> Dict[str, Any]:
        """
        Send instruction and screenshot to Volcengine GUI model (with history).
        
        Args:
            instruction: User instruction (e.g. "Open WeChat").
            image_b64: Base64 encoded screenshot.
            
        Returns:
            Parsed response containing thought and structured action.
        """
        if not self.api_key:
            raise ValueError("ARK_API_KEY is not set")
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare new user message
        new_user_msg = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": instruction
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}" if not image_b64.startswith("http") else image_b64
                    }
                }
            ]
        }
        
        # Prune history images (keep max 4 previous images + 1 current = 5 total)
        # Also prune history length to avoid token limit issues
        pruned_history = self._prune_history_turns(self.history, max_turns=10)
        pruned_history = self._prune_history_images(pruned_history, max_images=4)
        
        # Construct full messages: System + Pruned History + New User Message
        messages = [
            {
                "role": "system",
                "content": COMPUTER_USE_DOUBAO
            }
        ] + pruned_history + [new_user_msg]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1
        }
        
        try:
            logger.info(f"Sending request to Volcengine API (model: {self.model}, history_len: {len(self.history)})...")
            # Increase timeout to 120s for complex reasoning
            with httpx.Client(timeout=120.0) as client:
                response = client.post(self.API_URL, headers=headers, json=payload)
                response.raise_for_status()
                
                resp_json = response.json()
                content = resp_json['choices'][0]['message']['content']
                
                # Parse the response
                parsed_result = parse_action_from_text(content)
                parsed_result["raw_content"] = content
                
                # Update history
                self.history.append(new_user_msg)
                self.history.append({
                    "role": "assistant",
                    "content": content
                })
                
                return parsed_result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.text}")
            raise RuntimeError(f"Volcengine API Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise RuntimeError(f"Volcengine Request Failed: {e}")

    def parse_action(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse the raw response from Volcengine into structured actions.
        
        Note: The actual response format needs to be handled carefully.
        Assuming the model returns text that needs parsing, or structured JSON.
        Based on the docs, it might return a thought process and action.
        
        This is a placeholder for the parsing logic.
        """
        # TODO: Implement robust parsing based on actual model output format
        # For now, we return the raw content for the Agent to interpret
        return response
