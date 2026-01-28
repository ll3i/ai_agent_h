"""
Multi-Model Manufacturing AI Agent
다중 모델 기반 강화된 제조공정 AI Agent

아키텍처:
- JUDGE: gpt-4o-mini (빠른 비전 분석)
- THINK: claude-3.5-sonnet (깊이 있는 추론)
- ACT: gpt-3.5-turbo (빠른 의사결정)
- VERIFY: gpt-4o (강력한 최종 검증)
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
from src.utils import setup_logging, save_results_to_csv, print_agent_flow_chart

# 환경 설정
load_dotenv()
setup_logging(Config.LOGS_DIR)
logger = logging.getLogger(__name__)

# =========================
# 다중 모델 설정
# =========================
API_KEY = os.getenv('SALTLUX_API_KEY', 'YOUR_API_KEY')
BRIDGE_URL = os.getenv('SALTLUX_API_BASE_URL', 'https://bridge.luxiacloud.com/llm/openai/chat/completions/{model}/create')

# 각 Agent별 모델 설정
MODELS = Config.LUXIA_MODELS
MODEL_PROFILES = Config.MODEL_PROFILES

# 입력/출력 경로
PROJECT_ROOT = Path(__file__).parent.parent
TEST_CSV_PATH = str(PROJECT_ROOT / "data.csv")
OUTPUT_PATH = str(Config.OUTPUT_DIR / "output.csv")

# API 호출 헤더
HEADERS = {"apikey": API_KEY, "Content-Type": "application/json"}

# 대회 라벨 정의
LABEL_NORMAL = 0
LABEL_ABNORMAL = 1

# =========================
# 관찰 항목 정의 (도메인 지식)
# =========================
OBS_ITEMS = [
    ("package_damage", "크랙/파손/깨짐 등 패키지 손상 (치명적 결함)"),
    ("lead_missing_or_broken", "리드 결손/단선 (신뢰성 저하)"),
    ("lead_severe_bend_or_contact", "심한 휨 또는 리드끼리 접촉 (단락 위험)"),
    ("solder_bridge_or_blob", "솔더 브리지 또는 납땜 뭉침 (전기적 결함)"),
    ("misalignment_severe", "소자 위치가 과도하게 틀어짐 (조립 오류)"),
]

KEYS = [k for k, _ in OBS_ITEMS]

# 도메인 기반 결함 가중치
DEFECT_SEVERITY = {
    "package_damage": 1.0,
    "lead_missing_or_broken": 0.95,
    "lead_severe_bend_or_contact": 0.90,
    "solder_bridge_or_blob": 0.85,
    "misalignment_severe": 0.80,
}

# =========================
# API 호출 함수 (모델별)
# =========================
def _post_chat_with_model(model: str, messages, timeout=90) -> str:
    """
    특정 모델로 API 호출
    
    Args:
        model: 모델명 (gpt-4o, claude-3.5-sonnet 등)
        messages: 메시지 리스트
        timeout: 타임아웃
        
    Returns:
        LLM 응답 텍스트
    """
    import requests
    
    url = BRIDGE_URL.replace('{model}', model)
    payload = {"model": model, "messages": messages, "stream": False}
    
    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=timeout)
        
        if r.status_code != 200:
            raise RuntimeError(f"API Error ({model}): status={r.status_code}")
        
        response = r.json()
        return response["choices"][0]["message"]["content"].strip()
        
    except Exception as e:
        logger.error(f"API call failed for model {model}: {e}")
        raise


def _safe_json_extract(s: str) -> dict:
    """JSON 안전하게 추출"""
    try:
        return json.loads(s)
    except Exception:
        m = re.search(r"\{.*\}", s, flags=re.S)
        if m:
            return json.loads(m.group(0))
    raise ValueError(f"JSON parse failed")


# =========================
# Prompt Builders (모델별 최적화)
# =========================
def build_judge_prompt(strict: bool = False) -> str:
    """JUDGE(관찰) - gpt-4o-mini 최적화 프롬프트"""
    header = (
        "JSON만 출력해. 이미지에서 다음 항목을 관찰하고 true/false로 채워.\n"
        "형식은 정확하게:\n"
    )
    json_template = "{\n" + ",\n".join([f'  "{k}": false' for k, _ in OBS_ITEMS]) + "\n}"
    
    criteria = "\n".join([f"- {k}: {desc}" for k, desc in OBS_ITEMS])
    
    advanced_tips = (
        "\n\n[도메인 지식 - 반도체 제조]\n"
        "1. 패키지 손상: 미세 크랙도 응력 집중점\n"
        "2. 리드 접촉: 쇼트 위험 직결\n"
        "3. 솔더 브리지: 전기적 단락\n"
    )
    
    return header + json_template + "\n\n기준:\n" + criteria + advanced_tips


def build_think_prompt(obs: Dict[str, bool], img_context: str = "") -> str:
    """THINK(추론) - claude 최적화 프롬프트"""
    defect_count = sum(1 for v in obs.values() if v)
    defects = [k for k, v in obs.items() if v]
    
    return f"""
    관찰 결과를 깊이 있게 분석하세요.
    
    [관찰 결과]
    - 결함 개수: {defect_count}
    - 감지된 결함: {', '.join(defects) if defects else '없음'}
    
    [분석 요구사항]
    1. 각 결함의 심각도 평가 (1-10)
    2. 제조 공정상 원인 분석
    3. 신뢰성 영향도 평가
    4. 최종 분류 추천: Normal(0) 또는 Abnormal(1)
    
    JSON 형식으로 답변:
    {{
        "severity_analysis": {{"결함명": 점수}},
        "root_cause": "원인 분석",
        "reliability_impact": "영향도",
        "recommendation": 0 또는 1,
        "confidence": 0.0-1.0
    }}
    """


def build_act_prompt(reasoning: Dict[str, Any]) -> str:
    """ACT(의사결정) - gpt-3.5-turbo 최적화 프롬프트"""
    return f"""
    빠른 의사결정을 내리세요. JSON만 출력.
    
    분석 결과: {json.dumps(reasoning, ensure_ascii=False)}
    
    규칙:
    - 치명적 결함(패키지, 리드) → 무조건 1(Abnormal)
    - 2개 이상 결함 → 1(Abnormal)
    - 1개 이상 결함 → 1(Abnormal)
    - 결함 없음 → 0(Normal)
    
    응답:
    {{"decision": 0 또는 1, "confidence": 0.0-1.0}}
    """


def build_verify_prompt(label: int, reasoning: Dict[str, Any], img_context: str = "") -> str:
    """VERIFY(검증) - gpt-4o 최적화 프롬프트"""
    return f"""
    최종 검증을 수행하세요. 신뢰도를 높이기 위해 깊이 있게 검토.
    
    [현재 판단]
    - 레이블: {label} ({'Normal' if label == 0 else 'Abnormal'})
    - 근거: {json.dumps(reasoning, ensure_ascii=False, indent=2)}
    
    [검증 체크리스트]
    1. 판단의 논리적 타당성 확인
    2. 도메인 지식과의 일치도 검증
    3. 놓친 결함이 있을 가능성 평가
    4. 신뢰도 점수 재계산
    
    응답:
    {{
        "verified": true/false,
        "final_label": 0 또는 1,
        "confidence": 0.0-1.0,
        "reasoning": "최종 판단 근거"
    }}
    """


# =========================
# Multi-Model Agent Steps
# =========================

def judge_step(img_url: str, strict: bool = False) -> Dict[str, bool]:
    """
    JUDGE Step - 관찰 (gpt-4o-mini)
    빠른 비전 분석으로 초기 결함 감지
    """
    logger.info(f"  [JUDGE] Using model: {MODELS['judge']}")
    
    prompt = build_judge_prompt(strict)
    
    try:
        content = _post_chat_with_model(
            MODELS['judge'],
            [
                {"role": "system", "content": "너는 반도체 품질 검사 전문가다. JSON만 출력."},
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": img_url}},
                ]},
            ]
        )
        
        obs = _safe_json_extract(content)
        return {k: bool(obs.get(k, False)) for k in KEYS}
        
    except Exception as e:
        logger.error(f"  [JUDGE] Failed: {e}")
        return {k: False for k in KEYS}


def think_step(obs: Dict[str, bool]) -> Dict[str, Any]:
    """
    THINK Step - 깊이 있는 추론 (claude-3.5-sonnet)
    관찰 결과를 전문가 수준으로 분석
    """
    logger.info(f"  [THINK] Using model: {MODELS['think']}")
    
    defect_count = sum(1 for v in obs.values() if v)
    defects = [k for k, v in obs.items() if v]
    severity_score = sum(DEFECT_SEVERITY.get(d, 0.5) for d in defects)
    critical_defects = {'package_damage', 'lead_missing_or_broken', 'lead_severe_bend_or_contact'}
    has_critical = bool(set(defects) & critical_defects)
    
    prompt = build_think_prompt(obs)
    
    try:
        content = _post_chat_with_model(
            MODELS['think'],
            [{"role": "user", "content": prompt}]
        )
        
        analysis = _safe_json_extract(content)
        
    except Exception as e:
        logger.warning(f"  [THINK] Analysis failed: {e}")
        analysis = {}
    
    reasoning = {
        'total_defects': defect_count,
        'defect_items': defects,
        'severity_score': severity_score,
        'has_critical_defect': has_critical,
        'observation_result': obs,
        'analysis': analysis,
        'confidence_level': _estimate_confidence(defect_count, has_critical)
    }
    
    logger.debug(f"  [THINK] Severity: {severity_score:.2f}, Critical: {has_critical}")
    return reasoning


def act_step(reasoning: Dict[str, Any]) -> Tuple[int, bool]:
    """
    ACT Step - 빠른 의사결정 (gpt-3.5-turbo)
    규칙 기반 빠른 판단
    """
    logger.info(f"  [ACT] Using model: {MODELS['act']}")
    
    prompt = build_act_prompt(reasoning)
    
    try:
        content = _post_chat_with_model(MODELS['act'], [{"role": "user", "content": prompt}])
        decision = _safe_json_extract(content)
        label = decision.get('decision', 0)
        
    except Exception as e:
        logger.warning(f"  [ACT] Decision failed: {e}")
        label = LABEL_ABNORMAL if reasoning['total_defects'] >= 1 else LABEL_NORMAL
    
    uncertain = (reasoning['total_defects'] == 0) or (reasoning['total_defects'] == 1)
    
    logger.debug(f"  [ACT] Decision: {label}, Uncertain: {uncertain}")
    return label, uncertain


def verify_step(label: int, reasoning: Dict[str, Any], is_review: bool = False) -> Dict[str, Any]:
    """
    VERIFY Step - 최종 검증 (gpt-4o)
    강력한 최종 확인으로 신뢰도 극대화
    """
    logger.info(f"  [VERIFY] Using model: {MODELS['verify']}")
    
    prompt = build_verify_prompt(label, reasoning)
    
    try:
        content = _post_chat_with_model(MODELS['verify'], [{"role": "user", "content": prompt}])
        verification = _safe_json_extract(content)
        
    except Exception as e:
        logger.warning(f"  [VERIFY] Verification failed: {e}")
        verification = {}
    
    # 신뢰도 맵
    confidence_map = {
        'VERY_HIGH': 0.99,
        'HIGH': 0.95,
        'MEDIUM': 0.70,
        'LOW': 0.60
    }
    
    base_confidence = verification.get('confidence', confidence_map.get(reasoning.get('confidence_level', 'LOW'), 0.50))
    
    if is_review and label == LABEL_ABNORMAL:
        final_confidence = min(base_confidence + 0.05, 0.99)
    else:
        final_confidence = base_confidence
    
    result = {
        'verified': True,
        'decision': label,
        'decision_label': 'Normal' if label == 0 else 'Abnormal',
        'confidence': final_confidence,
        'verification_detail': verification,
        'reasoning': reasoning
    }
    
    logger.debug(f"  [VERIFY] Final Confidence: {final_confidence:.2f}")
    return result


def _estimate_confidence(defect_count: int, has_critical: bool = False) -> str:
    """신뢰도 추정"""
    if has_critical:
        return 'VERY_HIGH'
    elif defect_count >= 2:
        return 'HIGH'
    elif defect_count == 1:
        return 'MEDIUM'
    else:
        return 'LOW'


# =========================
# Integrated Multi-Model Agent
# =========================

def classify_multi_model_agent(img_url: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    다중 모델 통합 Agent
    
    각 단계마다 최적화된 모델 사용:
    1. JUDGE (gpt-4o-mini): 빠른 비전 분석
    2. THINK (claude): 깊이 있는 추론
    3. ACT (gpt-3.5-turbo): 빠른 의사결정
    4. VERIFY (gpt-4o): 강력한 최종 검증
    """
    logger.info("=" * 60)
    logger.info(f"Multi-Model Agent: {img_url[-20:]}")
    logger.info("=" * 60)
    
    for attempt in range(max_retries):
        try:
            # Step 1: JUDGE
            obs1 = judge_step(img_url, strict=False)
            
            # Step 2: THINK
            reasoning1 = think_step(obs1)
            
            # Step 3: ACT
            label1, uncertain = act_step(reasoning1)
            
            # 치명적 결함이거나 확실하면 바로 검증
            if reasoning1.get('has_critical_defect', False) or not uncertain:
                verification = verify_step(label1, reasoning1, is_review=False)
                
                logger.info(f"Final Decision: {verification['decision_label']} "
                           f"(confidence: {verification['confidence']:.2f})")
                logger.info("=" * 60 + "\n")
                
                return {
                    'prediction': label1,
                    'confidence': verification['confidence'],
                    'verified': True,
                    'iterations': 1,
                    'models_used': list(MODELS.values())
                }
            
            # 재검토 필요
            logger.info("  [REVIEW] Uncertain decision, performing strict re-analysis...")
            
            obs2 = judge_step(img_url, strict=True)
            reasoning2 = think_step(obs2)
            label2, _ = act_step(reasoning2)
            
            # 재검토 결과 확인
            if reasoning2.get('has_critical_defect', False) or label2 == LABEL_ABNORMAL:
                verification = verify_step(label2, reasoning2, is_review=True)
                
                logger.info(f"Final Decision: {verification['decision_label']} "
                           f"(confidence: {verification['confidence']:.2f})")
                logger.info("=" * 60 + "\n")
                
                return {
                    'prediction': label2,
                    'confidence': verification['confidence'],
                    'verified': True,
                    'iterations': 2,
                    'models_used': list(MODELS.values())
                }
            
            # 1차 결과 유지
            verification = verify_step(label1, reasoning1, is_review=True)
            
            logger.info(f"Final Decision: {verification['decision_label']} "
                       f"(confidence: {verification['confidence']:.2f})")
            logger.info("=" * 60 + "\n")
            
            return {
                'prediction': label1,
                'confidence': verification['confidence'],
                'verified': True,
                'iterations': 2,
                'models_used': list(MODELS.values())
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

def process_images_with_multi_model(csv_path: str, output_path: str) -> pd.DataFrame:
    """
    CSV 파일의 이미지를 다중 모델로 처리
    """
    logger.info(f"Loading images from: {csv_path}")
    
    test_df = pd.read_csv(csv_path)
    
    if "id" not in test_df.columns or "img_url" not in test_df.columns:
        raise ValueError(f"Required columns: id, img_url")
    
    logger.info(f"Loaded {len(test_df)} images")
    logger.info(f"Models: {json.dumps(MODELS, indent=2, ensure_ascii=False)}")
    
    preds = []
    n = len(test_df)
    
    for i, row in test_df.iterrows():
        _id = row["id"]
        img_url = row["img_url"]
        
        try:
            result = classify_multi_model_agent(img_url)
            label = result['prediction']
            
            print(f"[{i+1}/{n}] id={_id} -> {label}")
            
        except Exception as e:
            logger.error(f"[{i+1}/{n}] id={_id} ERROR: {e}")
            print(f"[{i+1}/{n}] id={_id} ERROR -> fallback 0")
            label = LABEL_NORMAL
        
        preds.append({"id": _id, "label": label})
        time.sleep(0.2)
    
    out_df = pd.DataFrame(preds, columns=["id", "label"])
    out_df.to_csv(output_path, index=False, encoding='utf-8')
    
    logger.info(f"Saved results to: {output_path}")
    print(f"\nSaved: {output_path}")
    print(out_df.head())
    
    return out_df


def main():
    """메인 실행 함수"""
    print_agent_flow_chart()
    
    logger.info("Multi-Model Manufacturing AI Agent - Starting")
    logger.info(f"Models Configuration:")
    for step, model in MODELS.items():
        profile = MODEL_PROFILES.get(step, {})
        logger.info(f"  {step.upper()}: {model}")
        logger.info(f"    - Purpose: {profile.get('purpose', 'N/A')}")
        logger.info(f"    - Capabilities: {profile.get('capabilities', [])}")
    
    if not Path(TEST_CSV_PATH).exists():
        logger.error(f"Input file not found: {TEST_CSV_PATH}")
        raise FileNotFoundError(TEST_CSV_PATH)
    
    results_df = process_images_with_multi_model(TEST_CSV_PATH, OUTPUT_PATH)
    
    normal_count = (results_df['label'] == 0).sum()
    abnormal_count = (results_df['label'] == 1).sum()
    
    logger.info(f"\nSummary:")
    logger.info(f"   Total: {len(results_df)}")
    logger.info(f"   Normal: {normal_count}")
    logger.info(f"   Abnormal: {abnormal_count}")
    logger.info(f"   Abnormal Rate: {abnormal_count/len(results_df)*100:.1f}%")
    
    print(f"\nSummary:")
    print(f"   Total: {len(results_df)}")
    print(f"   Normal: {normal_count}")
    print(f"   Abnormal: {abnormal_count}")
    print(f"   Abnormal Rate: {abnormal_count/len(results_df)*100:.1f}%")


if __name__ == "__main__":
    main()
