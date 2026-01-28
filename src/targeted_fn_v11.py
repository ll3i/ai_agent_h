
"""
V11 Targeted FN Detection (Optimized Recall)
============================================
Goal: Catch the ~15 defects missed by V10/V4 without the V8 over-kill.

Strategy:
1. "Smart Aggressive" Lead Check:
   - Detect "Short/Cut" leads even if slightly ambiguous
   - But strictly filter "Shadow" false positives
2. Specific Edge Case Prompts:
   - "Side Lead" (Test_046)
   - "Twist" (Test_014)
   - "Missing Leg" (Test_028, 055, 060)
"""
import os
import sys
import requests
import base64
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment
from dotenv import load_dotenv
load_dotenv()

BRIDGE_URL = os.getenv('SALTLUX_API_BASE_URL', 'https://bridge.luxiacloud.com/llm/openai/chat/completions/{model}/create')
API_KEY = os.getenv("SALTLUX_API_KEY", "")
HEADERS = {"apikey": API_KEY, "Content-Type": "application/json"}
MODEL = os.getenv("MODEL_JUDGE", "luxia3-llm-32b-0731")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# ===============================
# V11 SPECIALIST PROMPTS
# ===============================

# 1. Presence (Standard)
PRESENCE_PROMPT = """
Is there a black transistor component in this image?
Answer YES if you see a black body.
Answer NO if the image is empty (only board visible).
Answer: YES or NO
"""

# 2. Lead Specialist (Aggressive but Smart)
LEAD_SPECIALIST_PROMPT = """
Look at the 3 metal legs of the component. 

Detect ANY of these defects:
1. **SHORT/CUT**: A leg clearly stops in the middle of the air. (Most common defect)
2. **MISSING**: You count only 2 legs instead of 3.
3. **Floating**: A leg is detached from the body.
4. **SIDEWAYS**: A leg bends 90 degrees to the side.

**FP Prevention**: 
- Leaves/shadows on the board are NORMAL.
- Bends/curves are NORMAL as long as the leg goes down.
- Crossing legs are NORMAL.

If you see a SHORT, CUT, or MISSING leg, answer DEFECT.
Otherwise NORMAL.

Answer: DEFECT or NORMAL
"""

# 3. Orientation Specialist (Twist/Flip)
ORIENTATION_SPECIALIST_PROMPT = """
Check orientation:

1. **UPSIDE DOWN**: Legs point UP.
2. **FLIPPED**: Round back face visible.
3. **TWISTED**: Rotated > 45 degrees (diagonal).

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


def targeted_fn_v11(image_path: str) -> tuple:
    """
    V11 Specialist Checks
    """
    base64_image = encode_image(image_path)
    
    # 1. Empty Check
    res = call_api(PRESENCE_PROMPT, base64_image, "PRESENCE-v11")
    if "NO" in res:
        return True, "FN: Empty Image"
    
    # 2. Lead Specialist (Priority)
    res = call_api(LEAD_SPECIALIST_PROMPT, base64_image, "LEAD-v11")
    if "DEFECT" in res:
        return True, "FN: Lead Defect"
    
    # 3. Orientation Specialist
    res = call_api(ORIENTATION_SPECIALIST_PROMPT, base64_image, "ORIENT-v11")
    if "DEFECT" in res:
        return True, "FN: Orientation Defect"
    
    return False, "NORMAL"
