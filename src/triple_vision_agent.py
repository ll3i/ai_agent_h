"""
Triple Vision Agent: Full Image + Body ROI + Lead ROI
3개의 이미지를 동시에 분석하여 맥락 + 세부 분석 결합

핵심 전략:
- Full Image: 전체적인 불량 패턴 파악 (맥락 유지)
- Body ROI: 몰딩/패키지 상태 집중 분석
- Lead ROI: 리드/다리 상태 집중 분석
"""

import os
import json
import re
import base64
import logging
import requests
from typing import Tuple
from dotenv import load_dotenv

from src.roi_cropper import crop_body_roi, crop_lead_roi

load_dotenv()
logger = logging.getLogger(__name__)

# API 설정 (integrated_agent.py와 동일)
BRIDGE_URL = os.getenv('SALTLUX_API_BASE_URL', 'https://bridge.luxiacloud.com/llm/openai/chat/completions/{model}/create')
API_KEY = os.getenv("SALTLUX_API_KEY", "")
HEADERS = {"apikey": API_KEY, "Content-Type": "application/json"}
MODEL = os.getenv("MODEL_JUDGE", "luxia3-llm-32b-0731")


# =========================
# Triple Vision 프롬프트
# =========================
TRIPLE_VISION_PROMPT = """
You are analyzing a **TO-92 Transistor** with **3 IMAGES**:

【IMAGE 1 - FULL VIEW】
- Use this for OVERALL context
- Check: Is the component present? Correct posture? Rotation?

【IMAGE 2 - BODY ZOOM】
- Focus on the BLACK PLASTIC PACKAGE
- Check: Cracks? Holes? Damage to molding?

【IMAGE 3 - LEAD ZOOM】  
- Focus on the METAL LEADS (exactly 3 vertical pins)
- Check: Cut leads? Missing leads? Leads touching?
- ⚠️ IGNORE horizontal copper traces on the stripboard!

【DEFECT DETECTION - BE CAREFUL】
Analyze ALL 3 images together before deciding!

1. component_missing: Is the black body completely absent in Image 1?

2. lead_connectivity_fail ⭐ MOST IMPORTANT ⭐
   - Check Image 1: Are all 3 leads visible from body to board?
   - Check Image 3: Any lead cut, bent, broken, or touching?
   - ⚠️ If ANY lead issue detected → TRUE
   - ⚠️ When uncertain → TRUE (better to over-detect)

3. body_broken_severe: Is internal chip exposed through package damage?

4. posture_bad: Is the component lying down or upside down?

5. rotation_severe: Is rotation >= 45 degrees?

【SHADOW RULE】
- Shadows make leads look darker but DON'T break them
- Look for PHYSICAL GAPS or MISSING sections, not just dark colors
- If lead is continuous (even if dark) → NOT a defect

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


def classify_triple_vision(image_path: str) -> Tuple[int, str]:
    """
    Triple Vision 분류: Full + Body ROI + Lead ROI
    
    Returns:
        (label, reason)
    """
    logger.info(f"[TRIPLE VISION] Classifying: {image_path}")
    
    # 1. 이미지 로드 및 크로핑
    full_bytes = _load_image_bytes(image_path)
    body_bytes = crop_body_roi(image_path)
    lead_bytes = crop_lead_roi(image_path)
    
    # 2. Base64 인코딩
    full_b64 = base64.b64encode(full_bytes).decode('utf-8')
    body_b64 = base64.b64encode(body_bytes).decode('utf-8')
    lead_b64 = base64.b64encode(lead_bytes).decode('utf-8')
    
    # 3. LLM 호출 with 3 images
    try:
        response = _post_chat([
            {"role": "system", "content": "You are a precision quality inspector for TO-92 transistors. Analyze ALL 3 images carefully."},
            {"role": "user", "content": [
                {"type": "text", "text": TRIPLE_VISION_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{full_b64}"}},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{body_b64}"}},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{lead_b64}"}}
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
        logger.error(f"  [TRIPLE VISION] Error: {e}")
        return 0, f"Error: {e}"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        label, reason = classify_triple_vision(sys.argv[1])
        print(f"Result: {'ABNORMAL' if label == 1 else 'NORMAL'}")
        print(f"Reason: {reason}")
