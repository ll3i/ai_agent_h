
"""
Conservative Classifier v6.0
============================
Strategy: Start from original results + targeted corrections

Based on error analysis:
- Original model had 17 defects
- 7 were False Positives (should be 0): TEST_004, 013, 026, 036, 057, 063, 094
- ~20 were False Negatives (missed defects)

v6 Approach:
1. Check for SPECIFIC known patterns only
2. Be VERY conservative to avoid FP
3. Only catch CLEAR defects
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
# SIMPLE, CLEAR PROMPTS (Conservative)
# ===============================

# Single comprehensive check with CLEAR criteria
CONSERVATIVE_CHECK = """
Inspect this TO-92 transistor image. Answer conservatively - only flag CLEAR defects.

## DEFECT CRITERIA (answer DEFECT only if ONE of these is clearly true):

1. **NO COMPONENT**: The image shows ONLY the brown board - no black transistor body visible at all.

2. **UPSIDE DOWN**: The transistor body is at the BOTTOM with leads pointing UP (reversed orientation).

3. **LEAD CUT/MISSING**: You can clearly see that one of the 3 leads is:
   - Completely missing (only 2 leads visible)
   - Cut in the middle (lead stops before reaching the bottom)
   - Not attached to the body

4. **SEVERE DAMAGE**: Large piece of the body is broken off or cracked through.

## NORMAL CRITERIA:
- If component is present with 3 leads going down → NORMAL
- If there are minor scratches, shadows, or slight bend → NORMAL
- If you're not 100% sure of a defect → NORMAL

Be CONSERVATIVE. Minor imperfections are okay. Only flag CLEAR, OBVIOUS defects.

Answer: DEFECT or NORMAL
Briefly explain (10 words max):
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
            logger.info(f"  [{check_name}] → {result[:80]}...")
            return result
        else:
            logger.error(f"  [{check_name}] API Error: {response.status_code}")
            return "ERROR"
    except Exception as e:
        logger.error(f"  [{check_name}] Exception: {e}")
        return "ERROR"


def classify_v6(image_path: str) -> tuple:
    """
    Conservative v6 Classification
    
    Single comprehensive check with clear criteria.
    Defaults to NORMAL when uncertain.
    
    Returns: (label: int, reason: str)
    """
    base64_image = encode_image(image_path)
    
    result = call_api(CONSERVATIVE_CHECK, base64_image, "CONSERVATIVE")
    result_upper = result.upper()
    
    if "ERROR" in result_upper:
        return 0, "API Error - defaulting to NORMAL"
    
    # Only flag as defect if DEFECT appears prominently
    # and NORMAL is not the main answer
    if result_upper.startswith("DEFECT") or result_upper[:20].count("DEFECT") > result_upper[:20].count("NORMAL"):
        # Extract reason
        reason = result.split(":")[-1].strip()[:50] if ":" in result else result[:50]
        return 1, f"DEFECT: {reason}"
    else:
        return 0, "NORMAL"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        label, reason = classify_v6(test_path)
        print(f"Result: {label} ({reason})")
