"""
Integrated Manufacturing AI Agent
Baseline(Observe-Decide-Review)와 우리의 Judge-Think-Act-Verify 구조 통합
"""

import os
import re
import json
import time
import random
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
from dotenv import load_dotenv

# 프로젝트 모듈 임포트
from src.config import Config
from src.image_processor import ImageProcessor
from src.saltlux_client import SaltluxClient
from src.vision_analyzer import VisionAnalyzer
from src.reasoner import Reasoner
from src.decision_maker import DecisionMaker
from src.verifier import Verifier
from src.agent_core import ManufacturingAgent, AgentState
from src.utils import setup_logging, save_results_to_csv, print_agent_flow_chart

# 환경 설정
load_dotenv()
setup_logging(Config.LOGS_DIR)
logger = logging.getLogger(__name__)

# =========================
# 설정
# =========================
API_KEY = os.getenv('SALTLUX_API_KEY', 'YOUR_API_KEY')
BRIDGE_URL = os.getenv('SALTLUX_API_BASE_URL', 'https://bridge.luxiacloud.com/llm/openai/chat/completions/{model}/create')
MODEL_JUDGE = "luxia3-llm-32b-0731"  # 최신 Luxia 모델: 상세 이미지 분석
MODEL_THINK = "luxia3-llm-32b-0731"  # 최신 Luxia 모델: 깊이 있는 추론
MODEL_ACT = "luxia3-llm-13b-0731"    # 고성능 Luxia 모델: 빠른 판단
MODEL_VERIFY = "luxia3-llm-32b-0731" # 최신 Luxia 모델: 최종 검증

# 입력/출력 경로
# data.csv (dev.csv로 제공될 예정)
PROJECT_ROOT = Path(__file__).parent.parent
TEST_CSV_PATH = str(PROJECT_ROOT / "data.csv")  # 1일차 제공 파일
OUTPUT_PATH = str(Config.OUTPUT_DIR / "output.csv")

# API 호출 헤더
HEADERS = {"apikey": API_KEY, "Content-Type": "application/json"}

# 대회 라벨 정의
LABEL_NORMAL = 0
LABEL_ABNORMAL = 1

# =========================
# 관찰 항목 정의 (IC 부품 검사 기준 - 분류 판단 기준 기반)
# =========================
# "분류 판단 기준.md" 기반으로 정의된 6가지 불량 유형:
# 1. 유령형 (Missing): 부품 유실
# 2. 연결형 (Connectivity): 절단/미삽/합선 (가장 중요)
# 3. 파손형 (Broken): 몸체 깨짐 (심각한 경우만)
# 4. 곡예형 (Posture): 자세 불량 (누움/뒤집힘)
# 5. 회전형 (Alignment): 정렬 불량 (45도 이상 회전)
# 6. 정상: 흠집/파손 있어도 기능(연결)에 문제 없음

OBS_ITEMS = [
    ("component_missing", "👻 유령형: 부품 전체 유실"),
    ("lead_connectivity_fail", "🗡️ 연결형: 다리 절단/미삽/합선 (가장 중요)"),
    ("body_broken_severe", "💥 파손형: 몸체 깨짐 (내부 칩 노출)"),
    ("posture_bad", "🤸 곡예형: 누움/뒤집힘"),
    ("rotation_severe", "🌀 회전형: 45도 이상 회전"),
]

KEYS = [k for k, _ in OBS_ITEMS]

# 불량 유형별 심각도 (가중치)
DEFECT_SEVERITY = {
    "component_missing": 1.0,          # 가장 심각: 부품 없음
    "lead_connectivity_fail": 0.98,    # 극히 심각: 전기 연결 실패 (가장 중요)
    "body_broken_severe": 0.95,        # 매우 심각: 몸체 심각 파손
    "posture_bad": 0.85,               # 심각: 부품 누움/뒤집힘
    "rotation_severe": 0.80,           # 중대: 45도 이상 회전
}

# =========================
# 시스템 프롬프트
# =========================
SYSTEM = (
    "너는 제조공정 소자 검사 이미지 분석기다.\n"
    "반드시 요청한 JSON만 출력한다. 다른 텍스트는 절대 출력하지 않는다.\n"
)


# =========================
# Prompt Builder
# =========================
def build_prompt(strict: bool = False) -> str:
    """
    IC 부품 검사 프롬프트 (분류 판단 기준 기반)
    6가지 불량 유형 + 정상 판별
    
    Args:
        strict: True면 보수적 판단 (애매하면 불량으로)
        
    Returns:
        프롬프트 문자열
    """
    
    header = """
You are a HIGHLY ACCURATE TO-92 Transistor quality inspection expert. 

【COMPONENT SPECIFICATION】
- Component Type: **TO-92 Transistor** (3-pin plastic package)
- Expected Leads: **EXACTLY 3 leads** (Left, Center, Right)
- Background: **Stripboard (Orange/Copper PCB)**
  ⚠️ CRITICAL: Do NOT confuse copper traces on the stripboard with transistor leads!
  - Transistor leads: Vertical metal pins coming from the black plastic body
  - Stripboard traces: Horizontal copper lines on the orange board

🎯 PRIMARY GOAL: Identify DEFECTIVE components with MAXIMUM sensitivity.
⚠️  False Negatives (missing defects) are WORSE than False Positives!

【Critical: lead_connectivity_fail is MOST IMPORTANT】

【6-Category Classification】

1️⃣ component_missing: Transistor body completely absent (empty footprint only)

2️⃣ lead_connectivity_fail ⭐⭐⭐ HIGHEST PRIORITY ⭐⭐⭐
   ANY of these → TRUE:
   - Lead is CUT/SEVERED (shortened/jagged/incomplete end)
   - Lead is MISSING from PCB hole (not inserted/floating)
   - Lead is TOUCHING another lead (short circuit)
   - Lead spacing < 1mm (dangerously close)
   - WRONG NUMBER of leads (must be exactly 3)
   
   DETAILED INSPECTION FOR EACH LEAD (3 leads total: LEFT, CENTER, RIGHT):
   ■ Check 1: Can see lead clearly? (Don't confuse with copper traces!)
   ■ Check 2: Lead FULLY INSERTED in hole?
   ■ Check 3: Lead is INTACT? (not cut/broken/shortened)
   ■ Check 4: Lead spacing >= 1mm? (not touching)
   ■ Check 5: Lead in correct position?
   
   ✗ FALSE: ALL 3 leads PASS all 5 checks
   ✓ TRUE: ANY lead FAILS any check OR lead count ≠ 3

3️⃣ body_broken_severe: Internal structure VISIBLY exposed
   ✗ FALSE: Surface damage, scratches, dents (no internal exposure)
   ✓ TRUE: Internal chip/circuitry/structure clearly visible

4️⃣ posture_bad: Component lying down or upside down

5️⃣ rotation_severe: >= 45 degree rotation

【KEY DECISION RULE】
If uncertain about lead_connectivity_fail → Mark as TRUE (Better to be cautious in manufacturing!)
Missing a defect is worse than marking something as defective!
"""
    
    json_template = """
Output ONLY this JSON (NO other text):
{
  "component_missing": false,
  "lead_connectivity_fail": false,
  "body_broken_severe": false,
  "posture_bad": false,
  "rotation_severe": false
}
"""

    if strict:
        rule = """
【VERIFICATION MODE - 정밀 재검토 (Precision & Recall Balance)】
⚠️  GOAL: Distinguish REAL DEFECTS from Shadows/Artifacts.

1️⃣ SHADOW/NOISE (Mark as NORMAL)
    - Dark/Black area ALONG the lead path? -> Shadow (Normal)
    - Lead looks faint/blurry but continuous? -> Focus issue (Normal)
    - Surface scratches on body? -> Normal

2️⃣ REAL DEFECTS (Mark as ABNORMAL)
    - Lead ENDS abruptly (Cut/Broken)? -> ABNORMAL (True)
    - A visible GAP where metal should be? -> ABNORMAL (True)
    - Lead is FLOATING (not inserted in hole)? -> ABNORMAL (True)
    - Lead is BENT and touching neighbor? -> ABNORMAL (True)

⚠️  Decision Guide:
    - If lead path is continuous but dark -> CONNECTED (Normal).
    - If lead path is BROKEN/INTERRUPTED -> DISCONNECTED (Abnormal).
    - If unsure, look for the "cut end". If no cut end visible -> Assume Shadow (Normal).
"""
    else:
        rule = """
【STANDARD MODE - 체계적 검사 (Systematic Inspection)】

🔍 Step-by-Step Lead Inspection:
For EACH of 3 leads (LEFT, CENTER, RIGHT):
✓ VISUAL GAP CHECK: Is there a clear whitespace gap in the lead?
   - NO (Dark/Shadowed/Faint) -> Connected (Pass)
   - YES (Bright Gap) -> Broken (Fail)

✓ Lead spacing >= 1mm? (no short)
→ IF any failure: lead_connectivity_fail = TRUE

🔍 Body Assessment (Be Lenient):
→ Internal structure exposed? (chip visible) = TRUE
→ Surface scratches, edge chips, discoloration? = FALSE (Ignore these!)

【Decision Rules】
1. Be careful of SHADOWS. Dark leads are usually connected.
2. Only flag lead_connectivity_fail if a BREACH is visible.
3. Ignore minor surface aesthetics.
"""

    return header + "\n" + json_template + rule



PROMPT_NORMAL = build_prompt(strict=False)
PROMPT_STRICT = build_prompt(strict=True)


# =========================
# LLM API 호출
# =========================
def _post_chat(messages, timeout=90) -> str:
    """
    Saltlux LLM API 호출 (Baseline과 동일)
    
    Args:
        messages: OpenAI ChatCompletions 형식의 메시지
        timeout: 요청 타임아웃 (초)
        
    Returns:
        LLM 응답 텍스트
    """
    import requests
    
    payload = {"model": MODEL_JUDGE, "messages": messages, "stream": False}
    r = requests.post(BRIDGE_URL, headers=HEADERS, json=payload, timeout=timeout)
    
    if r.status_code != 200:
        raise RuntimeError(f"API Error: status={r.status_code}, body={r.text[:300]}")
    
    return r.json()["choices"][0]["message"]["content"].strip()


def _safe_json_extract(s: str) -> dict:
    """
    LLM 응답에서 JSON 안전하게 추출
    
    Args:
        s: LLM 응답 텍스트
        
    Returns:
        파싱된 JSON 딕셔너리
    """
    try:
        return json.loads(s)
    except Exception:
        m = re.search(r"\{.*\}", s, flags=re.S)
        if m:
            return json.loads(m.group(0))
    raise ValueError(f"JSON parse failed: {s[:200]}")


import cv2
import numpy as np

def _preprocess_image_bytes(image_path: str) -> bytes:
    """
    이미지 전처리 (CLAHE 적용) 및 바이트 변환
    
    Args:
        image_path: 이미지 파일 경로
        
    Returns:
        전처리된 이미지의 바이트 데이터 (PNG 형식)
    """
    try:
        # 1. 이미지 로드 (한글 경로 지원을 위해 numpy 사용)
        img_array = np.fromfile(image_path, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")
            
        # 2. CLAHE (Contrast Limited Adaptive Histogram Equalization) 적용
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        lab = cv2.merge((l, a, b))
        final = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # 3. 바이트로 인코딩
        success, encoded_img = cv2.imencode('.png', final)
        if not success:
            raise ValueError("Failed to encode processed image")
            
        return encoded_img.tobytes()
        
    except Exception as e:
        logger.warning(f"Preprocessing failed ({e}), falling back to raw image.")
        with open(image_path, 'rb') as f:
            return f.read()


# =========================
# Agent Steps (Judge-Think-Act-Verify 통합)
# =========================

def observe(img_url: str, strict: bool = False) -> Dict[str, bool]:
    """
    JUDGE Step: Observe (관찰 단계)
    
    Baseline의 observe 함수와 동일하지만,
    우리의 Judge 단계로 통합됩니다.
    
    Args:
        img_url: 이미지 URL 또는 로컬 파일 경로
        strict: 보수적 모드
        
    Returns:
        {항목명: true/false} 딕셔너리
    """
    import base64
    import os
    
    logger.info(f"  [OBSERVE] Analyzing image (strict={strict})")
    
    prompt = PROMPT_STRICT if strict else PROMPT_NORMAL
    
    try:
        # 로컬 파일 경로 처리
        if os.path.exists(img_url):
            # ⭐ [Note] CLAHE preprocessing increased False Positives (noise amplification).
            # Reverting to raw image for best performance (71% accuracy).
            # img_bytes = _preprocess_image_bytes(img_url)
            
            with open(img_url, 'rb') as f:
                img_bytes = f.read()
                
            img_data = base64.b64encode(img_bytes).decode('utf-8')
            
            # 파일 확장자에 따른 MIME 타입 결정
            # (opencv 엔코딩은 기본 png지만, 원본 확장자 로직 유지해도 무방)
            if img_url.lower().endswith('.png'):
                media_type = "image/png"
            elif img_url.lower().endswith('.jpg') or img_url.lower().endswith('.jpeg'):
                media_type = "image/jpeg"
            else:
                media_type = "image/png"  # 기본값
            
            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{media_type};base64,{img_data}"
                }
            }
        else:
            # URL로 처리
            image_content = {
                "type": "image_url",
                "image_url": {"url": img_url}
            }
        
        content = _post_chat([
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                image_content,
            ]},
        ])
        
        obs = _safe_json_extract(content)
        
        # 키 누락 대비
        return {k: bool(obs.get(k, False)) for k in KEYS}
        
    except Exception as e:
        logger.error(f"  [OBSERVE] Failed: {e}")
        return {k: False for k in KEYS}


def think(obs: Dict[str, bool]) -> Dict[str, Any]:
    """
    THINK Step: 분석 (분류 판단 기준 기반)
    
    관찰 결과를 분석하여 최종 판정을 준비합니다.
    분류 판단 기준의 6가지 불량 유형 기반:
    1. component_missing: 부품 유실
    2. lead_connectivity_fail: 다리 절단/미삽/합선 (⭐ 가장 중요)
    3. body_broken_severe: 몸체 심각 파손
    4. posture_bad: 누움/뒤집힘
    5. rotation_severe: 45도 이상 회전
    6. 정상: 기능 이상 없으면 정상
    
    Args:
        obs: 관찰 결과
        
    Returns:
        분석 결과
    """
    logger.info("  [THINK] 분석 중...")
    
    defect_count = sum(1 for v in obs.values() if v)
    defects = [k for k, v in obs.items() if v]
    
    # 도메인 기반 심각도 점수 계산
    severity_score = sum(DEFECT_SEVERITY.get(d, 0.5) for d in defects)
    
    # ⭐ 연결형 결함 체크 (가장 중요)
    has_connectivity_fail = obs.get('lead_connectivity_fail', False)
    
    # 기타 심각한 결함 체크
    has_critical = has_connectivity_fail or obs.get('component_missing', False)
    
    reasoning = {
        'total_defects': defect_count,
        'defect_items': defects,
        'severity_score': severity_score,
        'has_critical_defect': has_critical,
        'has_connectivity_fail': has_connectivity_fail,
        'observation_result': obs,
        'confidence_level': _estimate_confidence(defect_count, obs, has_critical)
    }
    
    logger.debug(f"  [THINK] 감지된 결함: {defect_count}개 - {defects}")
    logger.debug(f"  [THINK] 심각도 점수: {severity_score:.2f}, 치명적: {has_critical}")
    
    return reasoning



def _estimate_confidence(defect_count: int, obs: Dict[str, bool], has_critical: bool = False) -> str:
    """
    결함 개수 및 심각도에 따른 신뢰도 추정 (도메인 기반)
    
    반도체 제조 원칙:
    - 치명적 결함(패키지, 리드): 1개만 있어도 불량 확정
    - 다중 결함: 매우 높은 신뢰도
    - 단순 결함: 중간 신뢰도
    - 결함 없음: 보수적 신뢰도 (놓친 게 있을 수 있음)
    
    Args:
        defect_count: 결함 개수
        obs: 관찰 결과
        has_critical: 치명적 결함 포함 여부
        
    Returns:
        신뢰도 레벨 ('VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW')
    """
    if has_critical:
        return 'VERY_HIGH'  # 치명적 결함 = 확정 불량
    elif defect_count >= 2:
        return 'HIGH'  # 여러 결함이 감지되면 신뢰도 높음
    elif defect_count == 1:
        return 'MEDIUM'  # 단일 결함은 중간 신뢰도
    else:
        return 'LOW'  # 결함 없으면 신뢰도 낮음 (놓친 것이 있을 수 있음)


def act(reasoning: Dict[str, Any]) -> Tuple[int, bool]:
    """
    ACT Step: 의사결정 (Updated for Reduced FP)
    
    Args:
        reasoning: Think 단계의 결과
        
    Returns:
        (label, uncertain) 튜플
    """
    logger.info("  [ACT] 의사결정 중...")
    
    defect_count = reasoning['total_defects']
    obs = reasoning['observation_result']
    
    # ⭐ 1. 다중 결함: 불량 확률 높음 -> 즉시 불량 확정
    if defect_count >= 2:
        logger.info(f"    -> Multiple defects ({defect_count}): abnormal confirmed")
        return LABEL_ABNORMAL, False
    
    # ⭐ 2. 단일 결함: 연결형이라도 '불확실'로 판단하여 재검증 유도 (FP 방지)
    # 기존에는 연결형이면 바로 불량이었으나, 그림자 오인식이 많아 재검증 필수로 변경
    if defect_count == 1:
        if obs.get('lead_connectivity_fail', False):
             logger.info("    -> Single connectivity fail detected. Checking for shadows... (UNCERTAIN)")
             return LABEL_ABNORMAL, True # Trigger Verify (Double Check)
        else:
             logger.info("    -> Single non-critical defect: UNCERTAIN (trigger verify)")
             return LABEL_ABNORMAL, True
    
    # 3. 결함 없음
    logger.info("    -> No defects: normal")
    return LABEL_NORMAL, False


def verify(label: int, reasoning: Dict[str, Any], 
          is_review: bool = False) -> Dict[str, Any]:
    """
    VERIFY Step: 최종 검증 (분류 판단 기준 기반)
    
    의사결정을 검증하고 신뢰도를 결정합니다.
    
    신뢰도 기준:
    - 연결형 결함 감지: 98% (가장 확실)
    - 유령형/파손형 감지: 95%
    - 기타 결함: 85%
    - 결함 없음: 90% (정상은 높은 신뢰도)
    
    Args:
        label: 의사결정 결과 (0 or 1)
        reasoning: 분석 결과
        is_review: 재검토된 결과인지 여부
        
    Returns:
        검증 결과
    """
    logger.info(f"  [VERIFY] 최종 검증 (재검토={is_review})")
    
    obs = reasoning.get('observation_result', {})
    has_connectivity_fail = obs.get('lead_connectivity_fail', False)
    
    # 신뢰도 결정
    if label == LABEL_ABNORMAL:
        if has_connectivity_fail:
            confidence = 0.98  # 연결형 결함: 가장 확실
            detail = "🗡️ 연결형 결함 명확"
        else:
            confidence = 0.90  # 기타 불량
            detail = "결함 감지"
    else:
        confidence = 0.90  # 정상도 높은 신뢰도
        detail = "결함 없음"
    
    verdict = "NORMAL" if label == LABEL_NORMAL else "ABNORMAL"
    
    return {
        'verdict': verdict,
        'decision_label': label,
        'confidence': confidence,
        'detail': detail,
        'is_verified': True
    }


# =========================
# Integrated Agent (Observe-Decide-Review + Judge-Think-Act-Verify)
# =========================

def classify_agent_integrated(img_url: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    통합 AI Agent (분류 판단 기준 기반)
    
    Baseline의 Observe-Decide-Review 패턴을 우리의
    Judge-Think-Act-Verify 구조로 구현합니다.
    
    분류 기준:
    1. 연결형 결함(lead_connectivity_fail) 감지 → 즉시 불량 확정 ⭐ 가장 중요!
    2. 기타 결함 발견 → 불량 판정
    3. 결함 없음 → 정상 판정
    
    Flow:
    1. JUDGE(Observe): 1차 관찰
    2. THINK(Analyze): 결과 분석 (심각도 포함)
    3. ACT(Decide): 초기 판단
    4. VERIFY(Review): 검증 및 필요시 재검토
    
    Args:
        img_url: 이미지 URL
        max_retries: 최대 재시도 횟수
        
    Returns:
        최종 판단 결과
    """
    logger.info("=" * 60)
    logger.info(f"Agent Processing: {img_url[-20:]}")
    logger.info("=" * 60)
    
    for attempt in range(max_retries):
        try:
            # ========== Step 1: JUDGE (1차 관찰) ==========
            obs1 = observe(img_url, strict=False)
            
            # ========== Step 2: THINK (분석 + 도메인 가중치) ==========
            reasoning1 = think(obs1)
            print(f"   [Step 1] Defects: {reasoning1['defect_items']}")
            
            # ========== Step 3: ACT (판단) ==========
            label1, uncertain = act(reasoning1)
            
            # 도메인 원칙: 치명적 결함 발견 시 즉시 확정
            if reasoning1.get('has_critical_defect', False):
                verification = verify(label1, reasoning1, is_review=False)
                logger.info(f"Final Decision: {verification['decision_label']} "
                           f"(confidence: {verification['confidence']:.2f}, CRITICAL DEFECT)")
                logger.info("=" * 60 + "\n")
                
                return {
                    'prediction': label1,
                    'confidence': verification['confidence'],
                    'verified': True,
                    'iterations': 1,
                    'reason': 'Critical defect detected'
                }
            
            # 애매하지 않으면 바로 종료
            if not uncertain:
                verification = verify(label1, reasoning1, is_review=False)
                logger.info(f"Final Decision: {verification['decision_label']} "
                           f"(confidence: {verification['confidence']:.2f})")
                logger.info("=" * 60 + "\n")
                
                return {
                    'prediction': label1,
                    'confidence': verification['confidence'],
                    'verified': True,
                    'iterations': 1
                }
            
            # ========== 재검토 (REVIEW) ==========
            logger.info("  [REVIEW] Decision uncertain, performing strict re-analysis...")
            
            obs2 = observe(img_url, strict=True)
            reasoning2 = think(obs2)
            print(f"   [Step 2 Verify] Defects: {reasoning2['defect_items']}")
            label2, _ = act(reasoning2)
            
            # 도메인 원칙: 재검토에서도 치명적 결함 발견 시 확정
            if reasoning2.get('has_critical_defect', False):
                verification = verify(label2, reasoning2, is_review=True)
                logger.info(f"Final Decision: {verification['decision_label']} "
                           f"(confidence: {verification['confidence']:.2f}, CRITICAL AFTER REVIEW)")
                logger.info("=" * 60 + "\n")
                
                return {
                    'prediction': label2,
                    'confidence': verification['confidence'],
                    'verified': True,
                    'iterations': 2,
                    'reason': 'Critical defect confirmed in review'
                }
            
            # 재검토에서 결함이 잡히면 비정상 확정
            if label2 == LABEL_ABNORMAL:
                # ⚖️ TIE-BREAKER: Single defects are suspicious. Check ONE MORE TIME.
                # If it persists 3 times (Judge -> Verify -> TieBreaker), it's real.
                if reasoning2['total_defects'] == 1:
                    logger.info("  [TIE-BREAKER] Single defect detected. Running 3rd check for consistency...")
                    
                    obs3 = observe(img_url, strict=True) # Use strict mode again
                    reasoning3 = think(obs3)
                    print(f"   [Step 3 TieBreaker] Defects: {reasoning3['defect_items']}")
                    label3, _ = act(reasoning3)
                    
                    if label3 == LABEL_ABNORMAL:
                         verification = verify(label3, reasoning3, is_review=True)
                         logger.info(f"Final Decision: {verification['decision_label']} "
                                    f"(confidence: {verification['confidence']:.2f}, CONFIRMED BY TIE-BREAKER)")
                         logger.info("=" * 60 + "\n")
                         return {
                            'prediction': label3,
                            'confidence': verification['confidence'],
                            'verified': True,
                            'iterations': 3,
                            'reason': 'Confirmed by Tie-Breaker'
                         }
                    else:
                         verification = verify(LABEL_NORMAL, reasoning3, is_review=True)
                         logger.info(f"Final Decision: {verification['decision_label']} "
                                    f"(confidence: {verification['confidence']:.2f}, CLEARED BY TIE-BREAKER)")
                         logger.info("=" * 60 + "\n")
                         return {
                            'prediction': LABEL_NORMAL,
                            'confidence': verification['confidence'],
                            'verified': True,
                            'iterations': 3,
                            'reason': 'Cleared by Tie-Breaker'
                         }

                # Multiple defects in Verify -> Confirmed immediately
                verification = verify(label2, reasoning2, is_review=True)
                logger.info(f"Final Decision: {verification['decision_label']} "
                           f"(confidence: {verification['confidence']:.2f}, CONFIRMED ABNORMAL)")
                logger.info("=" * 60 + "\n")
                
                return {
                    'prediction': label2,
                    'confidence': verification['confidence'],
                    'verified': True,
                    'iterations': 2
                }
            
            # ⭐ 재검토에서 결함이 없으면 '정상'으로 판정 뒤집기 (False Positive 방지핵심)
            verification = verify(LABEL_NORMAL, reasoning2, is_review=True)
            logger.info(f"Final Decision: {verification['decision_label']} "
                       f"(confidence: {verification['confidence']:.2f}, FLIPPED TO NORMAL)")
            logger.info("=" * 60 + "\n")
            
            return {
                'prediction': LABEL_NORMAL,
                'confidence': verification['confidence'],
                'verified': True,
                'iterations': 2,
                'reason': 'Cleared by verification'
            }
            
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Final attempt failed: {e}")
                raise
            
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            wait_time = (0.5 * (2 ** attempt)) + random.uniform(0, 0.2)
            logger.info(f"  Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)


# =========================
# Main Pipeline
# =========================

def process_images_from_csv(csv_path: str, output_path: str) -> pd.DataFrame:
    """
    CSV 파일의 이미지 목록을 처리하고 결과 저장
    
    도메인 지식 기반 처리:
    - 치명적 결함 조기 감지로 비용 절감
    - 재검토 전략으로 정확도 향상
    - 심각도 기반 우선순위 판단
    
    Args:
        csv_path: 입력 CSV 파일 경로
        output_path: 출력 CSV 파일 경로
        
    Returns:
        결과 DataFrame
    """
    logger.info(f"Loading images from: {csv_path}")
    
    # CSV 로드
    test_df = pd.read_csv(csv_path)
    
    if "id" not in test_df.columns or "img_url" not in test_df.columns:
        raise ValueError(f"Required columns: id, img_url. Got: {test_df.columns.tolist()}")
    
    logger.info(f"Loaded {len(test_df)} images")
    
    preds = []
    n = len(test_df)
    
    for i, row in test_df.iterrows():
        _id = row["id"]
        img_url = row["img_url"]
        
        try:
            result = classify_agent_integrated(img_url)
            label = result['prediction']
            
            print(f"[{i+1}/{n}] id={_id} -> {label}")
            
        except Exception as e:
            logger.error(f"[{i+1}/{n}] id={_id} ERROR: {e}")
            print(f"[{i+1}/{n}] id={_id} ERROR -> fallback 0 | {e}")
            label = LABEL_NORMAL
        
        preds.append({"id": _id, "label": label})
        
        # API 호출 간격 (속도 조절)
        time.sleep(0.2)
    
    # 결과 DataFrame 생성
    out_df = pd.DataFrame(preds, columns=["id", "label"])
    
    # CSV로 저장 (UTF-8)
    out_df.to_csv(output_path, index=False, encoding='utf-8')
    
    logger.info(f"Saved results to: {output_path}")
    print(f"\n Saved: {output_path}")
    print(out_df.head())
    
    return out_df


# =========================
# Entry Point
# =========================

def main():
    """메인 실행 함수"""
    print_agent_flow_chart()
    
    logger.info("Manufacturing AI Agent - Starting")
    logger.info(f"   API Key: {API_KEY[:20]}...")
    logger.info(f"   Model: {MODEL}")
    logger.info(f"   Input: {TEST_CSV_PATH}")
    logger.info(f"   Output: {OUTPUT_PATH}")
    logger.info(f"   Domain: Semiconductor Manufacturing Quality Control")
    logger.info(f"   Architecture: Observe-Decide-Review + Judge-Think-Act-Verify")
    
    # 입력 파일 확인
    if not Path(TEST_CSV_PATH).exists():
        logger.error(f"Input file not found: {TEST_CSV_PATH}")
        raise FileNotFoundError(TEST_CSV_PATH)
    
    # 처리 시작
    results_df = process_images_from_csv(TEST_CSV_PATH, OUTPUT_PATH)
    
    # 통계
    normal_count = (results_df['label'] == 0).sum()
    abnormal_count = (results_df['label'] == 1).sum()
    
    logger.info(f"\n Summary:")
    logger.info(f"   Total: {len(results_df)}")
    logger.info(f"   Normal: {normal_count}")
    logger.info(f"   Abnormal: {abnormal_count}")
    logger.info(f"   Abnormal Rate: {abnormal_count/len(results_df)*100:.1f}%")
    
    print(f"\n Summary:")
    print(f"   Total: {len(results_df)}")
    print(f"   Normal: {normal_count}")
    print(f"   Abnormal: {abnormal_count}")
    print(f"   Abnormal Rate: {abnormal_count/len(results_df)*100:.1f}%")


if __name__ == "__main__":
    main()
