"""
J-T-A-V + Triple Vision 통합 에이전트
Judge-Think-Act-Verify 워크플로우 + Triple Vision (Full+Body+Lead)

Step 1: 민감도 증가 프롬프트
Step 2: J-T-A-V 워크플로우
Step 3: Tie-Breaker 로직
"""

import os
import json
import re
import base64
import logging
import requests
from typing import Tuple, Dict, List
from dotenv import load_dotenv

from src.roi_cropper import crop_body_roi, crop_lead_roi

load_dotenv()
logger = logging.getLogger(__name__)

# API 설정
BRIDGE_URL = os.getenv('SALTLUX_API_BASE_URL', 'https://bridge.luxiacloud.com/llm/openai/chat/completions/{model}/create')
API_KEY = os.getenv("SALTLUX_API_KEY", "")
HEADERS = {"apikey": API_KEY, "Content-Type": "application/json"}
MODEL = os.getenv("MODEL_JUDGE", "luxia3-llm-32b-0731")


# =========================
# Step 1: 민감도 증가 프롬프트 (JUDGE)
# =========================
JUDGE_PROMPT = """
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


# =========================
# Step 2: THINK 프롬프트 (분석)
# =========================
THINK_PROMPT = """
Analyze the defects found in this TO-92 transistor inspection.

Previous inspection result: {judge_result}

For each TRUE defect, explain:
1. What exactly is wrong?
2. How severe is it?
3. Confidence level (high/medium/low)?

If lead_connectivity_fail is TRUE, specify which lead(s) are affected.

Output as JSON:
{
  "defects": ["list of defects"],
  "severity": "critical/major/minor",
  "confidence": "high/medium/low",
  "analysis": "brief explanation"
}
"""


# =========================
# Step 3: VERIFY 프롬프트 (Tie-Breaker)
# =========================
VERIFY_PROMPT = """
VERIFICATION CHECK for TO-92 transistor.

Previous result found: {defect_type}

Look at the 3 images again CAREFULLY:
【IMAGE 1】Full view  【IMAGE 2】Body zoom  【IMAGE 3】Lead zoom

QUESTION: Can you GUARANTEE this is just a shadow/noise and NOT a defect?

INSTRUCTION:
- You are looking for FALSE ALARMS.
- If it looks like a defect, answer FALSE (Not a shadow).
- If you are uncertain, answer FALSE (Better to be safe).
- ONLY answer TRUE if you see a continuous, unbroken lead clearly and are 100% sure the previous detection was wrong.

Output ONLY this JSON:
{
  "is_definitely_shadow": true/false,
  "reason": "explanation"
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
    with open(image_path, 'rb') as f:
        return f.read()


def _prepare_images(image_path: str) -> Tuple[str, str, str]:
    """이미지 로드 및 Base64 인코딩"""
    full_bytes = _load_image_bytes(image_path)
    body_bytes = crop_body_roi(image_path)
    lead_bytes = crop_lead_roi(image_path)
    
    return (
        base64.b64encode(full_bytes).decode('utf-8'),
        base64.b64encode(body_bytes).decode('utf-8'),
        base64.b64encode(lead_bytes).decode('utf-8')
    )


# =========================
# J-T-A-V 워크플로우
# =========================

def judge(full_b64: str, body_b64: str, lead_b64: str) -> Dict:
    """
    JUDGE: 민감도 증가된 Triple Vision 검사
    """
    logger.info("  [JUDGE] Analyzing with Triple Vision...")
    
    response = _post_chat([
        {"role": "system", "content": "You are an aggressive quality inspector. Find ANY potential defects!"},
        {"role": "user", "content": [
            {"type": "text", "text": JUDGE_PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{full_b64}"}},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{body_b64}"}},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{lead_b64}"}}
        ]}
    ])
    
    result = _safe_json_extract(response)
    logger.info(f"  [JUDGE] Result: {result}")
    return result


def think(judge_result: Dict) -> Dict:
    """
    THINK: 결함 분석 및 분류
    """
    defects = [k for k, v in judge_result.items() if v]
    
    if not defects:
        return {"defects": [], "severity": "none", "confidence": "high", "analysis": "No defects found"}
    
    logger.info(f"  [THINK] Analyzing defects: {defects}")
    
    # 심각도 결정
    if "component_missing" in defects:
        severity = "critical"
    elif "lead_connectivity_fail" in defects:
        severity = "critical"
    elif "body_broken_severe" in defects:
        severity = "major"
    else:
        severity = "minor"
    
    return {
        "defects": defects,
        "severity": severity,
        "confidence": "high" if len(defects) > 1 else "medium",
        "analysis": f"Found {len(defects)} defect(s): {', '.join(defects)}"
    }


def act(think_result: Dict) -> Tuple[int, str, bool]:
    """
    ACT: 판정 결정 및 Tie-Breaker 필요 여부 결정
    
    Returns:
        (label, reason, needs_verification)
    """
    defects = think_result.get("defects", [])
    
    if not defects:
        logger.info("  [ACT] No defects → NORMAL")
        return 0, "No defects found", False
    
    # 다중 결함 → 즉시 ABNORMAL
    if len(defects) >= 2:
        logger.info(f"  [ACT] Multiple defects ({len(defects)}) → ABNORMAL")
        return 1, f"Multiple defects: {', '.join(defects)}", False
    
    # 단일 결함 → Tie-Breaker (검증) 여부 결정
    # 성능 최적화: 검증 단계가 Recall을 떨어뜨리므로(FN 증가), Judge를 신뢰하고 즉시 결함 판정.
    logger.info(f"  [ACT] Single defect ({defects[0]}) → Trust Judge (Skip Verify to save Recall)")
    return 1, f"Single defect: {defects[0]}", False


def verify(full_b64: str, body_b64: str, lead_b64: str, defect_type: str) -> bool:
    """
    VERIFY: Tie-Breaker - 단일 결함 재검증
    """
    logger.info(f"  [VERIFY] Re-checking: {defect_type}")
    
    prompt = VERIFY_PROMPT.format(defect_type=defect_type)
    
    response = _post_chat([
        {"role": "system", "content": "You are a strict quality verifier. Only confirm REAL defects."},
        {"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{full_b64}"}},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{body_b64}"}},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{lead_b64}"}}
        ]}
    ])
    
    result = _safe_json_extract(response)
    # is_definitely_shadow가 True이면 -> Verified(Normal)로 처리
    # is_definitely_shadow가 False이면 -> Defect(Abnormal)로 유지
    is_shadow = result.get("is_definitely_shadow", False)
    reason = result.get("reason", "N/A")
    
    logger.info(f"  [VERIFY] Is Shadow={is_shadow}, Reason={reason}")
    
    # is_shadow가 True이면 -> 결함 아님 (Verified False? 아니 여기 로직 헷갈림)
    # 원래 verify 함수는 "defect가 verify 되었는가?"를 반환했음.
    # 즉, True를 반환하면 "결함이 맞다(Abnormal)"
    # False를 반환하면 "결함이 아니다(Normal)"
    
    # 여기서는 is_shadow=True 이면 -> 결함 아님 -> return False
    # is_shadow=False 이면 -> 결함 맞음(또는 불확실) -> return True
    
    return not is_shadow


def classify_jtav_triple(image_path: str) -> Tuple[int, str]:
    """
    J-T-A-V + Triple Vision 통합 분류
    
    Returns:
        (label, reason)
    """
    logger.info(f"[J-T-A-V] Classifying: {image_path}")
    
    try:
        # 이미지 준비
        full_b64, body_b64, lead_b64 = _prepare_images(image_path)
        
        # JUDGE
        judge_result = judge(full_b64, body_b64, lead_b64)
        
        # THINK
        think_result = think(judge_result)
        
        # ACT
        label, reason, needs_verification = act(think_result)
        
        # VERIFY (Tie-Breaker)
        if needs_verification:
            defect_type = think_result["defects"][0]
            verified = verify(full_b64, body_b64, lead_b64, defect_type)
            
            if not verified:
                logger.info("  [TIE-BREAKER] Defect NOT verified → NORMAL")
                return 0, f"Defect {defect_type} not verified (likely shadow)"
            else:
                logger.info("  [TIE-BREAKER] Defect verified → ABNORMAL")
                return 1, f"Verified defect: {defect_type}"
        
        return label, reason
        
    except Exception as e:
        logger.error(f"  [ERROR] {e}")
        return 0, f"Error: {e}"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        label, reason = classify_jtav_triple(sys.argv[1])
        print(f"Result: {'ABNORMAL' if label == 1 else 'NORMAL'}")
        print(f"Reason: {reason}")
