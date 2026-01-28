
"""
V12 Sanity Check
================
Purpose: Filter False Positives from V8 results.
Input: Images flagged as DEFECT by V8 (that were Normal in V4).
Logic: "Is this REALLY a defect? Or just a shadow/minor issue?"

Prompt Strategy:
- Acknowledge a potential defect was found.
- Ask to verify if it's "MAJOR" or "MINOR/SHADOW".
- If unsure, bias towards KEEPING the defect (to protect Recall).
- Only reject if clearly Normal (shadows, lighting, minor bends).
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
# SANITY CHECK PROMPT
# ===============================

SANITY_CHECK_PROMPT = """
You are a Senior QC Inspector verifying a potential defect flagged by a junior inspector.

The junior inspector flagged this component as having a:
- MISSING LEAD
- CUT LEAD
- or ORIENTATION ERROR

**Your Job**: Verify if this is a REAL FUNCTIONAL DEFECT or a FALSE ALARM.

**FALSE ALARM (Answer NORMAL)** if:
- It's just a SHADOW on the board looking like a cut.
- The leads are there but just crossed or bent.
- The image is dark/blurry but the component shape looks generally correct.
- There are minor scratches or marks.

**REAL DEFECT (Answer DEFECT)** if:
- A lead is DEFINITELY missing or stops in mid-air.
- The component is DEFINITELY upside down.
- There is NO component (empty board).

**CRITICAL**: If you are 50/50 unsure, say DEFECT (Better safe than sorry).
Only override to NORMAL if you see evidence it's a false alarm (like shadows).

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


def sanity_check_v12(image_path: str) -> tuple:
    """
    Run Sanity Check on a potential defect.
    """
    base64_image = encode_image(image_path)
    
    res = call_api(SANITY_CHECK_PROMPT, base64_image, "SANITY-v12")
    
    if "NORMAL" in res:
        return False, "Sanity Check: False Alarm (Shadow/Minor)"
    else:
        return True, "Sanity Check: Confirmed Defect"
