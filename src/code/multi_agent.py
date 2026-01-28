"""
Multi-Agent Inspector System
Body Inspector와 Lead Inspector로 분업화된 분석

각 에이전트는 전문화된 프롬프트로 해당 영역만 집중 분석
"""

import os
import json
import re
import base64
import logging
import requests
from typing import Dict, Tuple
from dotenv import load_dotenv

from src.roi_cropper import crop_both_rois

load_dotenv()
logger = logging.getLogger(__name__)

# API 설정
BRIDGE_URL = os.getenv('SALTLUX_API_BASE_URL', 'https://bridge.luxiacloud.com/llm/openai/chat/completions/{model}/create')
API_KEY = os.getenv("SALTLUX_API_KEY", "")
HEADERS = {"apikey": API_KEY, "Content-Type": "application/json"}
MODEL = os.getenv("MODEL_JUDGE", "luxia3-llm-32b-0731")


# =========================
# Body Inspector (몰딩/패키지 전문)
# =========================
BODY_INSPECTOR_PROMPT = """
You are a **TO-92 Transistor BODY Inspector**.
You are analyzing ONLY the **upper portion** of the image containing the BLACK PLASTIC PACKAGE (molding).

【YOUR FOCUS】
✅ Black plastic body of the TO-92 transistor
✅ Package integrity (cracks, holes, damage)
✅ Component presence/absence

【IGNORE】
❌ Leads/legs (NOT your responsibility)
❌ Copper traces on the stripboard background
❌ Any metal pins

【DEFECT CATEGORIES】
1. component_missing: Is the black plastic body completely absent?
2. body_broken_severe: Is internal circuitry/chip VISIBLY exposed through the package?
   - Surface scratches = FALSE (normal)
   - Cracks exposing internals = TRUE

Output ONLY this JSON:
{"component_missing": false, "body_broken_severe": false}
"""


# =========================
# Lead Inspector (리드/다리 전문) - 민감도 증가 버전
# =========================
LEAD_INSPECTOR_PROMPT = """
You are a **HIGHLY SENSITIVE TO-92 Transistor LEAD Inspector**.
You are analyzing the **lower portion** of the image containing the METAL LEADS (legs).

⚠️ YOUR MISSION: Find ANY potential lead defects. When in doubt, mark as DEFECT!

【CRITICAL CONTEXT】
- Background: Orange/Copper STRIPBOARD with horizontal copper traces
- Transistor leads: VERTICAL silver/gray metal pins (EXACTLY 3: LEFT, CENTER, RIGHT)
- ⚠️ DO NOT confuse horizontal copper traces with transistor leads!

【DEFECT DETECTION - BE AGGRESSIVE】
1. lead_connectivity_fail: Mark TRUE if ANY of these:
   - Lead appears CUT, BROKEN, or SHORTENED
   - Lead is MISSING or not visible (less than 3 leads)
   - Leads are TOUCHING or TOO CLOSE (< 1mm spacing)
   - Lead looks BENT, TILTED, or DISPLACED
   - Lead is NOT fully inserted in hole
   - ANY visual anomaly on leads
   
   ⚠️ IMPORTANT: If you see ANYTHING unusual about the leads → TRUE
   ⚠️ If unsure → Mark TRUE (false positive is better than missing defect!)

2. posture_bad: Component lying down or upside down

3. rotation_severe: >= 45 degree rotation

【SHADOW vs DEFECT - Conservative Rule】
- If the dark area COMPLETELY blocks the lead path → Assume DEFECT (TRUE)
- Only mark as shadow if lead is CLEARLY continuous

Output ONLY this JSON:
{"lead_connectivity_fail": false, "posture_bad": false, "rotation_severe": false}
"""


def _post_chat(messages, timeout=60) -> str:
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


def inspect_body(body_image_bytes: bytes) -> Dict[str, bool]:
    """
    Body Inspector: 몰딩/패키지 영역 분석
    
    Returns:
        {'component_missing': bool, 'body_broken_severe': bool}
    """
    logger.info("  [BODY INSPECTOR] Analyzing package region...")
    
    img_b64 = base64.b64encode(body_image_bytes).decode('utf-8')
    
    try:
        response = _post_chat([
            {"role": "system", "content": "You are a precision quality inspector for TO-92 transistors."},
            {"role": "user", "content": [
                {"type": "text", "text": BODY_INSPECTOR_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
            ]}
        ])
        
        result = _safe_json_extract(response)
        return {
            "component_missing": bool(result.get("component_missing", False)),
            "body_broken_severe": bool(result.get("body_broken_severe", False))
        }
    except Exception as e:
        logger.error(f"  [BODY INSPECTOR] Error: {e}")
        return {"component_missing": False, "body_broken_severe": False}


def inspect_lead(lead_image_bytes: bytes) -> Dict[str, bool]:
    """
    Lead Inspector: 리드/다리 영역 분석
    
    Returns:
        {'lead_connectivity_fail': bool, 'posture_bad': bool, 'rotation_severe': bool}
    """
    logger.info("  [LEAD INSPECTOR] Analyzing lead region...")
    
    img_b64 = base64.b64encode(lead_image_bytes).decode('utf-8')
    
    try:
        response = _post_chat([
            {"role": "system", "content": "You are a precision quality inspector for TO-92 transistors."},
            {"role": "user", "content": [
                {"type": "text", "text": LEAD_INSPECTOR_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
            ]}
        ])
        
        result = _safe_json_extract(response)
        return {
            "lead_connectivity_fail": bool(result.get("lead_connectivity_fail", False)),
            "posture_bad": bool(result.get("posture_bad", False)),
            "rotation_severe": bool(result.get("rotation_severe", False))
        }
    except Exception as e:
        logger.error(f"  [LEAD INSPECTOR] Error: {e}")
        return {"lead_connectivity_fail": False, "posture_bad": False, "rotation_severe": False}


def aggregate_decision(body_result: Dict, lead_result: Dict) -> Tuple[int, str]:
    """
    두 Inspector의 결과를 종합하여 최종 판정
    
    Returns:
        (label, reason)
        - label: 0 = Normal, 1 = Abnormal
        - reason: 판정 근거
    """
    defects = []
    
    # Body defects
    if body_result.get("component_missing"):
        defects.append("component_missing")
    if body_result.get("body_broken_severe"):
        defects.append("body_broken_severe")
    
    # Lead defects
    if lead_result.get("lead_connectivity_fail"):
        defects.append("lead_connectivity_fail")
    if lead_result.get("posture_bad"):
        defects.append("posture_bad")
    if lead_result.get("rotation_severe"):
        defects.append("rotation_severe")
    
    if len(defects) == 0:
        return 0, "All inspections passed"
    else:
        return 1, f"Defects: {', '.join(defects)}"


def classify_multi_agent(image_path: str) -> Tuple[int, str]:
    """
    Multi-Agent 방식 분류
    
    1. 이미지를 Body/Lead ROI로 분리
    2. 각 Inspector가 분석
    3. 결과 종합
    
    Returns:
        (label, reason)
    """
    logger.info(f"[MULTI-AGENT] Classifying: {image_path}")
    
    # 1. ROI 크로핑
    rois = crop_both_rois(image_path)
    
    # 2. 각 Inspector 호출
    body_result = inspect_body(rois['body'])
    lead_result = inspect_lead(rois['lead'])
    
    logger.info(f"  Body: {body_result}")
    logger.info(f"  Lead: {lead_result}")
    
    # 3. 최종 판정
    label, reason = aggregate_decision(body_result, lead_result)
    
    logger.info(f"  Final: {'ABNORMAL' if label == 1 else 'NORMAL'} ({reason})")
    
    return label, reason


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        label, reason = classify_multi_agent(sys.argv[1])
        print(f"Result: {'ABNORMAL' if label == 1 else 'NORMAL'}")
        print(f"Reason: {reason}")
