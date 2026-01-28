
"""
Enhanced Classifier v5.0
========================
Balanced approach to improve BOTH FN and FP

Target: Score 0.57 → 0.75+

Key Improvements:
1. 3-Zone Lead Inspection (catches more FN)
2. Orientation Check (catches flipped/rotated)
3. Confidence-based voting (reduces FP)
"""
import os
import sys
import requests
import base64
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

BRIDGE_URL = os.getenv('SALTLUX_API_BASE_URL', 'https://bridge.luxiacloud.com/llm/openai/chat/completions/{model}/create')
API_KEY = os.getenv("SALTLUX_API_KEY", "")
HEADERS = {"apikey": API_KEY, "Content-Type": "application/json"}
MODEL = os.getenv("MODEL_JUDGE", "luxia3-llm-32b-0731")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# ===============================
# IMPROVED PROMPTS v5.0
# ===============================

# Primary Check: Comprehensive but balanced
PRIMARY_CHECK_PROMPT = """
You are inspecting a TO-92 transistor image for defects.

## INSPECTION CHECKLIST:

### 1. COMPONENT PRESENCE
- Is there a black plastic transistor body visible?
- If you ONLY see the brown board with holes (no component): DEFECT

### 2. LEAD CONNECTIVITY (CRITICAL - check carefully)
A normal TO-92 has exactly 3 metal leads going DOWN from the body.
- Count the leads: Are there exactly 3 leads visible?
- Check EACH lead: Does it connect from body to the bottom area?
- If ANY lead is: cut, missing, broken, or not reaching bottom → DEFECT

### 3. ORIENTATION
- The body should be at TOP, leads going DOWN
- If upside-down (leads pointing UP) or severely rotated: DEFECT

### 4. PHYSICAL DAMAGE
- Only MAJOR cracks, breaks, or missing parts count as defect
- Minor scratches, shadows, slight marks are NORMAL

## DECISION RULES:
- If component is MISSING → DEFECT
- If ANY lead has connectivity issue → DEFECT  
- If orientation is WRONG → DEFECT
- If there is MAJOR physical damage → DEFECT
- Otherwise → NORMAL

## IMPORTANT:
- Shadows on the board are NOT defects
- Focus on CLEAR, OBVIOUS problems only
- When in doubt about minor issues, say NORMAL

Give your final answer: DEFECT or NORMAL
Then briefly explain why (1 sentence).
"""

# Secondary confirmation for edge cases
LEAD_DETAIL_CHECK = """
Focus ONLY on the metal leads (the thin vertical pins).

Count and describe:
1. How many metal leads can you see? (should be 3)
2. Does each lead extend from the body to the bottom edge?
3. Are any leads cut, broken, or missing?

Answer format:
LEAD_COUNT: [number]
ALL_CONNECTED: YES or NO
PROBLEM: [describe if any, or NONE]
"""

ORIENTATION_CHECK = """
Check the transistor orientation:

1. Where is the black body? (TOP or BOTTOM of the component)
2. Which direction do the leads point? (UP or DOWN)
3. Is the component tilted more than 45 degrees?

A NORMAL orientation: body at TOP, leads pointing DOWN, minimal tilt.

Answer: ORIENTATION_OK or ORIENTATION_BAD
"""


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def call_api(prompt: str, base64_image: str, check_name: str) -> str:
    url = BRIDGE_URL.replace("{model}", MODEL)
    
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }
        ],
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=90)
        if response.status_code == 200:
            data = response.json()
            result = data["choices"][0]["message"]["content"].strip()
            logger.info(f"  [{check_name}] → {result[:60]}...")
            return result
        else:
            logger.error(f"  [{check_name}] API Error: {response.status_code}")
            return "ERROR"
    except Exception as e:
        logger.error(f"  [{check_name}] Exception: {e}")
        return "ERROR"


def classify_v5(image_path: str) -> tuple:
    """
    Enhanced v5 Classification with Balanced Approach
    
    Strategy:
    1. Primary comprehensive check
    2. If primary says DEFECT → do secondary confirmation
    3. If primary says NORMAL → do lead detail check for FN catch
    
    Returns: (label: int, reason: str)
    """
    base64_image = encode_image(image_path)
    
    # ===== PRIMARY CHECK =====
    primary_result = call_api(PRIMARY_CHECK_PROMPT, base64_image, "PRIMARY")
    primary_upper = primary_result.upper()
    
    if "ERROR" in primary_upper:
        return 0, "API Error - defaulting to NORMAL"
    
    # Parse primary result
    primary_defect = "DEFECT" in primary_upper and "NORMAL" not in primary_upper[:50]
    
    if primary_defect:
        # Primary says DEFECT - check if it's about leads or orientation
        # for confidence, but generally trust DEFECT calls
        
        # Check for common FP patterns (shadow, minor marks)
        if any(word in primary_result.lower() for word in ["shadow", "slight", "minor", "scratch"]):
            # Might be FP - do secondary check
            lead_result = call_api(LEAD_DETAIL_CHECK, base64_image, "LEAD-VERIFY")
            lead_upper = lead_result.upper()
            
            # Only override if leads are clearly OK
            if "LEAD_COUNT: 3" in lead_upper and "ALL_CONNECTED: YES" in lead_upper:
                return 0, "FP Override: Leads OK, minor issue ignored"
        
        return 1, f"DEFECT: {primary_result.split('.')[-1].strip()[:50] if '.' in primary_result else 'Primary check failed'}"
    
    else:
        # Primary says NORMAL - do secondary FN catch checks
        
        # Check 1: Lead detail check
        lead_result = call_api(LEAD_DETAIL_CHECK, base64_image, "LEAD-DETAIL")
        lead_upper = lead_result.upper()
        
        # FN catch: lead count wrong or connectivity issue
        if "LEAD_COUNT: 3" not in lead_upper:
            return 1, "FN Catch: Incorrect lead count"
        
        if "ALL_CONNECTED: NO" in lead_upper:
            return 1, "FN Catch: Lead connectivity issue"
        
        if "CUT" in lead_upper or "BROKEN" in lead_upper or "MISSING" in lead_upper:
            return 1, "FN Catch: Lead problem detected"
        
        # Check 2: Orientation check
        orient_result = call_api(ORIENTATION_CHECK, base64_image, "ORIENT")
        orient_upper = orient_result.upper()
        
        if "ORIENTATION_BAD" in orient_upper or "BAD" in orient_upper:
            return 1, "FN Catch: Orientation problem"
        
        # All checks passed
        return 0, "NORMAL: All checks passed"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        label, reason = classify_v5(test_path)
        print(f"Result: {label} ({reason})")
