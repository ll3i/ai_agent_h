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
BRIDGE_URL = os.getenv('SALTLUX_API_BASE_URL', 'https://bridge.luxiacloud.com/llm/openai/chat/completions/gpt-4o-mini/create')
MODEL = "gpt-4o-mini-2024-07-18"

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
# 관찰 항목 정의
# =========================
# Baseline과 동일하게 관찰할 결함 항목을 정의합니다.
OBS_ITEMS = [
    ("package_damage", "크랙/파손/깨짐 등 패키지 손상"),
    ("lead_missing_or_broken", "리드 결손/단선"),
    ("lead_severe_bend_or_contact", "심한 휨 또는 리드끼리 접촉"),
    ("solder_bridge_or_blob", "솔더 브리지 또는 납땜 뭉침"),
    ("misalignment_severe", "소자 위치가 과도하게 틀어짐"),
]

KEYS = [k for k, _ in OBS_ITEMS]

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
    Baseline과 동일한 프롬프트 생성 (strict 모드 지원)
    
    Args:
        strict: True면 보수적 판단 (애매하면 false)
        
    Returns:
        프롬프트 문자열
    """
    header = (
        "아래 항목을 이미지에서 관찰해 true/false로 채워 JSON만 출력해.\n"
        "형식은 반드시 아래와 동일해야 한다.\n"
    )
    
    json_template = "{\n" + ",\n".join([f'  "{k}": false' for k, _ in OBS_ITEMS]) + "\n}"
    
    if strict:
        rule = "\n판단 기준:\n- 매우 보수적으로 판단한다. 애매하면 무조건 false.\n"
    else:
        rule = "\n판단 기준:\n- 아주 명확할 때만 true. 애매하면 false.\n"
    
    criteria = "\n".join([f"- {k}: {desc}" for k, desc in OBS_ITEMS])
    
    return header + json_template + rule + criteria


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
    
    payload = {"model": MODEL, "messages": messages, "stream": False}
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


# =========================
# Agent Steps (Judge-Think-Act-Verify 통합)
# =========================

def observe(img_url: str, strict: bool = False) -> Dict[str, bool]:
    """
    JUDGE Step: Observe (관찰 단계)
    
    Baseline의 observe 함수와 동일하지만,
    우리의 Judge 단계로 통합됩니다.
    
    Args:
        img_url: 이미지 URL
        strict: 보수적 모드
        
    Returns:
        {항목명: true/false} 딕셔너리
    """
    logger.info(f"  [OBSERVE] Analyzing image (strict={strict})")
    
    prompt = PROMPT_STRICT if strict else PROMPT_NORMAL
    
    try:
        content = _post_chat([
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": img_url}},
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
    THINK Step: Analyze observations
    
    관찰 결과를 분석하여 결함 지표를 식별합니다.
    
    Args:
        obs: 관찰 결과
        
    Returns:
        분석 결과
    """
    logger.info("  [THINK] Analyzing observations")
    
    defect_count = sum(1 for v in obs.values() if v)
    defects = [k for k, v in obs.items() if v]
    
    reasoning = {
        'total_defects': defect_count,
        'defect_items': defects,
        'observation_result': obs,
        'confidence_level': _estimate_confidence(defect_count, obs)
    }
    
    logger.debug(f"  [THINK] Detected {defect_count} defects: {defects}")
    
    return reasoning


def _estimate_confidence(defect_count: int, obs: Dict[str, bool]) -> str:
    """
    결함 개수에 따른 신뢰도 추정
    
    Args:
        defect_count: 결함 개수
        obs: 관찰 결과
        
    Returns:
        신뢰도 레벨 ('HIGH', 'MEDIUM', 'LOW')
    """
    if defect_count >= 2:
        return 'HIGH'  # 여러 결함이 감지되면 신뢰도 높음
    elif defect_count == 1:
        return 'MEDIUM'  # 단일 결함은 중간 신뢰도
    else:
        return 'LOW'  # 결함 없으면 신뢰도 낮음 (놓친 것이 있을 수 있음)


def act(reasoning: Dict[str, Any]) -> Tuple[int, bool]:
    """
    ACT Step: Make decision
    
    분석 결과를 바탕으로 판단을 내립니다.
    
    Args:
        reasoning: Think 단계의 결과
        
    Returns:
        (label, uncertain) 튜플
        - label: 0 (Normal) 또는 1 (Abnormal)
        - uncertain: True면 재검토 필요
    """
    logger.info("  [ACT] Making decision")
    
    defect_count = reasoning['total_defects']
    
    # 규칙 기반 판단
    label = LABEL_ABNORMAL if defect_count >= 1 else LABEL_NORMAL
    
    # 재검토 대상 판단 (Baseline과 동일)
    uncertain = (defect_count == 0) or (defect_count == 1)
    
    logger.debug(f"  [ACT] Decision: {label}, Uncertain: {uncertain}")
    
    return label, uncertain


def verify(label: int, reasoning: Dict[str, Any], 
          is_review: bool = False) -> Dict[str, Any]:
    """
    VERIFY Step: Validate decision
    
    의사결정을 검증합니다.
    
    Args:
        label: 의사결정 결과 (0 or 1)
        reasoning: 분석 결과
        is_review: 재검토된 결과인지 여부
        
    Returns:
        검증 결과
    """
    logger.info(f"  [VERIFY] Verifying decision (review={is_review})")
    
    confidence_level = reasoning.get('confidence_level', 'LOW')
    
    # 신뢰도에 따른 검증
    confidence_map = {
        'HIGH': 0.95,
        'MEDIUM': 0.70,
        'LOW': 0.50
    }
    
    final_confidence = confidence_map.get(confidence_level, 0.50)
    
    verification = {
        'verified': True,
        'decision': label,
        'decision_label': 'Normal' if label == 0 else 'Abnormal',
        'confidence': final_confidence,
        'confidence_level': confidence_level,
        'reasoning': reasoning
    }
    
    logger.debug(f"  [VERIFY] Confidence: {final_confidence:.2f}")
    
    return verification


# =========================
# Integrated Agent (Observe-Decide-Review + Judge-Think-Act-Verify)
# =========================

def classify_agent_integrated(img_url: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    통합 AI Agent
    
    Baseline의 Observe-Decide-Review 패턴을 우리의
    Judge-Think-Act-Verify 구조로 구현합니다.
    
    Flow:
    1. JUDGE(Observe): 1차 관찰
    2. THINK(Analyze): 결과 분석
    3. ACT(Decide): 초기 판단
    4. VERIFY(Review): 검증 및 필요시 재검토
    
    Args:
        img_url: 이미지 URL
        max_retries: 최대 재시도 횟수
        
    Returns:
        최종 판단 결과
    """
    logger.info("=" * 60)
    logger.info(f"🤖 Agent Processing: {img_url[-20:]}")
    logger.info("=" * 60)
    
    for attempt in range(max_retries):
        try:
            # ========== Step 1: JUDGE (1차 관찰) ==========
            obs1 = observe(img_url, strict=False)
            
            # ========== Step 2: THINK (분석) ==========
            reasoning1 = think(obs1)
            
            # ========== Step 3: ACT (판단) ==========
            label1, uncertain = act(reasoning1)
            
            # 애매하지 않으면 바로 종료
            if not uncertain:
                # ========== Step 4: VERIFY (검증) ==========
                verification = verify(label1, reasoning1, is_review=False)
                
                logger.info(f"✅ Final Decision: {verification['decision_label']} "
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
            label2, _ = act(reasoning2)
            
            # 재검토에서도 결함이 잡히면 비정상 확정
            if label2 == LABEL_ABNORMAL:
                verification = verify(label2, reasoning2, is_review=True)
                logger.info(f"✅ Final Decision: {verification['decision_label']} "
                           f"(confidence: {verification['confidence']:.2f})")
                logger.info("=" * 60 + "\n")
                
                return {
                    'prediction': label2,
                    'confidence': verification['confidence'],
                    'verified': True,
                    'iterations': 2
                }
            
            # 재검토에서 결함이 없으면 1차 결과 유지
            verification = verify(label1, reasoning1, is_review=True)
            logger.info(f"✅ Final Decision: {verification['decision_label']} "
                       f"(confidence: {verification['confidence']:.2f})")
            logger.info("=" * 60 + "\n")
            
            return {
                'prediction': label1,
                'confidence': verification['confidence'],
                'verified': True,
                'iterations': 2
            }
            
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"❌ Final attempt failed: {e}")
                raise
            
            logger.warning(f"⚠️  Attempt {attempt + 1} failed: {e}")
            wait_time = (0.5 * (2 ** attempt)) + random.uniform(0, 0.2)
            logger.info(f"  Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)


# =========================
# Main Pipeline
# =========================

def process_images_from_csv(csv_path: str, output_path: str) -> pd.DataFrame:
    """
    CSV 파일의 이미지 목록을 처리하고 결과 저장
    
    Args:
        csv_path: 입력 CSV 파일 경로
        output_path: 출력 CSV 파일 경로
        
    Returns:
        결과 DataFrame
    """
    logger.info(f"📂 Loading images from: {csv_path}")
    
    # CSV 로드
    test_df = pd.read_csv(csv_path)
    
    if "id" not in test_df.columns or "img_url" not in test_df.columns:
        raise ValueError(f"Required columns: id, img_url. Got: {test_df.columns.tolist()}")
    
    logger.info(f"✅ Loaded {len(test_df)} images")
    
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
    
    logger.info(f"✅ Saved results to: {output_path}")
    print(f"\n✅ Saved: {output_path}")
    print(out_df.head())
    
    return out_df


# =========================
# Entry Point
# =========================

def main():
    """메인 실행 함수"""
    print_agent_flow_chart()
    
    logger.info("🚀 Manufacturing AI Agent - Starting")
    logger.info(f"   API Key: {API_KEY[:20]}...")
    logger.info(f"   Model: {MODEL}")
    logger.info(f"   Input: {TEST_CSV_PATH}")
    logger.info(f"   Output: {OUTPUT_PATH}")
    
    # 입력 파일 확인
    if not Path(TEST_CSV_PATH).exists():
        logger.error(f"❌ Input file not found: {TEST_CSV_PATH}")
        raise FileNotFoundError(TEST_CSV_PATH)
    
    # 처리 시작
    results_df = process_images_from_csv(TEST_CSV_PATH, OUTPUT_PATH)
    
    # 통계
    normal_count = (results_df['label'] == 0).sum()
    abnormal_count = (results_df['label'] == 1).sum()
    
    logger.info(f"\n📊 Summary:")
    logger.info(f"   Total: {len(results_df)}")
    logger.info(f"   Normal: {normal_count}")
    logger.info(f"   Abnormal: {abnormal_count}")
    logger.info(f"   Abnormal Rate: {abnormal_count/len(results_df)*100:.1f}%")
    
    print(f"\n📊 Summary:")
    print(f"   Total: {len(results_df)}")
    print(f"   Normal: {normal_count}")
    print(f"   Abnormal: {abnormal_count}")
    print(f"   Abnormal Rate: {abnormal_count/len(results_df)*100:.1f}%")


if __name__ == "__main__":
    main()
