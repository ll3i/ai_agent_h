
"""
V7 Classifier: V4 Baseline + Targeted FN Detection
===================================================
Strategy:
1. Use V4 results as baseline (20 defects at 0.57 score)
2. For items V4 marked as NORMAL, do targeted FN checks
3. Focus on SPECIFIC missed patterns without over-detecting

Target FN Patterns (from user feedback):
- Lead disconnection (not reaching bottom)
- Orientation (tilted >45°, upside down, flipped)
- Side connections (leads going sideways)
- Empty images
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
# TARGETED FN DETECTION PROMPTS
# ===============================

# FN Check 1: Lead Connectivity (Very Specific)
LEAD_FN_CHECK = """
Look at the metal leads (thin vertical wires) going from the black body down.

I need you to check ONE specific thing:
Do ALL 3 leads reach the BOTTOM EDGE of the visible area?

Answer YES if:
- You can see 3 leads and they all extend to near the bottom of the image
- Even if slightly bent, they reach down

Answer NO if:
- Any lead is SHORT and stops in the middle
- Any lead is CUT (doesn't reach bottom)
- You can only see 2 leads or fewer
- Leads go SIDEWAYS instead of down

Answer: YES or NO
"""

# FN Check 2: Orientation (Very Specific)
ORIENTATION_FN_CHECK = """
Check the transistor orientation:

Answer GOOD if:
- Black body is at the TOP
- 3 leads point DOWNWARD
- Component is roughly upright (not heavily tilted)

Answer BAD if:
- Component is UPSIDE DOWN (body at bottom, leads pointing up)
- Component is SIDEWAYS (lying on its side)
- Component is tilted MORE than 45 degrees from vertical
- Component is FLIPPED (showing the rounded back instead of flat front)

Answer: GOOD or BAD
"""

# FN Check 3: Component Presence (Very Specific)
PRESENCE_FN_CHECK = """
Simple question: Is there a transistor component in this image?

Answer NO if:
- You only see the brown board with holes
- There is no black plastic body visible at all
- The image is basically empty

Answer YES if:
- You can see any part of a black transistor body
- There are metal leads attached to something

Answer: YES or NO
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
        response = requests.post(url, headers=HEADERS, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            result = data["choices"][0]["message"]["content"].strip().upper()
            logger.info(f"  [{check_name}] → {result[:30]}")
            return result
        else:
            return "ERROR"
    except Exception as e:
        logger.error(f"  [{check_name}] Exception: {e}")
        return "ERROR"


def targeted_fn_check(image_path: str) -> tuple:
    """
    Targeted FN detection for items V4 marked as NORMAL.
    
    Checks for specific missed defect patterns:
    1. Component not present (empty image)
    2. Lead connectivity issue
    3. Orientation problem
    
    Returns: (is_defect: bool, reason: str)
    """
    base64_image = encode_image(image_path)
    
    # Check 1: Is component present?
    presence = call_api(PRESENCE_FN_CHECK, base64_image, "PRESENCE")
    if "NO" in presence:
        return True, "FN: Empty image - no component"
    
    # Check 2: Lead connectivity
    leads = call_api(LEAD_FN_CHECK, base64_image, "LEADS")
    if "NO" in leads:
        return True, "FN: Lead connectivity issue"
    
    # Check 3: Orientation
    orient = call_api(ORIENTATION_FN_CHECK, base64_image, "ORIENT")
    if "BAD" in orient:
        return True, "FN: Orientation problem"
    
    # All checks passed - keep as NORMAL
    return False, "Checks passed - confirmed NORMAL"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        is_defect, reason = targeted_fn_check(test_path)
        print(f"Result: {'DEFECT' if is_defect else 'NORMAL'} ({reason})")
