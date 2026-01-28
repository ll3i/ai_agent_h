
"""
V10 Targeted FN Detection
=========================
Strategy: Ultra-Conservative + Edge Specialist

1. Ultra-Conservative Checks (To avoid FPs):
   - Only flag if clearly MISSING component
   - Only flag if leads are clearly WRONG count (0-2) or CUT
   - Only flag if orientation is clearly INVERTED

2. Edge Case Specialist (To catch FNs):
   - "Side Connection": Detect leads going sideways (TEST_046)
   - "Severe Twist": Detect 45+ degree rotation (TEST_014)

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
# V10 SPECIALIST PROMPTS
# ===============================

# 1. Presence (Standard)
PRESENCE_PROMPT = """
Is there a black transistor component in this image?
Answer YES if you see a black body.
Answer NO if the image is empty (only board visible).
Answer: YES or NO
"""

# 2. Lead Specialist (Conservative + Side Check)
LEAD_SPECIALIST_PROMPT = """
Analyze the metal leads (legs) of the transistor.

Check for these SPECIFIC defects:
1. **COUNT**: Are there fewer than 3 leads? (0, 1, or 2)
2. **CUT**: Is a lead clearly cut short and floating?
3. **SIDEWAYS**: Do the leads bend sharply to the SIDE within the board area instead of going down?

**IGNORE** minor bends, shadows, or crossing leads.
Only flag if one of the above is CLEARLY true.

Answer: DEFECT or NORMAL
"""

# 3. Orientation Specialist (Conservative + Twist Check)
ORIENTATION_SPECIALIST_PROMPT = """
Analyze the 3D orientation of the component.

Check for these SPECIFIC defects:
1. **UPSIDE DOWN**: Leads pointing UP.
2. **BACKSIDE**: Showing the rounded back face instead of flat front.
3. **SEVERE TWIST**: Rotated more than 45 degrees relative to the board holes.

**IGNORE** minor tilts (less than 30-40 degrees).

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


def targeted_fn_v10(image_path: str) -> tuple:
    """
    V10 Specialist Checks
    """
    base64_image = encode_image(image_path)
    
    # 1. Empty Check (Fastest)
    res = call_api(PRESENCE_PROMPT, base64_image, "PRESENCE-v10")
    if "NO" in res:
        return True, "FN: Empty Image"
    
    # 2. Lead Specialist (Side check included)
    res = call_api(LEAD_SPECIALIST_PROMPT, base64_image, "LEAD-v10")
    if "DEFECT" in res:
        return True, "FN: Lead/Side Defect"
    
    # 3. Orientation Specialist (Twist check included)
    res = call_api(ORIENTATION_SPECIALIST_PROMPT, base64_image, "ORIENT-v10")
    if "DEFECT" in res:
        return True, "FN: Orientation/Twist Defect"
    
    return False, "NORMAL"
