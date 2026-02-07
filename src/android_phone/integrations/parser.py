import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def parse_action_from_text(text: str) -> Dict[str, Any]:
    """
    Parse the model output text into structured thought and action.
    
    Expected format:
    Thought: ...
    Action: ...
    
    Returns:
        Dict with keys 'thought' and 'action' (parsed components).
    """
    result = {
        "thought": None,
        "action_raw": None,
        "action_parsed": None
    }
    
    # Extract Thought
    thought_match = re.search(r'Thought:\s*(.*?)(?=Action:|$)', text, re.DOTALL | re.IGNORECASE)
    if thought_match:
        result["thought"] = thought_match.group(1).strip()
        
    # Extract Action
    action_match = re.search(r'Action:\s*(.*)', text, re.DOTALL | re.IGNORECASE)
    
    if action_match:
        action_raw = action_match.group(1).strip()
    else:
        # Fallback: try to find the function call pattern directly in the text
        # Look for pattern: func_name(arg=...)
        # We look for known function names
        known_funcs = ["click", "left_double", "right_single", "drag", "hotkey", "type", "scroll", "wait", "finished"]
        func_pattern = r'(' + '|'.join(known_funcs) + r')\((.*)\)'
        func_match_fallback = re.search(func_pattern, text, re.DOTALL)
        if func_match_fallback:
            action_raw = func_match_fallback.group(0)
            logger.info(f"Fallback parsing success: found {action_raw}")
        else:
            action_raw = None

    if action_raw:
        result["action_raw"] = action_raw
        
        # Parse specific function call
        # e.g. click(point='<point>500 500</point>')
        # e.g. type(content='hello')
        
        # Regex to match function name and arguments
        # Matches: func_name(arg1='val1', arg2='val2')
        func_match = re.match(r'(\w+)\((.*)\)', action_raw, re.DOTALL)
        if func_match:
            func_name = func_match.group(1)
            args_str = func_match.group(2)
            
            parsed_action = {"type": func_name}
            
            # Extract point: point='<point>x y</point>'
            point_match = re.search(r"point=['\"]<point>(\d+)\s+(\d+)</point>['\"]", args_str)
            if point_match:
                parsed_action["x"] = int(point_match.group(1))
                parsed_action["y"] = int(point_match.group(2))
                
            # Extract start_point (drag): start_point='<point>x y</point>'
            start_point_match = re.search(r"start_point=['\"]<point>(\d+)\s+(\d+)</point>['\"]", args_str)
            if start_point_match:
                parsed_action["start_x"] = int(start_point_match.group(1))
                parsed_action["start_y"] = int(start_point_match.group(2))
                
            # Extract end_point (drag): end_point='<point>x y</point>'
            end_point_match = re.search(r"end_point=['\"]<point>(\d+)\s+(\d+)</point>['\"]", args_str)
            if end_point_match:
                parsed_action["end_x"] = int(end_point_match.group(1))
                parsed_action["end_y"] = int(end_point_match.group(2))
                
            # Extract content (type/finished): content='...'
            # Handle escaped quotes carefully
            content_match = re.search(r"content=['\"](.*?)['\"](?=\s*(?:,|$))", args_str)
            if content_match:
                parsed_action["content"] = content_match.group(1)
                
            # Extract key (hotkey): key='...'
            key_match = re.search(r"key=['\"](.*?)['\"]", args_str)
            if key_match:
                parsed_action["key"] = key_match.group(1)
                
            # Extract direction (scroll): direction='...'
            dir_match = re.search(r"direction=['\"](.*?)['\"]", args_str)
            if dir_match:
                parsed_action["direction"] = dir_match.group(1)

            # Extract filename (screenshot): filename='...'
            filename_match = re.search(r"filename=['\"](.*?)['\"]", args_str)
            if filename_match:
                parsed_action["filename"] = filename_match.group(1)

            result["action_parsed"] = parsed_action
            
    return result
