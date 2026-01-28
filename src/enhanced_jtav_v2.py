
"""
Enhanced J-T-A-V Classification Agent v2.0
=====================================
Improvements based on user feedback:
1. Empty Image Detection (No Component = Defect)
2. Lead Connectivity Strict Check
3. Orientation/Rotation Detection
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

# API 설정 - 기존 jtav_triple_vision.py와 동일하게
BRIDGE_URL = os.getenv('SALTLUX_API_BASE_URL', 'https://bridge.luxiacloud.com/llm/openai/chat/completions/{model}/create')
API_KEY = os.getenv("SALTLUX_API_KEY", "")
HEADERS = {"apikey": API_KEY, "Content-Type": "application/json"}
MODEL = os.getenv("MODEL_JUDGE", "luxia3-llm-32b-0731")

logger = logging.getLogger(__name__)

# ===============================
# ENHANCED PROMPTS v2.0
# ===============================

STAGE1_COMPONENT_CHECK_PROMPT = """
## Task: Component Presence Check

Look at this image carefully.

**Question**: Is there a TO-92 transistor component (a small black plastic body with metal legs) visible in the image?

**Answer Rules**:
- If you see ONLY a brown pegboard with holes and NO black plastic component → Answer: MISSING
- If you see a black plastic transistor body (even partial) → Answer: PRESENT

Answer with ONE word: MISSING or PRESENT
"""

STAGE2_ORIENTATION_CHECK_PROMPT = """
## Task: Orientation Check

A normal TO-92 transistor should be:
- Upright with the flat side facing forward
- Metal leads pointing DOWNWARD
- NOT upside down or rotated more than 30 degrees

**Question**: Is this transistor properly oriented?

**Answer Rules**:
- If component is upside down (leads pointing UP) → Answer: BAD
- If component is rotated/tilted more than 30 degrees → Answer: BAD
- If component is properly upright with leads DOWN → Answer: OK

Answer with ONE word: BAD or OK
"""

STAGE3_LEAD_CONNECTIVITY_PROMPT = """
## Task: Lead Connectivity Inspection (STRICT)

A normal TO-92 transistor has 3 metal leads that must:
1. Be attached to the body
2. Extend continuously DOWNWARD
3. Reach near the BOTTOM of the image
4. NOT be cut, broken, bent excessively, or missing

**Inspect each lead carefully**:
- Left lead: Connected and extends to bottom?
- Center lead: Connected and extends to bottom?
- Right lead: Connected and extends to bottom?

**DEFECT conditions** (answer DEFECT if ANY is true):
- Any lead is completely missing
- Any lead is cut/broken (stops abruptly, doesn't reach bottom)
- Any lead is severely bent (>45 degrees from vertical)
- Leads are shorted together (touching each other)

Answer with ONE word: DEFECT or NORMAL
"""

STAGE4_BODY_CHECK_PROMPT = """
## Task: Body Integrity Check

Inspect the black plastic body of the transistor for:
- Cracks or chips
- Missing pieces
- Discoloration or burn marks
- Damaged markings

Answer with ONE word: DEFECT or NORMAL
"""


def encode_image(image_path: str) -> str:
    """Encode image to base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def call_vision_api(prompt: str, base64_image: str, max_tokens: int = 50) -> str:
    """Call Saltlux Vision API via bridge.luxiacloud.com - 기존 jtav와 동일 방식"""
    # URL에서 {model} 대체
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
            return data["choices"][0]["message"]["content"].strip().upper()
        else:
            logger.error(f"API Error: {response.status_code}")
            return "ERROR"
    except Exception as e:
        logger.error(f"API Exception: {e}")
        return "ERROR"


def classify_enhanced_jtav(image_path: str) -> tuple:
    """
    Enhanced J-T-A-V Classification with 4-Stage Pipeline
    
    Stage 1: Component Presence Check (NEW)
    Stage 2: Orientation Check (NEW)
    Stage 3: Lead Connectivity (Enhanced)
    Stage 4: Body Integrity Check
    
    Returns: (label: int, reason: str)
    """
    base64_image = encode_image(image_path)
    reasons = []
    
    # ===== STAGE 1: Component Presence =====
    logger.info("Stage 1: Component Presence Check")
    result1 = call_vision_api(STAGE1_COMPONENT_CHECK_PROMPT, base64_image)
    
    if "MISSING" in result1:
        logger.info("→ DEFECT: No component visible (empty image)")
        return 1, "DEFECT: No component visible in image (empty/missing)"
    
    reasons.append("Component present")
    
    # ===== STAGE 2: Orientation Check =====
    logger.info("Stage 2: Orientation Check")
    result2 = call_vision_api(STAGE2_ORIENTATION_CHECK_PROMPT, base64_image)
    
    if "BAD" in result2:
        logger.info("→ DEFECT: Component orientation incorrect")
        return 1, "DEFECT: Component is rotated/upside-down"
    
    reasons.append("Orientation OK")
    
    # ===== STAGE 3: Lead Connectivity (Strict) =====
    logger.info("Stage 3: Lead Connectivity Check (Strict)")
    result3 = call_vision_api(STAGE3_LEAD_CONNECTIVITY_PROMPT, base64_image)
    
    if "DEFECT" in result3:
        logger.info("→ DEFECT: Lead connectivity issue")
        return 1, "DEFECT: Lead connectivity problem (cut/missing/bent)"
    
    reasons.append("Leads connected")
    
    # ===== STAGE 4: Body Check =====
    logger.info("Stage 4: Body Integrity Check")
    result4 = call_vision_api(STAGE4_BODY_CHECK_PROMPT, base64_image)
    
    if "DEFECT" in result4:
        logger.info("→ DEFECT: Body damage detected")
        return 1, "DEFECT: Body damage (crack/chip)"
    
    reasons.append("Body intact")
    
    # ===== ALL PASSED =====
    logger.info("→ NORMAL: All checks passed")
    return 0, f"NORMAL: {', '.join(reasons)}"


# ===============================
# WRAPPER FOR BACKWARD COMPATIBILITY
# ===============================

def classify_omni_enhanced(image_path: str) -> tuple:
    """
    Wrapper function for enhanced classification
    Compatible with existing run scripts
    """
    return classify_enhanced_jtav(image_path)


if __name__ == "__main__":
    # Quick test
    import sys
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        label, reason = classify_enhanced_jtav(test_path)
        print(f"Result: {label} ({reason})")
