
"""
V13 Sanity Check (Extremely Conservative)
=========================================
Purpose: Filter ONLY OBVIOUS False Positives from V8.
Policy: "Guilty until proven Innocent"

V12 failed because it reverted real defects.
V13 strategy:
- Assume V8 is correct (DEFECT).
- Only revert to NORMAL if it is 100% CLEARLY a shadow/lighting issue.
- If there is ANY doubt (even 1%), keep it as DEFECT.
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
# V13 CONSERVATIVE PROMPT
# ===============================

SANITY_CHECK_PROMPT_V13 = """
You are a Final Reviewer checking a reported defect.
The previous system marked this component as DEFECTIVE.

**Your Goal**: Identify FALSE ALARMS caused by shadows or lighting.

** STRICT RULES **:
1. **DEFAULT TO DEFECT**: Unless you are 100% SURE it is a false alarm, you must agree it is a DEFECT.
2. **FALSE ALARM CRITERIA**:
   - You can clearly see the lead continues through the shadow.
   - It is obviously just a lighting artifact on the board.
   - The leads are just crossed/bent but definitely connected.
3. **REAL DEFECT CRITERIA**:
   - Any missing lead.
   - Any cut lead.
   - Any ambiguity or blurriness (If you can't see it clearly, ASSUME DEFECT).

**QUESTION**: Is this absolutely, 100% a false alarm?

Answer **NORMAL** only if you are absolutely certain it is a false alarm.
Answer **DEFECT** if there is any chance it is a real defect.

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


def sanity_check_v13(image_path: str) -> tuple:
    """
    Run V13 Conservative Sanity Check.
    """
    base64_image = encode_image(image_path)
    
    res = call_api(SANITY_CHECK_PROMPT_V13, base64_image, "SANITY-v13")
    
    if "NORMAL" in res:
        return False, "False Alarm (100% Sure)"
    else:
        return True, "Defect Maintained"
