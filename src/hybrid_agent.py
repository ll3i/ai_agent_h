"""
Hybrid Agent: Full Image + Lead ROI
전체 이미지(맥락 유지) + Lead ROI(집중 분석)를 함께 사용

Single-Agent의 맥락 + Multi-Agent의 집중력 결합
"""

import os
import json
import re
import base64
import logging
import requests
from typing import Dict, Tuple
from dotenv import load_dotenv

from src.roi_cropper import crop_lead_roi

load_dotenv()
logger = logging.getLogger(__name__)

# API 설정
BRIDGE_URL = os.getenv('SALTLUX_API_BASE_URL', 'https://bridge.luxiacloud.com/llm/openai/chat/completions/{model}/create')
API_KEY = os.getenv("SALTLUX_API_KEY", "")
HEADERS = {"apikey": API_KEY, "Content-Type": "application/json"}
MODEL = os.getenv("MODEL_JUDGE", "luxia3-llm-32b-0731")


# =========================
# Hybrid Inspector Prompt (Full + Lead ROI)
# =========================
HYBRID_PROMPT = """
You are a **HIGHLY SENSITIVE TO-92 Transistor Quality Inspector**.

You are provided with **TWO IMAGES**:
1. **Image 1 (FULL)**: The complete transistor image for overall context
2. **Image 2 (LEAD ZOOM)**: A zoomed-in view of ONLY the lead/leg region

【COMPONENT SPECIFICATION】
- Component: TO-92 Transistor (3-pin plastic package)
- Expected: EXACTLY 3 vertical metal leads (Left, Center, Right)
- Background: Orange/Copper STRIPBOARD
  ⚠️ DO NOT confuse horizontal copper traces with transistor leads!

【INSPECTION STEPS】
STEP 1: Look at Image 1 (FULL) for overall context
- Is the component present?
- Is the posture correct (standing upright)?
- Any severe rotation?

STEP 2: Look at Image 2 (LEAD ZOOM) for detailed lead analysis
- Count the leads: Must be EXACTLY 3
- Check each lead: Cut? Bent? Missing? Touching?
- Look for ANY anomaly

【DEFECT CATEGORIES - BE AGGRESSIVE】
1. component_missing: Body completely absent → TRUE

2. lead_connectivity_fail ⭐⭐⭐ HIGHEST PRIORITY ⭐⭐⭐
   Mark TRUE if ANY of these in EITHER image:
   - Lead appears CUT, BROKEN, or SHORTENED
   - Lead is MISSING (less than 3)
   - Leads are TOUCHING or TOO CLOSE
   - Lead is BENT, TILTED, or DISPLACED
   - Lead NOT fully inserted in hole
   - ANY visual anomaly on leads
   
   ⚠️ When in doubt → Mark TRUE (better safe than sorry!)

3. body_broken_severe: Internal structure visibly exposed → TRUE

4. posture_bad: Lying down or upside down → TRUE

5. rotation_severe: >= 45 degree rotation → TRUE

Output ONLY this JSON:
{
  "component_missing": false,
  "lead_connectivity_fail": false,
  "body_broken_severe": false,
  "posture_bad": false,
  "rotation_severe": false
}
"""


def _post_chat(messages, timeout=90) -> str:
    """LLM API 호출"""
    payload = {"model": MODEL, "messages": messages, "stream": False}
    r = requests.post(BRIDGE_URL, headers=HEADERS, json=payload, timeout=timeout)
    
    if r.status_code != 200:
        raise RuntimeError(f"API Error: {r.status_code}")
    
    return r.json()["choices"][0]["message"]["content"].strip()


def _safe_json_extract(s: str) -> dict:
    """JSON 안전 추출"""
    try:
        return json.loads(s)
    except:
        m = re.search(r"\{.*\}", s, flags=re.S)
        if m:
            return json.loads(m.group(0))
    return {}


def _load_image_bytes(image_path: str) -> bytes:
    """이미지 바이트 로드"""
    with open(image_path, 'rb') as f:
        return f.read()


def classify_hybrid(image_path: str) -> Tuple[int, str]:
    """
    Hybrid 방식 분류: Full Image + Lead ROI
    
    Returns:
        (label, reason)
    """
    logger.info(f"[HYBRID] Classifying: {image_path}")
    
    # 1. Full image 로드
    full_img_bytes = _load_image_bytes(image_path)
    full_img_b64 = base64.b64encode(full_img_bytes).decode('utf-8')
    
    # 2. Lead ROI 크로핑
    lead_roi_bytes = crop_lead_roi(image_path)
    lead_roi_b64 = base64.b64encode(lead_roi_bytes).decode('utf-8')
    
    # 3. LLM 호출 with 2 images
    try:
        response = _post_chat([
            {"role": "system", "content": "You are a precision quality inspector for TO-92 transistors. Analyze BOTH images carefully."},
            {"role": "user", "content": [
                {"type": "text", "text": HYBRID_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{full_img_b64}"}},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{lead_roi_b64}"}}
            ]}
        ])
        
        result = _safe_json_extract(response)
        logger.info(f"  Result: {result}")
        
        # 판정
        defects = []
        for key, value in result.items():
            if value:
                defects.append(key)
        
        if len(defects) == 0:
            return 0, "All inspections passed"
        else:
            return 1, f"Defects: {', '.join(defects)}"
            
    except Exception as e:
        logger.error(f"  [HYBRID] Error: {e}")
        return 0, f"Error: {e}"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        label, reason = classify_hybrid(sys.argv[1])
        print(f"Result: {'ABNORMAL' if label == 1 else 'NORMAL'}")
        print(f"Reason: {reason}")
