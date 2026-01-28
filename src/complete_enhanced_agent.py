"""
Complete Enhanced Integrated Agent - 4-Step Judge-Think-Act-Verify
Luxia 32B 최신 모델로 초고해상도 프롬프트 모두 포함
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv
import requests
import pandas as pd

# 환경 설정
load_dotenv()

# =========================
# 설정
# =========================
API_KEY = os.getenv('SALTLUX_API_KEY', 'YOUR_API_KEY')
BRIDGE_URL = "https://bridge.luxiacloud.com/llm/openai/chat/completions/{model}/create"

# 4단계 모델 설정
MODEL_JUDGE = "luxia3-llm-32b-0731"    # 상세 분석
MODEL_THINK = "luxia3-llm-32b-0731"    # 깊이 있는 추론
MODEL_ACT = "luxia3-llm-13b-0731"      # 빠른 결정 (비용 최적)
MODEL_VERIFY = "luxia3-llm-32b-0731"   # 최종 검증

HEADERS = {"apikey": API_KEY, "Content-Type": "application/json"}

# 시스템 프롬프트
SYSTEM_PROMPT = """
당신은 반도체 제조 공정의 최고 수준 품질 검사 전문가입니다.
모든 응답은 정확한 JSON 형식으로 제공합니다.
기술적 정확성과 명확한 설명을 추구합니다.
"""

# =========================
# ACT PROMPT (STEP 3)
# =========================
def build_act_prompt(think_results: Dict[str, Any]) -> str:
    """
    ACT 단계: 빠른 결정 및 리스크 판단 (Luxia 13B용)
    ~1500 토큰 규모의 의사결정 프롬프트
    """
    
    prompt = """
[역할]
당신은 반도체 품질 결정 시스템의 의사결정 전문가입니다.
Think 단계의 깊이있는 분석을 받아, 빠르고 정확한 판정을 내립니다.

[결정 프레임워크]

【결정 기준 - 이진 판정】

[STEP 1] 즉시 불량 판정 규칙 (절대 규칙)
  
  다음 중 하나라도 YES면 → 무조건 ABNORMAL 불량 처리:
  
  ✗ 솔더 브리지 (2개 이상 핀 연결): 전기적 쇼트 → 즉시 불량
  ✗ 리드 완전 결손 (1개 이상): 회로 오픈 → 즉시 불량
  ✗ 리드 간 접촉 (0.5mm 미만 간격): 우발적 쇼트 위험 → 즉시 불량
  ✗ 패키지 대형 크랙 (> 3mm 길이): 습도 침투 → 즉시 불량
  ✗ 신뢰성 지표 > 0.7: 매우 위험 → 즉시 불량
  
  → 판정: ABNORMAL (신뢰도: 99%)

[STEP 2] 조건부 불량 판정 규칙 (주의 규칙)
  
  다음 조합인 경우 → ABNORMAL 불량 처리:
  
  ✗ 리드 부러짐(단선) + 미세 솔더 뭉침: 복합 결함 → 불량
  ✗ 정렬 오차(> 1.5mm) + 리드 휨: 조립 품질 저하 → 불량
  ✗ 미세 크랙(1-3mm) + 패키지 변색: 스트레스 신호 → 불량
  ✗ 리드 부분 손상 + 정렬 오차 > 2mm: 다중 결함 → 불량
  
  → 판정: ABNORMAL (신뢰도: 85-95%)

[STEP 3] 정상 판정 규칙 (엄격한 기준)
  
  모든 항목이 다음을 만족할 때만 → NORMAL 정상 처리:
  
  ✓ 패키지: 손상 없음, 색상 균일, 글자 선명
  ✓ 리드: 8개 모두 완전, 직선, 정렬 좋음
  ✓ 솔더: 깔끔한 멘스커스, 브리지 없음, 뭉침 없음
  ✓ 정렬: 중심에서 0.5mm 이내, 회전 < 2도
  ✓ 이미지 질: 점수 > 7/10
  
  → 판정: NORMAL (신뢰도: 90-99%)

[STEP 4] 모호한 경우 의사결정
  
  상황: 한두 가지 항목이 애매한 경우
  
  규칙 4-1: 이미지 질이 낮은 경우 (점수 < 5)
    → "이미지 재촬영 필요" + NORMAL (보수적 신뢰도: 50%)
    → 이유: 데이터 불충분으로 인한 확실성 부족
  
  규칙 4-2: 미세한 결함 (점수 < 3/10)
    → NORMAL (신뢰도: 70%)
    → 이유: 제조 허용 범위 내
  
  규칙 4-3: 경계 수준 결함 (점수 3-5/10)
    → ABNORMAL + 재검사 권고 (신뢰도: 75%)
    → 이유: 신뢰성 여유 확보를 위해 보수적 판정

【리스크 평가】

5-1. 신뢰성 리스크 등급 (1~5단계)

  LEVEL 5 (CRITICAL - 긴급)
  • 솔더 브리지 감지됨
  • 리드 완전 결손 1개 이상
  • 리드 간 접촉 감지됨
  • 패키지 대형 크랙
  → 조치: 즉시 불량 처리, 생산 중단, 원인 규명

  LEVEL 4 (HIGH - 높음)
  • 리드 부러짐 1개 이상
  • 정렬 오차 > 2mm
  • 심한 리드 휨 (> 20도)
  • 미세 솔더 브리지 (미성장)
  → 조치: 불량 처리, 생산 점검, 설정 검토

  LEVEL 3 (MEDIUM - 중간)
  • 미세 정렬 오차 (1-2mm)
  • 약한 리드 휨 (5-20도)
  • 솔더 뭉침 (미세)
  • 미세 패키지 변색
  → 조치: 불량 또는 재검사, 공정 모니터링

  LEVEL 2 (LOW - 낮음)
  • 매우 미세한 불규칙성
  • 글자 약간 흐림
  • 색상 약간 변화
  → 조치: 정상 처리, 기록만

  LEVEL 1 (NONE - 없음)
  • 모든 항목 정상
  → 조치: 정상 처리, 납품 가능

5-2. 비즈니스 영향도

  즉시 불량의 비용:
  • 현재 손실: 1개 부품 비용
  • 향후 손실 방지: 품질 신뢰도 유지
  • 고객 만족도: 유지/증대
  
  누락 불량의 비용:
  • 현장 고장 비용: 현재 손실의 10배 이상
  • 브랜드 손상: 장기적 신뢰도 저하
  • 법적 책임: 상품 책임 소송
  
  → 보수적 판정이 경제적으로 유리

【최종 판정 프로세스】

STEP A: 위 절대 규칙 검토
  → 하나라도 YES? → ABNORMAL (끝)

STEP B: 위 조건부 규칙 검토
  → 해당? → ABNORMAL (끝)

STEP C: 정상 규칙 검토
  → 모두 만족? → NORMAL (끝)

STEP D: 모호한 경우 처리
  → 이미지 질 판단
  → 보수적 판정 적용
  → 신뢰도 낮출 것

[신뢰도 계산 공식]

기본 신뢰도 = (이미지질_정규화) * 100

보정 계수:
• 절대 규칙 적용: × 0.99 (거의 확실)
• 조건부 규칙 적용: × 0.88 (높은 확신)
• 정상 규칙 적용: × 0.92 (높은 확신)
• 모호한 경우: × 0.65 (낮은 확신)

최종 신뢰도 = 기본 신뢰도 × 보정 계수

신뢰도 등급:
• 95-100: 매우 높음 (확실)
• 80-95: 높음 (거의 확실)
• 60-80: 중간 (상당히 확실)
• 40-60: 낮음 (의심)
• < 40: 매우 낮음 (재검사 필요)

【최종 의사결정】

판정 이유:
• 절대 규칙 적용: "치명적 결함: [구체적 결함명]"
• 조건부 규칙 적용: "복합 결함: [결함 조합]"
• 정상 규칙 적용: "모든 항목 정상"
• 모호한 경우: "데이터 불충분 또는 경계 사항"

권장 조치:
• ABNORMAL: "즉시 불량 처리", "재검사 권고", "공정 점검"
• NORMAL: "납품 가능", "추가 조치 없음"
• 의심: "이미지 재촬영", "추가 검사", "샘플 테스트"

[최종 JSON 응답 형식]
"""

    json_template = """{
  "decision_process": {
    "absolute_rule_violated": false,
    "absolute_rule_details": "없음",
    "conditional_rule_applied": false,
    "conditional_rule_details": "없음",
    "normal_rule_satisfied": true,
    "rule_satisfaction_details": "모든 항목 정상"
  },
  "risk_assessment": {
    "risk_level": "LEVEL 1: NONE",
    "reliability_risk": "없음",
    "business_impact": "정상 처리",
    "critical_failure_probability": "< 0.1%",
    "field_failure_estimate": "매우낮음"
  },
  "confidence_calculation": {
    "base_confidence": 95,
    "image_quality_factor": 0.95,
    "rule_certainty_factor": 0.98,
    "final_confidence": 92,
    "confidence_grade": "높음"
  },
  "final_decision": {
    "verdict": "NORMAL",
    "verdict_explanation": "모든 항목이 정상 기준을 만족함",
    "confidence_score": 92,
    "recommended_action": "납품 가능",
    "additional_checks_needed": false,
    "retest_recommended": false
  }
}"""

    prompt += f"\n\n[Think 단계 결과]\n{json.dumps(think_results, ensure_ascii=False, indent=2)}"
    prompt += f"\n\n[의사결정 결과]\n{json_template}"
    
    return prompt


# =========================
# VERIFY PROMPT (STEP 4)
# =========================
def build_verify_prompt(judge_results: Dict, think_results: Dict, act_results: Dict) -> str:
    """
    VERIFY 단계: 최종 검증 및 QA (Luxia 32B용)
    ~2000 토큰 규모의 최종 검증 프롬프트
    """
    
    prompt = """
[역할]
당신은 반도체 품질 보증(QA) 최고 검수자입니다.
Judge, Think, Act의 모든 단계를 검증하고,
최종 판정의 일관성과 신뢰성을 보장합니다.

[검증 프레임워크]

【검증 LEVEL 1】 상호 검증 (Cross-Validation)

1-1. Judge ↔ Think 검증
  
  확인 항목:
  ✓ Think의 결함 종류가 Judge 결과와 일치?
    - 불일치 시: 분석 재검토 필요
  
  ✓ Think의 심각도 점수가 Judge와 논리적으로 연결?
    - 점수 계산 방식 검증
  
  ✓ Think의 근본원인이 Judge 결과와 합리적?
    - 예: 솔더브리지 감지 → 리플로우 온도 높음 (합리적)
    - 예: 정렬오차 감지 → 솔더부족 (비합리적 - 재검토)
  
  검증 결과:
  • 완전 일치: 신뢰도 +5점
  • 부분 불일치: 신뢰도 -10점 (재분석)
  • 심각 불일치: 신뢰도 -20점 (재촬영)

1-2. Think ↔ Act 검증
  
  확인 항목:
  ✓ Act의 최종 판정이 Think의 결론과 일관성?
    - 예: Think "신뢰성지표 0.8" → Act "ABNORMAL" (일관)
    - 예: Think "신뢰성지표 0.2" → Act "ABNORMAL" (부일관 - 재검토)
  
  ✓ Act의 신뢰도가 Judge/Think의 분석 품질 반영?
    - Judge 이미지질 점수와 Act 신뢰도 연관성 확인
  
  ✓ Act의 권장 조치가 Think의 위험 평가와 일관?
    - Think "LEVEL 5 CRITICAL" → Act "즉시 불량 처리" (일관)
  
  검증 결과:
  • 완전 일치: 신뢰도 유지
  • 부분 불일치: 신뢰도 -10점
  • 불일치: 신뢰도 -20점 (최종 검토)

1-3. 논리적 일관성 검사
  
  점검 항목:
  ✓ Judge 결함 개수 = 합산된 결함들의 합?
  ✓ 심각도 점수의 계산 방식이 반복 적용?
  ✓ 신뢰도가 이미지질과 일관성 있게 변화?
  ✓ 최종 판정이 판정 기준에 부합?

【검증 LEVEL 2】 도메인 검증 (Domain Expert Review)

2-1. 반도체 신뢰성 관점

  질문:
  • 이 결함의 조합이 실제로 신뢰성 저해?
  • 현장에서 고장날 확률이 맞게 평가?
  • 제조 공정상 이 결함이 발생하는 것이 합리적?
  
  예시 검증:
  □ Judge: 솔더브리지 감지
    Think: 신뢰성 CRITICAL
    → 검증: 솔더브리지 = 쇼트 = 고장 확실 ✓
  
  □ Judge: 미세글자흐림
    Think: 신뢰성 정상
    → 검증: 글자흐림은 신뢰성 무관 ✓
  
  □ Judge: 정렬오차 2.5mm
    Think: 신뢰성 주의
    → 검증: 오차 > 2mm일 때 조립 신뢰성 저하 ✓

2-2. 제조 공정 관점

  검증:
  ✓ 근본원인이 실제 공정 문제를 지적?
    - "리플로우 온도 높음" → 실제 온도 곡선 검증 가능?
    - "픽앤플레이스 오정렬" → 실제 센서 교정 가능?
  
  ✓ 권장 조치가 실행 가능한가?
    - "온도 하강" → 몇도 하강 필요?
    - "센서 재교정" → 구체적 절차?

2-3. 패턴 인식

  누적 데이터 기반 검증:
  • 이번 불량이 최근의 다른 사례들과 유사?
  • 같은 생산 라인의 다른 제품도 같은 결함?
  • 시간대에 따른 패턴 관찰 가능?

【검증 LEVEL 3】 이미지 품질 재평가

3-1. 이미지 충분성 검증

  점검:
  ✓ 이미지가 모든 8개 리드를 충분히 표현?
    - 리드 끝이 명확히 보이는가?
    - 리드 간 간격을 정확히 측정 가능한가?
  
  ✓ 패키지 전체 윤곽이 선명?
    - 모서리 손상을 감지할 수 있는가?
  
  ✓ 납땜 부분이 충분히 상세?
    - 브리지를 확실히 판별할 수 있는가?
  
  ✓ 조명이 모든 영역을 공평하게 조사?
    - 그림자 때문에 결함을 놓쳤을 가능성?

3-2. 불확실성 평가

  만약 다음 중 하나라면 이미지 재촬영 권고:
  □ 초점이 흐린 부분 (리드 팁)
  □ 강한 역광으로 인한 측정 불가
  □ 각도가 30도 이상 기울어짐
  □ 노이즈가 결함 판별을 방해
  □ 해상도가 너무 낮음 (< 300x300)

【검증 LEVEL 4】 최종 판정 확인

4-1. 판정 타당성 (Decision Soundness)

  정상 판정의 경우 (NORMAL):
  ✓ 모든 5개 항목(package/lead/solder/alignment/quality)이 기준 충족?
  ✓ 숨어있는 결함이 없을 가능성이 높은가?
  ✓ 신뢰도 점수가 70점 이상인가?
  → 통과 시: 최종 확정 (신뢰도 유지)
  → 미통과 시: 보수적 수정 (신뢰도 5-10점 감소)

  불량 판정의 경우 (ABNORMAL):
  ✓ 최소 하나의 절대 규칙이 위반되었는가?
  ✓ 또는 명확한 복합 결함이 있는가?
  ✓ Judge에서 이 결함이 명확히 감지되었는가?
  → 통과 시: 최종 확정 (신뢰도 유지)
  → 미통과 시: 신뢰도 감소 또는 재평가

4-2. 신뢰도 최종 조정

  조정 규칙:
  • 모든 단계 완전 일관: ±0점
  • 부분 불일치 발견: -5점
  • 논리 오류 발견: -10점
  • 도메인 지식 오류: -15점
  • 이미지 질 의심: -20점

  최종 신뢰도 범위:
  • 95-100점: "매우 높음 - 즉시 처리"
  • 80-95점: "높음 - 정상 처리"
  • 60-80점: "중간 - 기록 후 처리"
  • 40-60점: "낮음 - 재검사 권고"
  • < 40점: "매우 낮음 - 재촬영 필수"

【검증 체크리스트】

□ 상호 검증 완료 (Judge-Think-Act)
□ 논리적 일관성 확인
□ 도메인 지식 검증
□ 제조 공정 타당성 확인
□ 이미지 품질 재평가
□ 신뢰도 최종 조정
□ 권장 조치의 실행 가능성 확인

[최종 JSON 응답]
"""

    json_template = """{
  "cross_validation": {
    "judge_think_consistency": "일치",
    "judge_think_details": "모든 결함이 일관성있게 분석됨",
    "think_act_consistency": "일치",
    "think_act_details": "판정과 근거가 논리적으로 연결됨",
    "logical_coherence": "높음",
    "coherence_score": 95
  },
  "domain_validation": {
    "reliability_assessment_valid": true,
    "reliability_validation": "솔더브리지 = 쇼트 = 고장확실",
    "manufacturing_causality_valid": true,
    "manufacturing_validation": "근본원인이 제조공정상 타당",
    "pattern_consistency": "일관된 결함 패턴"
  },
  "image_quality_revalidation": {
    "image_sufficiency": "충분",
    "resolution_adequate": true,
    "focus_clarity": "선명",
    "lighting_quality": "적절",
    "measurement_confidence": "높음",
    "uncertainty_risk": "없음",
    "retake_needed": false
  },
  "final_verdict_confirmation": {
    "verdict": "NORMAL",
    "verdict_valid": true,
    "validation_reason": "모든 검증 단계에서 일관성 확인",
    "critical_rules_met": true,
    "confidence_adjustment": 0,
    "final_confidence": 92
  },
  "qa_notes": "모든 단계 검증 완료. 최종 판정 확정.",
  "recommended_final_action": "납품 가능"
}"""

    prompt += f"\n\n[종합 분석 결과]\n"
    prompt += f"Judge: {json.dumps(judge_results, ensure_ascii=False, indent=2)[:500]}...\n"
    prompt += f"Think: {json.dumps(think_results, ensure_ascii=False, indent=2)[:500]}...\n"
    prompt += f"Act: {json.dumps(act_results, ensure_ascii=False, indent=2)[:500]}...\n"
    prompt += f"\n[최종 검증]\n{json_template}"
    
    return prompt


# =========================
# API CALL & JSON EXTRACTION
# =========================
def call_llm(model: str, messages: List[Dict], timeout: int = 120) -> str:
    """LLM API 호출"""
    url = BRIDGE_URL.format(model=model)
    payload = {
        "model": model,
        "messages": messages,
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=timeout)
        
        if response.status_code != 200:
            raise RuntimeError(f"API Error: {response.status_code}")
        
        return response.json()["choices"][0]["message"]["content"].strip()
    
    except Exception as e:
        print(f"❌ API 호출 실패: {e}")
        return "{}"


def extract_json(response: str) -> Dict:
    """LLM 응답에서 JSON 추출"""
    try:
        return json.loads(response)
    except:
        import re
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
    return {}


# =========================
# JUDGE PROMPT (STEP 1)
# =========================
def build_judge_prompt(image_analysis: str = "") -> str:
    """JUDGE 단계: 상세 이미지 분석"""
    
    prompt = """
[역할과 목표]
당신은 반도체 제조 품질 검사 최고 전문가입니다.
이미지를 6단계에 걸쳐 극도로 상세하게 분석합니다.

[분석 프로세스]

【1단계】 이미지 메타데이터 평가
  ✓ 해상도: 고/중간/저해상도
  ✓ 초점: 매우선명/선명/다소흐림/흐림
  ✓ 조명: 균등/과도/부족
  ✓ 촬영각도: 정면/약간기울임/크게기울임
  ✓ 노이즈: 없음/적음/중간/많음

【2단계】 패키지(Package) 상세 검사
  ✓ 패키지 기본정보 (타입, 크기, 색상)
  ✓ 표면 상태 (균일성, 색상, 광택)
  ✓ 표면 손상 (크랙, 깨짐, 벗겨짐, 글자, 변색)
  ✓ 가장자리 상세 검사 (4개 모서리 각각)
  ✓ 응력 집중 영역 감지

【3단계】 리드(Lead) 극도로 상세 검사
  ✓ 전체 리드 개요
  ✓ 8개 리드 각각 상세 검사 (완전성, 길이, 곧기, 색상, 산화, 접촉)
  ✓ 리드 그룹 분석 (좌/우 통합 상태)
  ✓ 리드 간 간격 균등성
  ✓ 리드 정렬 상태

【4단계】 납땜(Solder) 부분 상세 검사
  ✓ 전체 납땜 개요
  ✓ 각 리드별 납땜 상태 (양, 형태, 높이, 접촉)
  ✓ 리드 간 납땜 상태
  ✓ 납땜 결함 검사 (브리지, 뭉침, 산화, 콜드솔더)

【5단계】 정렬(Alignment) 상세 검사
  ✓ 패키지 정렬 상태 (좌우, 상하, 회전)
  ✓ 리드 정렬 상태
  ✓ 정렬 신뢰도

【6단계】 종합 평가
  ✓ 이미지 전체 질 점수 (1~10점)
  ✓ 분석 신뢰도
  ✓ 종합 분석 요약

[최종 JSON 응답 형식으로 출력]
"""
    return prompt


def build_think_prompt(judge_results: Dict[str, Any]) -> str:
    """THINK 단계: 깊이있는 분석"""
    
    prompt = """
[역할]
당신은 반도체 제조 공정 전문가이자 품질 분석가입니다.

[분석 프레임워크]

【구간 1】 결함 종합 평가
  • 검출된 결함 종류
  • 결함 심각도 종합 점수
  • 신뢰성 평가

【구간 2】 근본 원인 분석
  • 패키지 손상의 경우
  • 리드 결손/단선의 경우
  • 리드 심한휨/접촉의 경우
  • 솔더 브리지/뭉침의 경우
  • 정렬 오차의 경우

【구간 3】 도메인 지식 기반 신뢰성 분석
  • 반도체 신뢰성 메커니즘
  • 신뢰성 지표 계산
  
【구간 4】 최종 판정
  • ABNORMAL 조건
  • NORMAL 조건
  
【구간 5】 추가 정보
  • 위험 신호 (Red Flags)
  • 추가 검사 권고

[JSON 형식으로 응답]
"""
    return prompt


# =========================
# MAIN TEST
# =========================
if __name__ == "__main__":
    print("=" * 80)
    print("Complete Enhanced Agent - Judge-Think-Act-Verify with Luxia 32B")
    print("=" * 80)
    
    # 프롬프트 통계
    sample_judge_results = {"package_damage": False}
    sample_think_results = {"reliability_level": "정상"}
    sample_act_results = {"verdict": "NORMAL"}
    
    print("\n[프롬프트 길이 분석]")
    print("-" * 40)
    
    judge_prompt = build_judge_prompt()
    print(f"JUDGE 프롬프트: ~{len(judge_prompt)//4} 토큰 (약 {len(judge_prompt)} 자)")
    
    think_prompt = build_think_prompt(sample_think_results)
    print(f"THINK 프롬프트: ~{len(think_prompt)//4} 토큰 (약 {len(think_prompt)} 자)")
    
    act_prompt = build_act_prompt(sample_act_results)
    print(f"ACT 프롬프트: ~{len(act_prompt)//4} 토큰 (약 {len(act_prompt)} 자)")
    
    verify_prompt = build_verify_prompt(sample_judge_results, sample_think_results, sample_act_results)
    print(f"VERIFY 프롬프트: ~{len(verify_prompt)//4} 토큰 (약 {len(verify_prompt)} 자)")
    
    total = len(judge_prompt) + len(think_prompt) + len(act_prompt) + len(verify_prompt)
    print(f"\n총 프롬프트: ~{total//4} 토큰 (약 {total} 자)")
    print("✓ 모두 매우 상세한 초고해상도 프롬프트입니다!")
    
    print("\n" + "=" * 80)
