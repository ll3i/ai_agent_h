
"""
Hybrid Classification v4.0
==========================
Strategy: Use ORIGINAL model results as baseline + Supplementary FN detection

The original run (outpu1t.csv with 17 defects) had:
- False Positives: 7 (too many 1s)
- False Negatives: ~20 (missed defects)

Approach:
1. Start with original conservative classification
2. For items classified as NORMAL (0), do additional strict checks:
   - Empty Image Check
   - Clear Lead Disconnection Check
3. This way we catch more FNs without adding more FPs
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
# SUPPLEMENTARY PROMPTS (Only for catching FN)
# ===============================

# Check 1: Empty Image (VERY Important - catches TEST_008, TEST_084)
EMPTY_IMAGE_CHECK = """
Look at this image carefully.

SIMPLE QUESTION: Is there a black transistor component visible?

ANSWER "NO" if:
- You only see a brown board with holes
- There is no electronic component at all
- The image appears empty

ANSWER "YES" if:
- You can see any part of a black plastic component
- There are metal leads attached to something

Answer with single word: YES or NO
"""

# Check 2: Clear Lead Problem (catches disconnected leads)
LEAD_PROBLEM_CHECK = """
Look at the metal leads (the 3 thin vertical metal pins under the black body).

Is there an OBVIOUS lead problem?

ANSWER "YES" (problem exists) if:
- Any lead is clearly CUT or BROKEN (stops in the middle)
- Any lead is MISSING (you can only count 2 or fewer leads)
- Leads are going SIDEWAYS instead of down
- All leads are extremely short / not going to the bottom

ANSWER "NO" (leads look OK) if:
- You can see 3 leads going relatively downward
- Even if slightly bent, they still reach toward the bottom
- Some shadows or darkness is fine

Be conservative - only say YES if there is a CLEAR, OBVIOUS problem.

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


def supplement_check(image_path: str) -> tuple:
    """
    Supplementary check for items already classified as NORMAL.
    Only catches OBVIOUS defects that were missed.
    
    Returns: (should_change_to_defect: bool, reason: str)
    """
    base64_image = encode_image(image_path)
    
    # Check 1: Empty Image
    result1 = call_api(EMPTY_IMAGE_CHECK, base64_image, "EMPTY-CHECK")
    if "NO" in result1:
        return True, "Empty image - no component visible"
    
    # Check 2: Clear Lead Problem
    result2 = call_api(LEAD_PROBLEM_CHECK, base64_image, "LEAD-CHECK")
    if "YES" in result2:
        return True, "Clear lead connectivity problem"
    
    # Passed supplementary checks - keep as NORMAL
    return False, "Supplementary checks passed"


def classify_hybrid(image_path: str, original_label: int) -> tuple:
    """
    Hybrid classification:
    - If original = 1 (defect), keep it
    - If original = 0 (normal), do supplementary checks
    """
    if original_label == 1:
        return 1, "Original classification: DEFECT"
    
    # Original said NORMAL, let's double-check
    should_change, reason = supplement_check(image_path)
    
    if should_change:
        return 1, f"Supplementary catch: {reason}"
    else:
        return 0, "NORMAL (confirmed)"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        # Test with original label = 0
        label, reason = classify_hybrid(test_path, 0)
        print(f"Result: {label} ({reason})")
