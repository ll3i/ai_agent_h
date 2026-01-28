
"""
V14 Dispute Resolver
====================
Purpose: Resolve disagreements between V8 (Aggressive) and V10 (Conservative).
Context:
- V8 says DEFECT (likely Shadow or Cut)
- V10 says NORMAL (likely Normal or Ambiguous)

Target: Differentiate "Real Physical Cut" vs "Shadow Artifact"

Prompt Strategy:
- Frame it as a dispute between two inspectors.
- Ask for visual proof of a "PHYSICAL GAP" in the metal.
- Bias: If you see a Gap -> Defect. If continuous even if dark -> Normal.
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
# DISPUTE RESOLUTION PROMPT
# ===============================

DISPUTE_PROMPT = """
Two inspectors disagree on this transistor image.
- Inspector A says: "DEFECT! I see a broken lead or wrong orientation."
- Inspector B says: "NORMAL! It's just a shadow or camera angle."

**YOU are the Judge.**

**TASK**: Look at the metal leads and body carefully.

**DECIDE DEFECT ONLY IF:**
1. You clearly see a **PHYSICAL GAP** (empty space) in a metal lead.
2. A lead is **MISSING** entirely (only 2 leads).
3. The component is **UPSIDE DOWN** (absolute 180 degree error).
4. The component body is **BROKEN**.

**DECIDE NORMAL IF:**
1. The lead looks dark/black but is **CONTINUOUS** (Shadow).
2. The lead is bent or crossed but **REACHES THE BOTTOM**.
3. You are not sure if there is a gap or just lighting.

**KEY CRITERION**: "Is there a physical break in the material?"
If Yes -> DEFECT
If No/Unsure -> NORMAL

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


def resolve_dispute_v14(image_path: str) -> tuple:
    """
    Run Dispute Resolution.
    """
    base64_image = encode_image(image_path)
    
    res = call_api(DISPUTE_PROMPT, base64_image, "RESOLVER-v14")
    
    if "DEFECT" in res:
        return True, "Judge: Ruled as Real Defect (Gap/Break)"
    else:
        return False, "Judge: Ruled as Normal (Shadow/Ambiguous)"
