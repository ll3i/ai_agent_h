
"""
V15 Targeted FN Detection (Balanced Aggressive-Strict)
======================================================
Strategy (based on user feedback):
1. Baselined on V8 (Score 0.76) design.
2. Lead Check: 
   - Aggressive on: SHORT, MISSING, SIDEWAYS.
   - Strict on FP suppression: Shadow, Bend, Crossing = NORMAL.
3. Orientation:
   - Aggressive on: >45 deg Twist, Upside Down, Flipped.
   - Strict on: Minor tilt (<45) = NORMAL.
4. Empty: Strict (No component = Defect).
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
# V15 BALANCED PROMPTS
# ===============================

# 1. Presence (Strict)
PRESENCE_PROMPT = """
Is there a black transistor component in this image?
Answer YES if you see a black body.
Answer NO if the image is empty (only board visible).
Answer: YES or NO
"""

# 2. Lead Specialist (Balanced)
# "Active" detection for defects, "Strict" suppression for noise.
LEAD_SPECIALIST_PROMPT = """
Inspect the 3 metal legs of the component.

**DETECT THESE DEFECTS (Aggressive):**
1. **SHORT/CUT**: Leg stops in mid-air (clearly shorter than others).
2. **MISSING**: Only 0, 1, or 2 legs visible.
3. **SIDEWAYS**: Leg bends 90 degrees horizontally (reaching side of image).
4. **FLOATING**: Leg is detached from the body.

**IGNORE THESE NOISE (Strict FP Suppression):**
1. **Shadows**: If a leg looks cut but continues as a shadow/dark line -> NORMAL.
2. **Bends**: If a leg is curved/bent but goes down -> NORMAL.
3. **Touching**: If legs cross or touch -> NORMAL.
4. **Darkness**: If legs are hard to see due to lighting -> NORMAL.

**DECISION:**
If you see a CLEAR Defect from list #1, say DEFECT.
If it looks like Noise from list #2 or is ambiguous, say NORMAL.

Answer: DEFECT or NORMAL
"""

# 3. Orientation Specialist (Twist/Flip)
ORIENTATION_SPECIALIST_PROMPT = """
Check component orientation.

**DEFECT CONDITIONS:**
1. **UPSIDE DOWN**: Legs point UP.
2. **FLIPPED**: Round back face visible.
3. **EXTREME TWIST**: Rotated more than 45 degrees.

**NORMAL CONDITIONS:**
1. **MINOR TILT**: Tilted less than 45 degrees.
2. **STRAIGHT**: Upright with legs down.

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


def targeted_fn_v15(image_path: str) -> tuple:
    """
    V15 Specialist Checks
    """
    base64_image = encode_image(image_path)
    
    # 1. Empty Check
    res = call_api(PRESENCE_PROMPT, base64_image, "PRESENCE-v15")
    if "NO" in res:
        return True, "FN: Empty Image"
    
    # 2. Lead Specialist
    res = call_api(LEAD_SPECIALIST_PROMPT, base64_image, "LEAD-v15")
    if "DEFECT" in res:
        return True, "FN: Lead Defect (Short/Cut/Side)"
    
    # 3. Orientation Specialist
    res = call_api(ORIENTATION_SPECIALIST_PROMPT, base64_image, "ORIENT-v15")
    if "DEFECT" in res:
        return True, "FN: Orientation Defect (>45 Twist)"
    
    return False, "NORMAL"
