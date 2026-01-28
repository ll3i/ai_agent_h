
"""
Enhanced J-T-A-V Classification Agent v3.0
==========================================
Improvements based on user error analysis:

[False Negative 개선 - 놓친 불량 감지]
1. Empty Image Detection - 부품이 없는 이미지 감지 강화
2. Lead Disconnection - 리드 연결 불량 감지 강화 (엄격하게)
3. Orientation - 뒤집힘/비틀림 감지 강화

[False Positive 개선 - 과검 감소]  
4. 정상 부품에 대한 관대한 판정 (그림자/노이즈 무시)
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# ===============================
# IMPROVED PROMPTS v3.0
# ===============================

# Stage 1: 부품 존재 여부 확인 (Empty Image Detection)
STAGE1_COMPONENT_PROMPT = """
## Task: Component Presence Check (CRITICAL)

Look at this image. Your ONLY job is to determine if there is a transistor component.

**MISSING (DEFECT) conditions:**
- You see ONLY a brown/orange pegboard with round holes
- There is NO black plastic body visible anywhere
- The image is essentially "empty" - just the board

**PRESENT (continue checking) conditions:**
- You can see a black rectangular/semi-circular plastic body
- There are metal leads visible attached to a component

Be VERY STRICT: If you cannot clearly see a black transistor body, answer MISSING.

Answer: MISSING or PRESENT
"""

# Stage 2: 방향/자세 확인 (Orientation Check)  
STAGE2_ORIENTATION_PROMPT = """
## Task: Orientation Check (STRICT)

A NORMAL TO-92 transistor position:
- The black plastic body is at the TOP
- 3 metal leads extend DOWNWARD from the body
- The flat side of the body faces the camera
- Rotation less than 30 degrees from vertical

**DEFECT conditions - answer BAD if ANY is true:**
1. Component is UPSIDE DOWN (leads pointing UP, body at bottom)
2. Component is FLIPPED (you see the rounded back instead of flat front)
3. Component is ROTATED more than 45 degrees
4. Component is LYING ON ITS SIDE

**NORMAL condition:**
- Body at top, 3 leads going down, relatively upright

Be STRICT about orientation. If it looks wrong, say BAD.

Answer: BAD or OK
"""

# Stage 3: 리드 연결 상태 확인 (Lead Connectivity - VERY STRICT)
STAGE3_LEAD_PROMPT = """
## Task: Lead Connectivity Check (VERY STRICT - THIS IS CRITICAL)

A TO-92 transistor has 3 metal leads. Each lead must:
1. Be attached to the black body at the top
2. Extend CONTINUOUSLY downward (no breaks)
3. Reach the BOTTOM edge of the visible area
4. Be SEPARATE from other leads (not touching)

**CRITICAL - Check each lead position:**
- LEFT lead (Pin 1): Is it connected from body to bottom?
- CENTER lead (Pin 2): Is it connected from body to bottom?  
- RIGHT lead (Pin 3): Is it connected from body to bottom?

**DEFECT conditions - answer DEFECT if ANY is true:**
✗ Any lead is MISSING (you only see 2 or fewer leads)
✗ Any lead is CUT/BROKEN (stops before reaching bottom)
✗ Any lead is BENT SIDEWAYS (connecting to the side instead of down)
✗ Leads are SHORTED (two leads touching each other)
✗ Lead appears DISCONNECTED from the body
✗ Lead is floating or not soldered through the hole

**IMPORTANT: Shadows on the board are OK. Focus only on the METAL LEADS themselves.**

If you have ANY doubt about a lead's connectivity, answer DEFECT.

Answer: DEFECT or NORMAL
"""

# Stage 4: 바디 상태 확인 (Body Check - relaxed)
STAGE4_BODY_PROMPT = """
## Task: Body Integrity Check

Check the black plastic body for MAJOR physical damage only.

**DEFECT conditions (major damage only):**
- Large crack visible on the body
- Piece of the body is missing/broken off
- Body is severely deformed

**NORMAL conditions (minor issues are OK):**
- Small scratches are acceptable
- Slight discoloration is acceptable
- Text/markings are faded - this is OK
- Minor surface imperfections - OK

Be LENIENT here. Only major structural damage counts as defect.

Answer: DEFECT or NORMAL
"""


def encode_image(image_path: str) -> str:
    """Encode image to base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def call_vision_api(prompt: str, base64_image: str, stage_name: str) -> str:
    """Call Saltlux Vision API via bridge.luxiacloud.com"""
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
            result = data["choices"][0]["message"]["content"].strip().upper()
            logger.info(f"  [{stage_name}] → {result[:50]}")
            return result
        else:
            logger.error(f"  [{stage_name}] API Error: {response.status_code}")
            return "ERROR"
    except Exception as e:
        logger.error(f"  [{stage_name}] Exception: {e}")
        return "ERROR"


def classify_v3(image_path: str) -> tuple:
    """
    Enhanced J-T-A-V Classification v3.0
    
    Key improvements:
    - Stage 1: STRICT empty image detection
    - Stage 2: STRICT orientation check  
    - Stage 3: VERY STRICT lead connectivity
    - Stage 4: RELAXED body check (reduce false positives)
    
    Returns: (label: int, reason: str)
    """
    base64_image = encode_image(image_path)
    
    # ===== STAGE 1: Component Presence (CRITICAL) =====
    result1 = call_vision_api(STAGE1_COMPONENT_PROMPT, base64_image, "STAGE1-COMPONENT")
    
    if "MISSING" in result1 or "EMPTY" in result1 or "NO" in result1:
        return 1, "DEFECT: No component visible (empty image)"
    
    # ===== STAGE 2: Orientation Check =====
    result2 = call_vision_api(STAGE2_ORIENTATION_PROMPT, base64_image, "STAGE2-ORIENT")
    
    if "BAD" in result2 or "WRONG" in result2 or "DEFECT" in result2:
        return 1, "DEFECT: Orientation problem (flipped/rotated)"
    
    # ===== STAGE 3: Lead Connectivity (CRITICAL) =====
    result3 = call_vision_api(STAGE3_LEAD_PROMPT, base64_image, "STAGE3-LEAD")
    
    if "DEFECT" in result3 or "CUT" in result3 or "MISSING" in result3 or "BROKEN" in result3:
        return 1, "DEFECT: Lead connectivity issue"
    
    # ===== STAGE 4: Body Check (Relaxed) =====
    result4 = call_vision_api(STAGE4_BODY_PROMPT, base64_image, "STAGE4-BODY")
    
    if "DEFECT" in result4 and "MAJOR" in result4:
        return 1, "DEFECT: Body damage"
    
    # ===== ALL PASSED =====
    return 0, "NORMAL: All checks passed"


def classify_omni_v3(image_path: str) -> tuple:
    """Wrapper for backward compatibility"""
    return classify_v3(image_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        label, reason = classify_v3(test_path)
        print(f"Result: {label} ({reason})")
