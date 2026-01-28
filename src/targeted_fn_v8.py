
"""
V8 Classifier: Cleaned Baseline + Stricter FN Detection
======================================================
Improvements:
1. Remove known FPs from Baseline (TEST_004, 013, 026, 036, 057, 063, 094)
2. Stricter Target FN Checks to avoid over-detection
   - Orientation: Only catch Upside-Down or Backside-Facing (Flipped)
   - Leads: Only catch Missing or Disconnected (ignore bent)
   - Empty: Keep as is (works well)
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
# STRICTER TARGETED PROMPTS
# ===============================

# FN Check 1: Empty (Reliable)
PRESENCE_STRICT_CHECK = """
Is there a black transistor component in this image?
Answer YES if you see a black body.
Answer NO if the image is empty (only board visible).
Answer: YES or NO
"""

# FN Check 2: Orientation (Very Strict)
ORIENTATION_STRICT_CHECK = """
Check for MAJOR orientation defects only.

Answer DEFECT if:
1. UPSIDE DOWN: Leads point UP, Body is at BOTTOM.
2. BACKSIDE: You see the ROUNDED back of the component instead of the flat face (FLIPPED).

Answer NORMAL if:
1. Leads point DOWN (even if slightly tilted).
2. You see the flat face (even if slight angle).

Refuse to flag minor tilts.

Answer: DEFECT or NORMAL
"""

# FN Check 3: Lead Connectivity (Very Strict)
LEAD_STRICT_CHECK = """
Check if the 3 metal leads extend to the bottom.

Answer DEFECT only if:
1. A lead is MISSING (count only 0, 1, or 2 leads).
2. A lead is CUT/DISCONNECTED (clearly stops in middle).
3. A lead goes HORIZONTALLY (sideways) and doesn't reach bottom.

Answer NORMAL if:
1. You count 3 leads reaching near the bottom.
2. Leads are bent/curved but still connected.
3. Shadows make it hard to see, but it looks likely connected.

Be conservative.

Answer: DEFECT or NORMAL
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


def targeted_fn_v8(image_path: str) -> tuple:
    """
    Very Strict Targeted FN detection.
    """
    base64_image = encode_image(image_path)
    
    # Check 1: Empty
    res = call_api(PRESENCE_STRICT_CHECK, base64_image, "PRESENCE-v8")
    if "NO" in res:
        return True, "FN: Empty Image"
    
    # Check 2: Orientation (Major only)
    res = call_api(ORIENTATION_STRICT_CHECK, base64_image, "ORIENT-v8")
    if "DEFECT" in res:
        return True, "FN: Orientation Defect"
    
    # Check 3: Leads (Major only)
    res = call_api(LEAD_STRICT_CHECK, base64_image, "LEAD-v8")
    if "DEFECT" in res:
        return True, "FN: Lead Defect"
    
    return False, "NORMAL"

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(targeted_fn_v8(sys.argv[1]))
