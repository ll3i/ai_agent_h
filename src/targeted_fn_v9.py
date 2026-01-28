
"""
V9 Classifier: V4 Baseline + Ultra-Conservative FN Detection
============================================================
V8 Analysis:
- Caught almost all FNs (Good)
- Introduced ~30 new False Positives (Bad)
- Main culprit: Lead check was too strict (flagged shadows/bends)

V9 Strategy:
1. Keep V4 Baseline (Cleaned of known FPs)
2. FN Checks are now ULTRA-CONSERVATIVE:
   - Leads: Only flag if lead count < 3 or COMPLETELY missing. Ignore bends/shortness.
   - Orientation: Keep strict (Upside down/Flipped)
   - Empty: Keep strict
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
# ULTRA-CONSERVATIVE PROMPTS
# ===============================

# FN Check 1: Empty (Works well)
PRESENCE_PROMPT = """
Is there a black transistor component in this image?
Answer YES if you see a black body.
Answer NO if the image is empty (only board visible).
Answer: YES or NO
"""

# FN Check 2: Orientation (Specific)
# Only catch clearly wrong orientations
ORIENTATION_PROMPT = """
Check for MAJOR orientation errors.

Answer DEFECT if:
- UPSIDE DOWN (Leads pointing UP)
- FLIPPED (Showing rounded back)

Answer NORMAL if:
- Leads pointing DOWN (even if tilted)
- Flat face visible (even if angled)
- Lying on side (Ambiguous -> call it NORMAL to avoid FP)

Answer: DEFECT or NORMAL
"""

# FN Check 3: Lead Count (Ultra-Conservative)
# Instead of checking connectivity quality, just count leads.
# Most "Disconnected" defects in this set are leads that are missing/cut high.
LEAD_COUNT_PROMPT = """
Count the thin metal leads extending from the black body.

Answer DEFECT if:
- You see ZERO leads.
- You see ONE lead.
- You see TWO leads.
- You see clearly FLOATING leads (detached from body).

Answer NORMAL if:
- You see THREE leads (even if bent, short, or in shadow).
- You are not sure.

CRITICAL: If you see 3 things that look like leads, say NORMAL.

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


def targeted_fn_v9(image_path: str) -> tuple:
    """
    Ultra-Conservative FN Detection
    """
    base64_image = encode_image(image_path)
    
    # Check 1: Presence
    res = call_api(PRESENCE_PROMPT, base64_image, "PRESENCE-v9")
    if "NO" in res:
        return True, "FN: Empty Image"
    
    # Check 2: Leads (Count only)
    res = call_api(LEAD_COUNT_PROMPT, base64_image, "LEAD-v9")
    if "DEFECT" in res:
        return True, "FN: Lead Count Defect"
    
    # Check 3: Orientation
    res = call_api(ORIENTATION_PROMPT, base64_image, "ORIENT-v9")
    if "DEFECT" in res:
        return True, "FN: Orientation Defect"
    
    return False, "NORMAL"
