"""
Fusion Agent: 3가지 방식의 장점 결합

장점 결합 전략:
1. Single-Agent 장점: 높은 Recall (FN=6) - 민감한 결함 탐지
2. Triple Vision 장점: 균형 잡힌 기본 판정 (72%)
3. J-T-A-V 장점: 높은 Precision (FP=1) - 정확한 검증

Fusion Logic:
Step 1: Triple Vision으로 기본 분석
Step 2: Normal 판정 → 민감도 증가 재검사 (FN 방지)
Step 3: Abnormal 판정 + 단일 결함 → Tie-Breaker (FP 방지)
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
# Triple Vision 기본 프롬프트 (균형 잡힌)
# =========================
BALANCED_PROMPT = """
You are analyzing a **TO-92 Transistor** with **3 IMAGES**:
【IMAGE 1】Full view  【IMAGE 2】Body zoom  【IMAGE 3】Lead zoom

【DEFECT DETECTION】
1. component_missing: Black body completely absent?
2. lead_connectivity_fail: Any lead cut, broken, touching, or missing? (EXACTLY 3 leads required)
3. body_broken_severe: Internal chip exposed through damage?
4. posture_bad: Component lying down or upside down?
5. rotation_severe: Rotation >= 45 degrees?

【BACKGROUND】
- Orange stripboard with horizontal copper traces
- IGNORE copper traces, focus on VERTICAL leads

Output ONLY this JSON:
{"component_missing": false, "lead_connectivity_fail": false, "body_broken_severe": false, "posture_bad": false, "rotation_severe": false}
"""


# =========================
# 민감도 증가 프롬프트 (FN 방지)
# =========================
SENSITIVE_PROMPT = """
⚠️ SECOND CHECK - BE AGGRESSIVE! ⚠️

Look at the 3 images again. The first check said NORMAL.
Your job: Find ANY defect that was MISSED!

CHECK VERY CAREFULLY:
- Are there EXACTLY 3 leads visible?
- Is ANY lead shorter, bent, or damaged?
- Do the leads look unusual in ANY way?
- Is the component rotated or tilted?

RULE: If ANYTHING looks suspicious → Mark TRUE!
RULE: When uncertain → Mark TRUE (over-detect is better!)

Output ONLY this JSON:
{"lead_connectivity_fail": false, "any_defect_found": false}
"""


# =========================
# Tie-Breaker 프롬프트 (FP 방지)
# =========================
PRECISION_PROMPT = """
⚠️ VERIFICATION CHECK - BE STRICT! ⚠️

Previous check detected: {defect_type}

Look at the 3 images CAREFULLY. Is this a REAL defect or just a shadow/noise?

REAL DEFECT:
- Physical gap or break in the lead
- Lead is truly missing or cut
- Clear damage visible

SHADOW/NOISE (NOT a defect):
- Dark area but lead is continuous
- Lead goes from body to board without break
- Just lighting/shadow effect

Output ONLY this JSON:
{"is_real_defect": true, "reason": "explanation"}
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


def _build_image_content(full_b64: str, body_b64: str, lead_b64: str, prompt: str) -> list:
    """3개 이미지 + 프롬프트 메시지 구성"""
    return [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{full_b64}"}},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{body_b64}"}},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{lead_b64}"}}
    ]


# =========================
# Fusion Agent 메인 로직
# =========================

def step1_balanced_check(full_b64: str, body_b64: str, lead_b64: str) -> Dict:
    """Step 1: Triple Vision 균형 잡힌 기본 분석"""
    logger.info("  [Step1] Balanced Triple Vision check...")
    
    response = _post_chat([
        {"role": "system", "content": "You are a quality inspector."},
        {"role": "user", "content": _build_image_content(full_b64, body_b64, lead_b64, BALANCED_PROMPT)}
    ])
    
    result = _safe_json_extract(response)
    logger.info(f"  [Step1] Result: {result}")
    return result


def step2_sensitive_recheck(full_b64: str, body_b64: str, lead_b64: str) -> bool:
    """Step 2: Normal 판정 시 민감도 증가 재검사 (FN 방지)"""
    logger.info("  [Step2] Sensitive recheck for missed defects...")
    
    response = _post_chat([
        {"role": "system", "content": "You are an AGGRESSIVE defect finder. Find what was missed!"},
        {"role": "user", "content": _build_image_content(full_b64, body_b64, lead_b64, SENSITIVE_PROMPT)}
    ])
    
    result = _safe_json_extract(response)
    any_defect = result.get("lead_connectivity_fail", False) or result.get("any_defect_found", False)
    
    logger.info(f"  [Step2] Defect found: {any_defect}")
    return any_defect


def step3_precision_verify(full_b64: str, body_b64: str, lead_b64: str, defect_type: str) -> bool:
    """Step 3: Abnormal 판정 시 정밀 검증 (FP 방지)"""
    logger.info(f"  [Step3] Precision verification for: {defect_type}")
    
    prompt = PRECISION_PROMPT.format(defect_type=defect_type)
    
    response = _post_chat([
        {"role": "system", "content": "You are a strict quality verifier."},
        {"role": "user", "content": _build_image_content(full_b64, body_b64, lead_b64, prompt)}
    ])
    
    result = _safe_json_extract(response)
    is_real = result.get("is_real_defect", True)
    reason = result.get("reason", "N/A")
    
    logger.info(f"  [Step3] Real defect: {is_real}, Reason: {reason}")
    return is_real


def classify_fusion(image_path: str) -> Tuple[int, str]:
    """
    Fusion Agent: 3가지 방식의 장점 결합
    
    Returns:
        (label, reason)
    """
    logger.info(f"[FUSION] Classifying: {image_path}")
    
    try:
        # 이미지 준비
        full_b64, body_b64, lead_b64 = _prepare_images(image_path)
        
        # Step 1: 균형 잡힌 기본 분석
        step1_result = step1_balanced_check(full_b64, body_b64, lead_b64)
        
        # 결함 목록 추출
        defects = [k for k, v in step1_result.items() if v]
        
        if len(defects) == 0:
            # Normal 판정 → Step 2: 민감도 증가 재검사
            has_missed_defect = step2_sensitive_recheck(full_b64, body_b64, lead_b64)
            
            if has_missed_defect:
                logger.info("  [FUSION] Step2 found missed defect → ABNORMAL")
                return 1, "Defect found in sensitive recheck"
            else:
                logger.info("  [FUSION] No defects in both checks → NORMAL")
                return 0, "No defects found (double-checked)"
        
        elif len(defects) >= 2:
            # 다중 결함 → 즉시 ABNORMAL
            logger.info(f"  [FUSION] Multiple defects ({len(defects)}) → ABNORMAL")
            return 1, f"Multiple defects: {', '.join(defects)}"
        
        else:
            # 단일 결함 → Step 3: 정밀 검증 (FP 방지)
            defect_type = defects[0]
            is_real = step3_precision_verify(full_b64, body_b64, lead_b64, defect_type)
            
            if is_real:
                logger.info(f"  [FUSION] Single defect verified → ABNORMAL")
                return 1, f"Verified defect: {defect_type}"
            else:
                logger.info(f"  [FUSION] Single defect rejected (shadow) → NORMAL")
                return 0, f"Rejected as shadow: {defect_type}"
    
    except Exception as e:
        logger.error(f"  [ERROR] {e}")
        return 0, f"Error: {e}"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        label, reason = classify_fusion(sys.argv[1])
        print(f"Result: {'ABNORMAL' if label == 1 else 'NORMAL'}")
        print(f"Reason: {reason}")
