"""
Enhanced Integrated Manufacturing AI Agent - LUXIA 32B with Ultra-Detailed Prompts
Baseline(Observe-Decide-Review)과 Judge-Think-Act-Verify 구조 통합 + 초고해상도 프롬프트
사용 모델: Luxia 32B (최신 초고성능)
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
import requests

# 환경 설정
load_dotenv()

# =========================
# 설정 (Luxia 32B 최신 모델)
# =========================
API_KEY = os.getenv('SALTLUX_API_KEY', 'YOUR_API_KEY')
BRIDGE_URL = "https://bridge.luxiacloud.com/llm/openai/chat/completions/{model}/create"
MODEL_JUDGE = "luxia3-llm-32b-0731"    # 최신 32B: 상세 비전 분석
MODEL_THINK = "luxia3-llm-32b-0731"    # 최신 32B: 깊이 있는 추론
MODEL_ACT = "luxia3-llm-13b-0731"      # 13B: 빠른 결정 (비용 최적)
MODEL_VERIFY = "luxia3-llm-32b-0731"   # 최신 32B: 최종 검증

HEADERS = {"apikey": API_KEY, "Content-Type": "application/json"}

# 관찰 항목
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
# SYSTEM PROMPT
# =========================
SYSTEM_PROMPT = """
당신은 반도체 제조 공정의 최고 수준 품질 검사 전문가입니다.
- 제공된 PCB/IC 패키지 이미지를 극도로 세밀하게 분석합니다
- 반도체 신뢰성 및 제조 공정에 깊은 지식이 있습니다
- 기술적 정확성과 명확한 표현을 추구합니다
- 모든 응답은 요청한 JSON 형식으로만 제공합니다
"""

# =========================
# JUDGE PROMPT (STEP 1)
# =========================
def build_judge_prompt(image_analysis: str = "") -> str:
    """
    JUDGE 단계: 이미지 극도로 상세 분석 (Luxia 32B용)
    ~2000 토큰 규모의 상세 프롬프트
    """
    
    prompt = """
[역할과 목표]
당신은 반도체 제조 품질 검사의 최고 전문가입니다.
제공된 이미지를 극도로 자세하게 관찰하고, 기술적으로 정확한 분석을 제공합니다.

[분석 지침 - 6단계 체계적 관찰]

【1단계】 이미지 메타데이터 평가 (30초)
  ✓ 해상도: 고해상도(> 500x500) / 중간(300-500) / 저해상도(< 300)
  ✓ 초점: 매우선명(> 0.9) / 선명(0.7-0.9) / 다소흐림(0.5-0.7) / 흐림(< 0.5)
  ✓ 조명: 균등/과도/부족 - 그림자 영역의 가시성
  ✓ 촬영각도: 정면 0도 / 약간기울임 5-15도 / 크게기울임 > 15도
  ✓ 노이즈: 없음(0%) / 적음(1-5%) / 중간(5-10%) / 많음(> 10%)
  ✓ 배경: 깨끗함 / 약간더러움 / 많은간섭물

【2단계】 패키지(Package) 상세 검사 (120초)
  
  2-1. 패키지 기본 정보
    • 패키지 타입: DIP / SOP / QFP / BGA / 기타 (명시)
    • 크기 추정: 10mm / 15mm / 20mm / 기타
    • 색상: 검정 / 회색 / 갈색 / 기타 (명시)
    • 패키지 기하학적 형태: 정사각형 / 직사각형 / 기타
  
  2-2. 패키지 표면 상태 (0.1mm 단위 검사)
    • 전체 표면 균일성: 매우균일 / 균일 / 약간거친 / 거침
    • 색상 균일성: 완벽 / 미세변화 / 불균일 / 심한얼룩
    • 표면 광택: 무광(매트) / 반광택 / 고광택
    • 표면 손상 검사:
      - 크랙 (균열): 없음 / 미세크랙(< 1mm) / 중간크랙(1-5mm) / 큰크랙(> 5mm)
      - 깨짐 (파손): 없음 / 모서리만 / 모서리+면 / 심각
      - 벗겨짐 (레이어): 없음 / 미세 / 중간 / 심각
      - 글자/마킹 상태: 선명 / 약간흐림 / 흐림 / 깨짐
      - 변색 / 검은 자국: 없음 / 미세 / 중간 / 심각
      - 응력 집중 영역: 없음 / 보임 (위치 명시)
  
  2-3. 패키지 가장자리 상세 검사
    • 모든 4개 모서리(상단, 하단, 좌측, 우측) 각각 점검
    • 각 모서리: 깨끗함 / 미세손상 / 중간손상 / 심각손상
    • 모서리 날카로움: 정상 / 약간무딘 / 많이무딘
    • 모서리 직선성: 완벽 / 미세굽음 / 눈에띄는굽음

【3단계】 리드(Lead) 극도로 상세 검사 (180초)
  
  3-1. 전체 리드 개요
    • 리드 개수: 예상된 수량 (보통 8-16개)
    • 리드 배치: 양측 / 네방향 / 기타 (명시)
    • 리드 피치(간격): 정상(1.27mm/1.5mm 등) / 비표준(명시)
  
  3-2. 각 리드별 상세 검사 (8개 또는 16개 리드 모두)
  
    좌측 상단 리드 (Left-Top, LT):
      • 완전성: 정상(완전) / 단선(끝 손상) / 결손(완전없음)
      • 길이: 정상(5-7mm) / 너무짧음 / 너무길음
      • 곧기: 완벽직선 / 미세굽음(< 5도) / 중간굽음(5-20도) / 심한굽음(> 20도)
      • 휨 방향: 직선 / 상향 / 하향 / 좌향 / 우향 / 다중방향
      • 색상: 은색(정상) / 금색(정상) / 검정(산화) / 기타
      • 산화 정도: 없음 / 미세 / 중간 / 심각
      • 리드 끝 상태: 깨끗 / 약간손상 / 많이손상
      • 접촉 여부: 다른 리드와 접촉 안함 / 약간접촉(0.5-1mm) / 심한접촉(< 0.5mm)
    
    좌측 중상 리드 (Left-Upper-Middle, LUM):
      [위와 동일한 검사 항목]
    
    좌측 중하 리드 (Left-Lower-Middle, LLM):
      [위와 동일한 검사 항목]
    
    좌측 하단 리드 (Left-Bottom, LB):
      [위와 동일한 검사 항목]
    
    우측 상단 리드 (Right-Top, RT):
      [위와 동일한 검사 항목]
    
    우측 중상 리드 (Right-Upper-Middle, RUM):
      [위와 동일한 검사 항목]
    
    우측 중하 리드 (Right-Lower-Middle, RLM):
      [위와 동일한 검사 항목]
    
    우측 하단 리드 (Right-Bottom, RB):
      [위와 동일한 검사 항목]
  
  3-3. 리드 그룹 분석
    • 좌측 리드 4개 통합 상태: 모두정상 / 1개결함 / 2개이상결함
    • 우측 리드 4개 통합 상태: 모두정상 / 1개결함 / 2개이상결함
    • 좌우 대칭성: 완벽 / 미세차이 / 눈에띄는차이
    • 리드 간 간격 균등성: 균등 / 약간불균등 / 많이불균등
    • 리드 정렬: 수직정렬완벽 / 미세오차(< 0.5mm) / 중간오차(0.5-2mm) / 심한오차(> 2mm)

【4단계】 납땜(Solder) 부분 상세 검사 (120초)
  
  4-1. 전체 납땜 개요
    • 납땜 색상: 은색(정상) / 검정(산화) / 갈색(변색)
    • 납땜 광택: 광택있음(정상) / 무광(산화됨) / 불균등
    • 납땜 표면 형태: 매끈함(정상) / 거칠음(재냉각 흔적)
  
  4-2. 각 리드 납땜 상태 (8-16개 각각)
    • 납땜량: 적절 / 부족(드라이솔더) / 과다(뭉침)
    • 납땜 형태: 매끈한멘스커스(정상) / 둥근형 / 평평한형 / 뭉친형
    • 납땜 높이: 적절(리드높이의 50-80%) / 너무낮음 / 너무높음
    • 리드 접촉: 완벽접촉 / 불완전접촉 / 접촉없음(드라이솔더)
  
  4-3. 리드 간 납땜 상태 (모든 인접 리드 쌍)
    • 좌측 LT-LUM: 분리됨 / 0.5mm 이상간격 / 접촉위험(< 0.5mm) / 접촉됨(브리지)
    • 좌측 LUM-LLM: [위와 동일]
    • 좌측 LLM-LB: [위와 동일]
    • 우측 RT-RUM: [위와 동일]
    • 우측 RUM-RLM: [위와 동일]
    • 우측 RLM-RB: [위와 동일]
  
  4-4. 납땜 결함 검사
    • 브리지 (Bridge): 없음 / 미세브리지(2개핀) / 다중브리지 / 심각
    • 납덩이 (Blob): 없음 / 미세 / 중간 / 심각
    • 스플래시 (Splash): 없음 / 약간 / 많음
    • 콜드솔더 (Cold Solder): 없음 / 가능성있음 / 확실함
    • 보이드 (Void): 없음 / 미세 / 중간 / 심각

【5단계】 정렬(Alignment) 상세 검사 (90초)
  
  5-1. 패키지 정렬 상태
    • 좌우 정렬: 완벽중심 / 미세오차(< 0.5mm) / 중간오차(0.5-2mm) / 심한오차(> 2mm)
    • 상하 정렬: 완벽중심 / 미세오차 / 중간오차 / 심한오차
    • 회전: 0도(완벽) / 1-5도 / 5-15도 / > 15도
    • 회전방향: 시계방향 / 반시계방향 (해당하는 경우)
    • 정렬 오차 원인 추측: 조립기 오차 / 픽앤플레이스 오차 / 냉각 변형 / 기타
  
  5-2. 리드 정렬 상태
    • 모든 리드가 동일한 직선 상에 배치: 예 / 아니오
    • 좌측 리드 일직선성: 완벽 / 미세굽음 / 눈에띄는굽음
    • 우측 리드 일직선성: 완벽 / 미세굽음 / 눈에띄는굽음
    • 좌우 리드 높이 동일: 예 / 아니오
  
  5-3. 정렬 신뢰도
    • 이미지 각도가 정렬 측정에 미치는 영향: 없음 / 약간 / 상당함

【6단계】 종합 평가 (60초)
  
  6-1. 이미지 전체 질 점수: 1~10점
    • 점수 = (해상도점수 + 초점점수 + 조명점수 + 각도점수 + 노이즈점수) / 5
  
  6-2. 분석 신뢰도: 매우높음(95%+) / 높음(80-95%) / 중간(60-80%) / 낮음(< 60%)
    • 신뢰도에 영향을 주는 요인들 명시
  
  6-3. 종합 분석 요약: 3-5문장

[최종 JSON 응답 형식]
반드시 아래의 정확한 JSON 형식으로만 응답하세요. 다른 텍스트는 없어야 합니다.
"""
    
    json_template = """{
  "image_quality": {
    "resolution": "고해상도/중간/저해상도",
    "focus": "매우선명/선명/다소흐림/흐림",
    "lighting": "균등/과도/부족",
    "angle": "정면/약간기울임/크게기울임 (각도 명시)",
    "noise": "없음/적음/중간/많음",
    "background": "깨끗함/약간더러움/많은간섭물",
    "overall_quality_score": 8
  },
  "package_analysis": {
    "type": "DIP/SOP/QFP/기타",
    "size_estimated": "10-20mm",
    "color": "검정/회색/갈색/기타",
    "surface_uniformity": "매우균일/균일/약간거친/거침",
    "color_uniformity": "완벽/미세변화/불균일/심한얼룩",
    "glossiness": "무광/반광택/고광택",
    "cracks": "없음/미세크랙/중간크랙/큰크랙",
    "damage": "없음/미세손상/중간손상/심각손상",
    "peeling": "없음/미세/중간/심각",
    "marking_clarity": "선명/약간흐림/흐림/깨짐",
    "discoloration": "없음/미세/중간/심각",
    "edge_condition": "깨끗함/미세손상/중간손상/심각손상",
    "package_damage_detected": false,
    "package_damage_description": "없음"
  },
  "leads_analysis": {
    "total_count": 8,
    "configuration": "양측",
    "pitch_standard": "1.27mm",
    "left_side": {
      "LT": {
        "integrity": "정상",
        "length": "정상",
        "straightness": "완벽직선",
        "bend_direction": "직선",
        "color": "은색",
        "oxidation": "없음",
        "tip_condition": "깨끗",
        "contact_status": "접촉안함"
      },
      "LUM": {},
      "LLM": {},
      "LB": {},
      "overall_status": "모두정상"
    },
    "right_side": {
      "RT": {},
      "RUM": {},
      "RLM": {},
      "RB": {},
      "overall_status": "모두정상"
    },
    "symmetry": "완벽",
    "spacing_uniformity": "균등",
    "alignment": "수직정렬완벽",
    "missing_or_broken_detected": false,
    "missing_details": "없음",
    "severe_bend_detected": false,
    "bend_details": "없음"
  },
  "solder_analysis": {
    "overall_color": "은색",
    "overall_glossiness": "광택있음",
    "surface_texture": "매끈함",
    "individual_leads": {
      "LT": {
        "amount": "적절",
        "shape": "매끈한멘스커스",
        "height": "적절",
        "contact": "완벽접촉"
      }
    },
    "inter_lead_status": {
      "LT_LUM_gap": "0.5mm이상",
      "LUM_LLM_gap": "0.5mm이상",
      "LLM_LB_gap": "0.5mm이상",
      "RT_RUM_gap": "0.5mm이상",
      "RUM_RLM_gap": "0.5mm이상",
      "RLM_RB_gap": "0.5mm이상"
    },
    "bridge_detected": false,
    "bridge_details": "없음",
    "blob_detected": false,
    "blob_severity": "없음",
    "splash": "없음",
    "cold_solder": "없음",
    "void": "없음"
  },
  "alignment_analysis": {
    "horizontal_alignment": "완벽중심",
    "vertical_alignment": "완벽중심",
    "rotation": "0도",
    "rotation_direction": "없음",
    "horizontal_error_mm": 0.0,
    "vertical_error_mm": 0.0,
    "leads_linearity_left": "완벽",
    "leads_linearity_right": "완벽",
    "leads_height_equal": true,
    "severe_misalignment_detected": false,
    "misalignment_description": "없음"
  },
  "overall_assessment": {
    "initial_judgment": "NORMAL",
    "confidence_level": "높음",
    "confidence_percentage": 95,
    "defects_summary": "결함 없음. 모든 항목 정상.",
    "critical_issues": [],
    "secondary_issues": [],
    "recommendations": "정상 제품. 납품 가능."
  }
}"""

    if image_analysis:
        prompt += f"\n\n[제공된 이미지 기초 분석]\n{image_analysis}\n\n위 정보를 기반으로 위 6단계 프로세스에 따라 극도로 상세하게 분석하세요."
    
    prompt += f"\n\n[JSON 응답]\n{json_template}"
    
    return prompt


# =========================
# THINK PROMPT (STEP 2)
# =========================
def build_think_prompt(judge_results: Dict[str, Any]) -> str:
    """
    THINK 단계: 깊이있는 분석 및 근본 원인 분석 (Luxia 32B용)
    ~2500 토큰 규모의 심화 분석
    """
    
    prompt = """
[역할]
당신은 반도체 제조 공정 전문가이자 품질 분석가입니다.
Judge 단계의 상세한 분석 결과를 받아, 깊이있는 해석과 근본원인을 분석합니다.

[분석 프레임워크]

【구간 1】 결함 종합 평가

1-1. 검출된 결함 종류
  • 패키지 손상: 있음/없음
    - 존재한다면: 타입(크랙/파손/벗겨짐), 위치, 심각도
    - 신뢰성 영향: 응력집중점으로 작용 → 신뢰성 저하
  
  • 리드 결손/단선: 있음/없음
    - 존재한다면: 위치(좌/우, 상/중/하), 개수
    - 전기적 영향: 회로 오픈(Open Circuit) → 치명적
  
  • 리드 심한휨/접촉: 있음/없음
    - 존재한다면: 위치, 휨의 정도(각도), 리드간 간격
    - 전기적 영향: 쇼트(Short Circuit) 위험 → 즉시 불량 처리
  
  • 솔더 브리지/뭉침: 있음/없음
    - 존재한다면: 위치(어느 핀들 사이), 크기, 형태
    - 전기적 영향: 핀 간 쇼트 → 치명적 결함
  
  • 정렬 오차: 있음/없음
    - 존재한다면: 오차거리, 회전각도, 방향
    - 조립 품질: 공정 안정성 지표

1-2. 결함 심각도 종합 점수 (0~10점)
  • 단일 치명적 결함 (패키지손상, 리드결손, 솔더브리지): 9점
  • 다중 결함: 8~10점 (개수에 따라)
  • 단일 주요 결함 (리드휨/접촉, 정렬오차): 6~8점
  • 미세한 결함: 3~5점
  • 결함 없음: 0점

1-3. 신뢰성 평가
  • 즉각 불량 결함 여부: 존재/미존재
  • 신뢰성 마진: 매우충분 / 충분 / 경계 / 부족 / 위험

【구간 2】 근본 원인 분석

2-1. 패키지 손상의 경우
  원인 추론:
  • 생산 라인: 기계적 손상 → 핸들링 장비 검사 필요
  • 운송: 충격 손상 → 포장 강화 필요
  • 응력: 열응력/기계응력 → 공정 온도 검토
  • 재질 결함: 원재료 불량 → 공급업체 검사
  
  권장 조치:
  • 즉시 불량 처리
  • 생산 라인 (시간대/장비) 확인
  • 동일 배치 제품 재점검

2-2. 리드 결손/단선의 경우
  원인 추론:
  • 리드 와이어 단절: 피크 앤 플레이스 장비 검사
  • 과도한 리딩 부하: 센서 스프링 압력 조정
  • 빠른 냉각: 온도 곡선 재조정
  
  권장 조치:
  • 즉시 불량 처리
  • 픽앤플레이스 헤드 정렬 및 압력 검사
  • 온도 프로파일 재검증

2-3. 리드 심한휨 또는 접촉의 경우
  원인 추론:
  • 픽 오류: 로봇 그리퍼 손상 → 정비 필요
  • 플레이스 오류: 보드 고정 불량 → 설정 검토
  • 냉각 과정: 급냉 → 온도 곡선 조정
  
  권장 조치:
  • 불량 처리 (쇼트 위험)
  • 해당 시간대 생산 제품 100% 재검사
  • 로봇 그리퍼 및 센싱 검사

2-4. 솔더 브리지/뭉침의 경우
  원인 추론:
  • 과다 리플로우: 불꽃 온도 높음 → 온도 하강
  • 솔더 페이스트 과다: 적용량 감소 필요
  • 부품 오버래핑: 피치 조정
  • PCB 열용량 과다: 보드 설계 검토
  
  권장 조치:
  • 불량 처리
  • 솔더 페이스트 적용량 재설정
  • 리플로우 오븐 온도 곡선 검증
  • 해당 배치 제품 100% 검사

2-5. 정렬 오차의 경우
  원인 추론:
  • 카메라 정렬 오차: 광학 센서 교정 필요
  • 보드 고정 불량: 지그 파손 확인
  • 기울어진 보드: 정렬 알고리즘 검토
  
  권장 조치:
  • 오차가 명시된 사양 초과시 불량
  • 픽앤플레이스 기계 정렬 재교정
  • 센서 성능 테스트

【구간 3】 도메인 지식 기반 신뢰성 분석

3-1. 반도체 신뢰성 메커니즘
  
  가장 위험한 결함 (즉시 불량 처리):
  ① 솔더 브리지: 핀 간 쇼트 → 과전류 → 화재/연기 위험
  ② 리드 완전결손: 회로 오픈 → 전혀 작동 안함
  ③ 패키지 대형크랙: 습도 침투 → 고장
  
  매우 위험한 결함 (불량 처리):
  ④ 리드 심한휨 (< 0.5mm 간격): 비정상 접촉 위험
  ⑤ 리드 단선 (부러짐): 신뢰성 저하
  
  중간 위험 (사양에 따라 결정):
  ⑥ 미세 솔더 언더필: 기계적 강도 저하
  ⑦ 미세 정렬 오차 (< 1mm): 기능상 영향 없지만 신뢰성 주의
  
  낮은 위험 (무시 가능):
  ⑧ 미세 색상 변화
  ⑨ 글자 미세 흐림

3-2. 신뢰성 지표 (Reliability Index)
  = (최고심각도) × (결함개수) × (위치중요도) / (최대점수)
  
  지표 > 0.7: 매우 위험 (불량 처리)
  지표 0.5~0.7: 위험 (불량 처리 권고)
  지표 0.3~0.5: 경계 (추가 검사 필요)
  지표 < 0.3: 정상

【구간 4】 최종 판정

4-1. 판정 기준
  
  ABNORMAL (불량)의 조건:
  ✗ 솔더 브리지 1개 이상
  ✗ 리드 결손 1개 이상
  ✗ 리드 간 접촉 (0.5mm 미만)
  ✗ 패키지 대형 크랙 (> 3mm)
  ✗ 심각한 정렬 오차 (> 2mm) + 다른 결함
  
  NORMAL (정상)의 조건:
  ✓ 위 모든 조건을 만족하지 않음
  ✓ 이미지 질이 충분함 (점수 > 6)

4-2. 최종 신뢰도
  = (이미지질점수 × 10) + (결함확실성점수)
  최대 100점, 70점 이상이면 신뢰도 "높음"

【구간 5】 추가 정보

5-1. 위험 신호 (Red Flags)
  • 매우 낮은 이미지 질 → 재촬영 권고
  • 모호한 결함 → 영상 확대 분석 필요
  • 예상치 못한 결함 조합 → 공정 라인 점검

5-2. 추가 검사 권고
  • 초음파 검사 (솔더 보이드 확인)
  • 열화상 이미징 (열 문제 확인)
  • 전자 검사 (기능 검증)

[최종 JSON 응답 형식]
"""

    json_template = """{
  "defect_summary": {
    "total_defects_detected": 0,
    "critical_defects": [],
    "major_defects": [],
    "minor_defects": [],
    "defect_severity_score": 0.0
  },
  "root_cause_analysis": {
    "primary_cause": "없음",
    "secondary_causes": [],
    "process_area_affected": "없음",
    "equipment_likely_responsible": "없음"
  },
  "reliability_assessment": {
    "reliability_index": 0.0,
    "reliability_level": "정상",
    "failure_mode_potential": "없음",
    "critical_risk": false,
    "margin_status": "충분"
  },
  "domain_knowledge_analysis": {
    "semiconductor_reliability_concern": "없음",
    "manufacturing_process_implications": "정상 생산 범위",
    "field_failure_probability": "매우낮음"
  },
  "final_judgment": {
    "verdict": "NORMAL",
    "confidence_score": 95,
    "confidence_reason": "모든 항목 정상, 결함 없음",
    "recommended_action": "납품 가능"
  },
  "quality_assurance_notes": "추가 조치 없음"
}"""

    prompt += f"\n\n[Judge 단계 결과]\n{json.dumps(judge_results, ensure_ascii=False, indent=2)}"
    prompt += f"\n\n[JSON 응답]\n{json_template}"
    
    return prompt


# =========================
# API CALL HELPER
# =========================
def call_llm(model: str, messages: List[Dict], timeout: int = 120) -> str:
    """
    Luxia LLM API 호출
    """
    url = BRIDGE_URL.format(model=model)
    payload = {
        "model": model,
        "messages": messages,
        "stream": False
    }
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=timeout)
        
        if response.status_code != 200:
            raise RuntimeError(f"API Error: {response.status_code} - {response.text[:200]}")
        
        return response.json()["choices"][0]["message"]["content"].strip()
    
    except Exception as e:
        print(f"❌ LLM API 호출 실패: {e}")
        return "{}"


def extract_json(response: str) -> Dict:
    """
    LLM 응답에서 JSON 추출
    """
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
# MAIN PIPELINE
# =========================
def analyze_image(image_url: str) -> Dict[str, Any]:
    """
    이미지 분석 전체 파이프라인
    1. JUDGE: 상세 이미지 분석 (Luxia 32B)
    2. THINK: 근본 원인 분석 (Luxia 32B)
    """
    
    print(f"\n[분석 시작] {image_url}")
    
    # === STEP 1: JUDGE ===
    print("  📸 [JUDGE] Judge 단계 분석 중...")
    judge_prompt = build_judge_prompt()
    
    judge_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": judge_prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }
    ]
    
    judge_response = call_llm(MODEL_JUDGE, judge_messages)
    judge_results = extract_json(judge_response)
    print(f"  ✓ Judge 완료")
    
    # === STEP 2: THINK ===
    print("  🧠 [THINK] 깊이있는 분석 중...")
    think_prompt = build_think_prompt(judge_results)
    
    think_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": think_prompt}
    ]
    
    think_response = call_llm(MODEL_THINK, think_messages)
    think_results = extract_json(think_response)
    print(f"  ✓ Think 완료")
    
    # === 최종 판정 ===
    final_judgment = think_results.get("final_judgment", {}).get("verdict", "UNKNOWN")
    confidence = think_results.get("final_judgment", {}).get("confidence_score", 50)
    
    # 0: NORMAL, 1: ABNORMAL
    final_label = 0 if final_judgment == "NORMAL" else 1
    
    return {
        "image_url": image_url,
        "judge_results": judge_results,
        "think_results": think_results,
        "final_label": final_label,
        "final_judgment": final_judgment,
        "confidence": confidence
    }


# =========================
# TEST
# =========================
if __name__ == "__main__":
    print("=" * 80)
    print("Enhanced Integrated Agent - Luxia 32B with Ultra-Detailed Prompts")
    print("=" * 80)
    
    # 테스트 이미지 (필요시 수정)
    test_image = "https://example.com/test_image.jpg"
    
    # 프롬프트 미리보기
    print("\n[프롬프트 미리보기]")
    print("=" * 40)
    
    judge_prompt = build_judge_prompt()
    print(f"Judge 프롬프트 길이: {len(judge_prompt)} 토큰 (약)")
    print("\n[처음 500자]")
    print(judge_prompt[:500])
    print("\n[마지막 500자]")
    print(judge_prompt[-500:])
    
    print("\n" + "=" * 80)
    print("✓ Enhanced Agent 준비 완료!")
    print("=" * 80)
