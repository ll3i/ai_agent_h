# 🔄 Luxia AI Agent 워크플로우 다이어그램 완전 가이드

## 📋 개요

Luxia AI Agent 시스템의 모든 워크플로우를 시각적으로 정리한 완전 가이드입니다.

---

## 🎯 목차

1. [전체 시스템 아키텍처](#1-전체-시스템-아키텍처)
2. [Multi-Model Agent 워크플로우](#2-multi-model-agent-워크플로우)
3. [Luxia Enhanced Agent 워크플로우](#3-luxia-enhanced-agent-워크플로우)
4. [Fusion Agent 워크플로우](#4-fusion-agent-워크플로우)
5. [Final Omni-Agent 워크플로우](#5-final-omni-agent-워크플로우)
6. [실행 스크립트 워크플로우](#6-실행-스크립트-워크플로우)
7. [데이터 플로우](#7-데이터-플로우)

---

## 1. 전체 시스템 아키텍처

### 1.1 레이어 구조

```
┌─────────────────────────────────────────────────────────────┐
│                  Luxia AI Agent 전체 시스템                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Layer 1: 실행 스크립트 (Entry Points)              │     │
│  │ - run_full_analysis.py (대회 제출용)               │     │
│  │ - run_multi_agent_test.py (검증용)                 │     │
│  └────────────┬───────────────────────────────────────┘     │
│               ↓                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Layer 2: 통합 Agent 시스템                         │     │
│  │ - final_omni_agent.py (최종 통합) ⭐               │     │
│  │ - multi_agent.py (Multi-Agent 로직)                │     │
│  └────────────┬───────────────────────────────────────┘     │
│               ↓                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Layer 3: 핵심 Agent 로직                           │     │
│  │ ┌──────────────────┐  ┌──────────────────────┐    │     │
│  │ │ Vision Agent     │  │ Enhanced Agent       │    │     │
│  │ │ - jtav_triple    │  │ - RAG (Knowledge)    │    │     │
│  │ │ - fusion         │  │ - Report Gen         │    │     │
│  │ │ - multi_model    │  │ - Ensemble Rerank    │    │     │
│  │ └──────────────────┘  └──────────────────────┘    │     │
│  └────────────┬───────────────────────────────────────┘     │
│               ↓                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Layer 4: 공통 컴포넌트                              │     │
│  │ - roi_cropper.py (이미지 처리)                     │     │
│  │ - saltlux_client.py (API 호출)                     │     │
│  │ - config.py (설정 관리)                            │     │
│  │ - utils.py (유틸리티)                              │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 컴포넌트 간 의존성

```
run_full_analysis.py
    ↓
final_omni_agent.py
    ├── jtav_triple_vision.py (Vision Agent - 74%)
    │   ├── roi_cropper.py (이미지 크롭)
    │   │   ├── crop_body_roi() → Body Zoom
    │   │   └── crop_lead_roi() → Lead Zoom
    │   ├── saltlux_client.py (Luxia API)
    │   └── config.py (모델 설정)
    │
    └── luxia_enhanced_agent.py (Enhanced Features)
        ├── DefectKnowledgeBase (RAG)
        ├── DefectReportGenerator (보고서)
        └── EnsembleReranker (앙상블)
```

---

## 2. Multi-Model Agent 워크플로우

### 2.1 4단계 파이프라인

```
┌─────────────────────────────────────────────────────────────┐
│        Multi-Model Agent: Judge-Think-Act-Verify            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  START: classify_multi_model_agent(img_url)                 │
│    ↓                                                         │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Step 1: JUDGE (관찰)                             │       │
│  │ Model: gpt-4o-mini                               │       │
│  │ Input: 이미지 URL/Base64                         │       │
│  │ Output: obs = {                                  │       │
│  │   "package_damage": False,                       │       │
│  │   "lead_missing_or_broken": True,                │       │
│  │   "lead_severe_bend": False,                     │       │
│  │   "solder_bridge": False,                        │       │
│  │   "misalignment_severe": False                   │       │
│  │ }                                                │       │
│  └──────────────┬───────────────────────────────────┘       │
│                 ↓                                            │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Step 2: THINK (추론)                             │       │
│  │ Model: claude-3.5-sonnet                         │       │
│  │ Input: obs (관찰 결과)                           │       │
│  │ Process:                                         │       │
│  │   1. 결함 개수 계산: total_defects = 1           │       │
│  │   2. 결함 목록 추출: defect_items = [...]        │       │
│  │   3. 심각도 점수: severity_score = 0.95          │       │
│  │   4. 치명적 결함: has_critical_defect = True     │       │
│  │   5. 신뢰도 추정: confidence_level = "VERY_HIGH" │       │
│  │ Output: reasoning = {                            │       │
│  │   'total_defects': 1,                            │       │
│  │   'severity_score': 0.95,                        │       │
│  │   'has_critical_defect': True,                   │       │
│  │   'confidence_level': 'VERY_HIGH',               │       │
│  │   'analysis': "LLM 분석 결과..."                 │       │
│  │ }                                                │       │
│  └──────────────┬───────────────────────────────────┘       │
│                 ↓                                            │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Step 3: ACT (의사결정)                           │       │
│  │ Model: gpt-3.5-turbo                             │       │
│  │ Input: reasoning                                 │       │
│  │ Decision Logic:                                  │       │
│  │   IF has_critical_defect:                        │       │
│  │     → label = 1 (Abnormal)                       │       │
│  │     → uncertain = False                          │       │
│  │   ELIF total_defects >= 2:                       │       │
│  │     → label = 1 (Abnormal)                       │       │
│  │     → uncertain = False                          │       │
│  │   ELIF total_defects >= 1:                       │       │
│  │     → label = 1 (Abnormal)                       │       │
│  │     → uncertain = True (재검토 필요)             │       │
│  │   ELSE:                                          │       │
│  │     → label = 0 (Normal)                         │       │
│  │     → uncertain = True (재검토 필요)             │       │
│  │ Output: (label=1, uncertain=False)               │       │
│  └──────────────┬───────────────────────────────────┘       │
│                 ↓                                            │
│  ┌──────────────────────────────────────────────────┐       │
│  │ 재검토 필요 여부 판단                            │       │
│  │ IF uncertain AND NOT has_critical_defect:        │       │
│  │   → 재검토 실행 (Step 1~3 반복, strict=True)    │       │
│  │ ELSE:                                            │       │
│  │   → 바로 검증 단계로                             │       │
│  └──────────────┬───────────────────────────────────┘       │
│                 ↓                                            │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Step 4: VERIFY (검증)                            │       │
│  │ Model: gpt-4o                                    │       │
│  │ Input: label, reasoning, is_review               │       │
│  │ Validation Checklist:                            │       │
│  │   1. 판단의 논리적 타당성 확인                   │       │
│  │   2. 도메인 지식과의 일치도 검증                 │       │
│  │   3. 놓친 결함 가능성 평가                       │       │
│  │   4. 신뢰도 점수 재계산                          │       │
│  │ Confidence Boost:                                │       │
│  │   IF is_review AND label == 1:                   │       │
│  │     final_confidence += 0.05 (max 0.99)          │       │
│  │ Output: {                                        │       │
│  │   'verified': True,                              │       │
│  │   'decision': 1,                                 │       │
│  │   'confidence': 0.99,                            │       │
│  │   'verification_detail': "...",                  │       │
│  │   'reasoning': "..."                             │       │
│  │ }                                                │       │
│  └──────────────┬───────────────────────────────────┘       │
│                 ↓                                            │
│  RETURN: {                                                   │
│    'prediction': 1,                                          │
│    'confidence': 0.99,                                       │
│    'verified': True,                                         │
│    'iterations': 1 or 2,                                     │
│    'models_used': ['gpt-4o-mini', 'claude', 'gpt-3.5', 'gpt-4o'] │
│  }                                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 재검토 메커니즘

```
Judge → Think → Act
         ↓
    uncertain? ───No──→ Verify → END
         ↓Yes
         ↓
    has_critical? ───Yes──→ Verify → END
         ↓No
         ↓
    [재검토 시작]
         ↓
    Judge(strict=True) → Think → Act
         ↓
    Verify(is_review=True) → END
```

### 2.3 신뢰도 추정 로직

```python
def _estimate_confidence(defect_count, has_critical):
    ┌─────────────────────────────────────┐
    │ IF has_critical_defect:             │
    │   → VERY_HIGH (99%)                 │
    ├─────────────────────────────────────┤
    │ ELIF defect_count >= 2:             │
    │   → HIGH (95%)                      │
    ├─────────────────────────────────────┤
    │ ELIF defect_count == 1:             │
    │   → MEDIUM (70%)                    │
    ├─────────────────────────────────────┤
    │ ELSE (defect_count == 0):           │
    │   → LOW (60%)                       │
    └─────────────────────────────────────┘
```

---

## 3. Luxia Enhanced Agent 워크플로우

### 3.1 강화 파이프라인

```
┌─────────────────────────────────────────────────────────────┐
│           Luxia Enhanced Agent: 3단계 강화 시스템            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  START: process_complete(img_url, analysis, model_results)  │
│    ↓                                                         │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Step 1: Knowledge Agent (RAG)                    │       │
│  │ enhance_decision()                               │       │
│  │                                                  │       │
│  │ Input:                                           │       │
│  │   - decision = 1                                 │       │
│  │   - confidence = 0.85                            │       │
│  │   - description = "리드 연결 문제"               │       │
│  │                                                  │       │
│  │ Process:                                         │       │
│  │   1. similarity_search(description, top_k=3)     │       │
│  │      ↓                                           │       │
│  │   2. 키워드 추출: {"리드", "연결", "문제"}       │       │
│  │      ↓                                           │       │
│  │   3. Jaccard Similarity 계산:                    │       │
│  │      case_002: 0.75 (솔더 브리지)                │       │
│  │      case_005: 0.45 (리드 휨)                    │       │
│  │      case_001: 0.30 (패키지 크랙)                │       │
│  │      ↓                                           │       │
│  │   4. boost_confidence(decision, cases):          │       │
│  │      matching_count = 2/3 (같은 판정)            │       │
│  │      weighted_sum = 0.75 + 0.45 = 1.20           │       │
│  │      total_sum = 0.75 + 0.45 + 0.30 = 1.50       │       │
│  │      match_rate = 1.20 / 1.50 = 0.80             │       │
│  │      boost = 0.10 + (0.80 × 0.20) = 0.26         │       │
│  │      ↓                                           │       │
│  │   5. enhanced_confidence = min(0.85 + 0.26, 0.99)│       │
│  │                          = 0.99                  │       │
│  │                                                  │       │
│  │ Output: (decision=1, enhanced_confidence=0.99)   │       │
│  └──────────────┬───────────────────────────────────┘       │
│                 ↓                                            │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Step 2: Ensemble Reranker (앙상블)               │       │
│  │ rerank_decisions()                               │       │
│  │                                                  │       │
│  │ Input:                                           │       │
│  │   model_results = [                              │       │
│  │     {'model': 'gpt-4o-mini', 'decision': 1, 'confidence': 0.85}, │
│  │     {'model': 'claude', 'decision': 1, 'confidence': 0.90},      │
│  │     {'model': 'gpt-3.5', 'decision': 0, 'confidence': 0.75}      │
│  │   ]                                              │       │
│  │                                                  │       │
│  │ Process:                                         │       │
│  │   1. Model Weights 적용:                         │       │
│  │      gpt-4o-mini: 1.0                            │       │
│  │      claude: 0.9                                 │       │
│  │      gpt-3.5: 0.7                                │       │
│  │      ↓                                           │       │
│  │   2. Weighted Score 계산:                        │       │
│  │      score_0 = 0.7 × 0.75 = 0.525                │       │
│  │      score_1 = 1.0 × 0.85 + 0.9 × 0.90 = 1.66    │       │
│  │      total_weight = 1.0 + 0.9 + 0.7 = 2.6        │       │
│  │      ↓                                           │       │
│  │   3. 정규화:                                     │       │
│  │      final_confidence_0 = 0.525 / 2.6 = 0.20     │       │
│  │      final_confidence_1 = 1.66 / 2.6 = 0.64      │       │
│  │      ↓                                           │       │
│  │   4. 최종 판정:                                  │       │
│  │      decision = 1 (0.64 > 0.20)                  │       │
│  │      confidence = 0.64                           │       │
│  │                                                  │       │
│  │ Output: {                                        │       │
│  │   'decision': 1,                                 │       │
│  │   'confidence': 0.64,                            │       │
│  │   'score_0': 0.20,                               │       │
│  │   'score_1': 0.64,                               │       │
│  │   'method': 'weighted_ensemble'                  │       │
│  │ }                                                │       │
│  └──────────────┬───────────────────────────────────┘       │
│                 ↓                                            │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Step 3: Report Generator (보고서 생성)           │       │
│  │ generate_full_report()                           │       │
│  │                                                  │       │
│  │ Input:                                           │       │
│  │   - analysis_result (원본 분석)                  │       │
│  │   - model_results (다중 모델 판정)               │       │
│  │   - final_decision (1)                           │       │
│  │                                                  │       │
│  │ Process:                                         │       │
│  │   1. _format_narrative():                        │       │
│  │      이미지 ID, 시간, 결함, 심각도, 신뢰도       │       │
│  │      ↓                                           │       │
│  │   2. _template_report():                         │       │
│  │      [1] 발견된 결함                             │       │
│  │      [2] 심각도 평가                             │       │
│  │      [3] 원인 분석                               │       │
│  │      [4] 권장 조치                               │       │
│  │      [5] 신뢰도                                  │       │
│  │                                                  │       │
│  │ Output: professional_report (string)             │       │
│  └──────────────┬───────────────────────────────────┘       │
│                 ↓                                            │
│  RETURN: {                                                   │
│    'final_decision': 1,                                      │
│    'confidence': 0.99,                                       │
│    'report': "...",                                          │
│    'enhancements_applied': [                                 │
│      'semantic_search',                                      │
│      'text_generation',                                      │
│      'reranking'                                             │
│    ]                                                         │
│  }                                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Fusion Agent 워크플로우

### 4.1 3단계 Adaptive 전략

```
┌─────────────────────────────────────────────────────────────┐
│          Fusion Agent: Balanced → Sensitive → Precision      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  START: classify_fusion(image_path)                         │
│    ↓                                                         │
│  ┌──────────────────────────────────────────────────┐       │
│  │ 이미지 준비 (Triple Vision)                      │       │
│  │ _prepare_images()                                │       │
│  │                                                  │       │
│  │ Original Image                                   │       │
│  │   ├─→ Full View (전체 맥락)                      │       │
│  │   ├─→ crop_body_roi() → Body Zoom (패키지 확대)  │       │
│  │   └─→ crop_lead_roi() → Lead Zoom (리드 확대)    │       │
│  │                                                  │       │
│  │ Output: (full_b64, body_b64, lead_b64)           │       │
│  └──────────────┬───────────────────────────────────┘       │
│                 ↓                                            │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Step 1: Balanced Check (균형 잡힌 기본 분석)     │       │
│  │ step1_balanced_check()                           │       │
│  │                                                  │       │
│  │ Input: 3개 이미지 + BALANCED_PROMPT              │       │
│  │                                                  │       │
│  │ Prompt 전략:                                     │       │
│  │   - 5개 결함 분류 (component_missing,           │       │
│  │     lead_connectivity_fail, body_broken,         │       │
│  │     posture_bad, rotation_severe)                │       │
│  │   - JSON 출력 강제                               │       │
│  │   - 배경 노이즈 무시 가이드                      │       │
│  │                                                  │       │
│  │ Output: {                                        │       │
│  │   "component_missing": False,                    │       │
│  │   "lead_connectivity_fail": True,                │       │
│  │   "body_broken_severe": False,                   │       │
│  │   "posture_bad": False,                          │       │
│  │   "rotation_severe": False                       │       │
│  │ }                                                │       │
│  │                                                  │       │
│  │ 결함 목록 추출: defects = ["lead_connectivity_fail"] │       │
│  │ 결함 개수: len(defects) = 1                      │       │
│  └──────────────┬───────────────────────────────────┘       │
│                 ↓                                            │
│          결함 개수 평가                                      │
│                 ↓                                            │
│  ┌──────────┬──────────┬──────────┐                         │
│  │ 0개      │ 1개      │ 2개+     │                         │
│  │ (Normal) │ (경계)   │ (다중)   │                         │
│  └────┬─────┴────┬─────┴────┬─────┘                         │
│       ↓          ↓          ↓                               │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Step 2: Sensitive Recheck (FN 방지)              │       │
│  │ (0개 결함인 경우에만 실행)                        │       │
│  │ step2_sensitive_recheck()                        │       │
│  │                                                  │       │
│  │ Input: 3개 이미지 + SENSITIVE_PROMPT              │       │
│  │                                                  │       │
│  │ Prompt 전략:                                     │       │
│  │   - "BE AGGRESSIVE!" 모드                        │       │
│  │   - 불확실하면 TRUE 판정                         │       │
│  │   - 놓친 결함 찾기                               │       │
│  │   - RULE: ANYTHING suspicious → Mark TRUE        │       │
│  │                                                  │       │
│  │ Output: {                                        │       │
│  │   "lead_connectivity_fail": False,               │       │
│  │   "any_defect_found": False                      │       │
│  │ }                                                │       │
│  │                                                  │       │
│  │ IF any_defect_found:                             │       │
│  │   → RETURN (1, "Defect found in recheck")        │       │
│  │ ELSE:                                            │       │
│  │   → RETURN (0, "No defects (double-checked)")    │       │
│  └──────────────────────────────────────────────────┘       │
│       ↑                               ↓                     │
│       │                          (다중 결함)                 │
│       │                               ↓                     │
│       │                    즉시 RETURN (1, "Multiple defects") │
│       │                                                      │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Step 3: Precision Verify (FP 방지)               │       │
│  │ (1개 결함인 경우에만 실행)                        │       │
│  │ step3_precision_verify()                         │       │
│  │                                                  │       │
│  │ Input:                                           │       │
│  │   - 3개 이미지                                   │       │
│  │   - PRECISION_PROMPT.format(defect_type)         │       │
│  │   - defect_type = "lead_connectivity_fail"       │       │
│  │                                                  │       │
│  │ Prompt 전략:                                     │       │
│  │   - "BE STRICT!" 모드                            │       │
│  │   - 실제 결함 vs 그림자/노이즈 구분              │       │
│  │   - REAL DEFECT: Physical gap, break, damage    │       │
│  │   - SHADOW/NOISE: Dark area, continuous lead    │       │
│  │                                                  │       │
│  │ Output: {                                        │       │
│  │   "is_real_defect": True,                        │       │
│  │   "reason": "Physical gap visible in lead"       │       │
│  │ }                                                │       │
│  │                                                  │       │
│  │ IF is_real_defect:                               │       │
│  │   → RETURN (1, "Verified defect: ...")           │       │
│  │ ELSE:                                            │       │
│  │   → RETURN (0, "Rejected as shadow: ...")        │       │
│  └──────────────────────────────────────────────────┘       │
│                 ↓                                            │
│  RETURN: (label, reason)                                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 의사결정 트리

```
                  classify_fusion()
                         │
                    [이미지 준비]
                         │
              ┌──────────┴──────────┐
              │  Step 1: Balanced   │
              │  Triple Vision      │
              └──────────┬──────────┘
                         │
                  [결함 개수 평가]
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    [0개 결함]       [1개 결함]       [2개+ 결함]
        │                │                │
        ↓                ↓                ↓
  ┌─────────┐      ┌─────────┐      ┌──────────┐
  │ Step 2: │      │ Step 3: │      │즉시 판정 │
  │Sensitive│      │Precision│      │ label=1  │
  │ Recheck │      │ Verify  │      └──────────┘
  └────┬────┘      └────┬────┘            ↓
       │                │              RETURN
       ↓                ↓              (1, "Multiple
  [재검사 결과]    [검증 결과]          defects")
       │                │
  ┌────┴────┐      ┌────┴────┐
  │결함 발견?│      │실제결함?│
  └────┬────┘      └────┬────┘
   Yes │ No         Yes │ No
       │                │
  ┌────┴────┐      ┌────┴────┐
  │ label=1 │      │ label=1 │
  │  or 0   │      │  or 0   │
  └────┬────┘      └────┬────┘
       │                │
       └────────┬───────┘
                ↓
           RETURN (label, reason)
```

---

## 5. Final Omni-Agent 워크플로우

### 5.1 3대 Agent 통합

```
┌─────────────────────────────────────────────────────────────┐
│    Final Omni-Agent: Vision + Knowledge + Report 통합        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  START: classify_omni_final(image_path)                     │
│    ↓                                                         │
│  omni_agent.analyze(image_path)                             │
│    ↓                                                         │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Agent 1: Vision Agent (74% 최고 정확도)          │       │
│  │ self.vision_agent(image_path)                    │       │
│  │ = classify_jtav_triple(image_path)               │       │
│  │                                                  │       │
│  │ 내부 실행:                                       │       │
│  │   Judge (Luxia 32B)                              │       │
│  │     ↓                                            │       │
│  │   Think (Luxia 32B)                              │       │
│  │     ↓                                            │       │
│  │   Act (Luxia 13B)                                │       │
│  │     ↓                                            │       │
│  │   Verify (Luxia 32B)                             │       │
│  │     +                                            │       │
│  │   Triple Vision (Full + Body + Lead)             │       │
│  │                                                  │       │
│  │ Output:                                          │       │
│  │   label = 1                                      │       │
│  │   reason = "Lead connectivity fail detected"     │       │
│  └──────────────┬───────────────────────────────────┘       │
│                 ↓                                            │
│           (label=1, reason="...")                           │
│                 ↓                                            │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Agent 2: Knowledge Agent (RAG)                   │       │
│  │ self.knowledge_agent.similarity_search()         │       │
│  │                                                  │       │
│  │ Input:                                           │       │
│  │   query = "Lead connectivity fail detected"      │       │
│  │   top_k = 2                                      │       │
│  │                                                  │       │
│  │ Process:                                         │       │
│  │   1. 키워드 추출:                                │       │
│  │      {"lead", "connectivity", "fail", "detected"}│       │
│  │      ↓                                           │       │
│  │   2. 5개 사례 데이터베이스 검색:                 │       │
│  │      case_001: 패키지 크랙 (severity 0.95)       │       │
│  │      case_002: 솔더 브리지 (severity 0.90)       │       │
│  │      case_003: 소자 위치 이탈 (severity 0.80)    │       │
│  │      case_004: 정상 사례 (severity 0.10)         │       │
│  │      case_005: 경미한 휨 (severity 0.40)         │       │
│  │      ↓                                           │       │
│  │   3. Jaccard Similarity 계산:                    │       │
│  │      case_002: score = 0.65                      │       │
│  │      case_005: score = 0.45                      │       │
│  │      case_001: score = 0.25                      │       │
│  │      ...                                         │       │
│  │      ↓                                           │       │
│  │   4. Top 2 반환:                                 │       │
│  │      [                                           │       │
│  │        {'case': case_002, 'similarity': 0.65},  │       │
│  │        {'case': case_005, 'similarity': 0.45}   │       │
│  │      ]                                           │       │
│  │                                                  │       │
│  │ Output: similar_cases (top 2)                    │       │
│  └──────────────┬───────────────────────────────────┘       │
│                 ↓                                            │
│           similar_cases = [...]                             │
│                 ↓                                            │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Context 추가 여부 판단                           │       │
│  │                                                  │       │
│  │ relevant_case = similar_cases[0]                 │       │
│  │   = {'case': case_002, 'similarity_score': 0.65}│       │
│  │                                                  │       │
│  │ IF similarity_score > 0.1:                       │       │
│  │   kb_context = f" (Similar to {case['id']}:     │       │
│  │                   {case['description']})"        │       │
│  │   = " (Similar to case_002: 두 개의 리드 간     │       │
│  │      솔더 브리지 형성, 전기적 단락 위험.         │       │
│  │      lead_connectivity_fail 감지됨.)"            │       │
│  │ ELSE:                                            │       │
│  │   kb_context = ""                                │       │
│  └──────────────┬───────────────────────────────────┘       │
│                 ↓                                            │
│           kb_context = " (Similar to case_002: ...)"        │
│                 ↓                                            │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Agent 3: Report Agent (컨텍스트 강화)            │       │
│  │ final_reason = reason + kb_context               │       │
│  │                                                  │       │
│  │ Input:                                           │       │
│  │   reason = "Lead connectivity fail detected"     │       │
│  │   kb_context = " (Similar to case_002: ...)"     │       │
│  │                                                  │       │
│  │ Process:                                         │       │
│  │   final_reason = reason + kb_context             │       │
│  │   = "Lead connectivity fail detected             │       │
│  │      (Similar to case_002: 두 개의 리드 간       │       │
│  │       솔더 브리지 형성, 전기적 단락 위험.        │       │
│  │       lead_connectivity_fail 감지됨.)"           │       │
│  │                                                  │       │
│  │ Output: final_reason (enhanced)                  │       │
│  └──────────────┬───────────────────────────────────┘       │
│                 ↓                                            │
│  RETURN: (label=1, final_reason="...")                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 간단한 플로우차트

```
Image → Vision Agent (JTAV + Triple Vision)
           ↓
      (label, reason)
           ↓
        Knowledge Agent (RAG Search)
           ↓
      similar_cases
           ↓
     [similarity > 0.1?]
       Yes ↓    No ↓
        Context  (skip)
           ↓      ↓
     Report Agent
           ↓
   enhanced_reason
           ↓
  RETURN (label, reason)
```

---

## 6. 실행 스크립트 워크플로우

### 6.1 run_full_analysis.py

```
┌─────────────────────────────────────────────────────────────┐
│              run_full_analysis.py 실행 플로우                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  START: python run_full_analysis.py                         │
│    ↓                                                         │
│  main()                                                      │
│    ↓                                                         │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Phase 1: Example Dataset 분석                    │       │
│  │ run_dataset("example_images.csv",                │       │
│  │             "output_example.csv",                 │       │
│  │             "Example Dataset")                    │       │
│  │                                                  │       │
│  │ Process:                                         │       │
│  │   1. CSV 로드 (예: 20개 이미지)                  │       │
│  │      ↓                                           │       │
│  │   2. FOR each row in df:                         │       │
│  │        image_id = row['id']                      │       │
│  │        image_path = row['img_url']               │       │
│  │        ↓                                         │       │
│  │      3. classify_omni_final(image_path)          │       │
│  │         ↓                                        │       │
│  │      4. results.append({'id': id, 'label': label})│       │
│  │        ↓                                         │       │
│  │   5. Save to output_example.csv                  │       │
│  │   6. Save to output_example_detailed.csv         │       │
│  │      (with reason column)                        │       │
│  │                                                  │       │
│  │ Output:                                          │       │
│  │   - output_example.csv (id, label)               │       │
│  │   - output_example_detailed.csv (id, label, reason)│     │
│  └──────────────┬───────────────────────────────────┘       │
│                 ↓                                            │
│  ┌──────────────────────────────────────────────────┐       │
│  │ Phase 2: Test Dataset 분석                       │       │
│  │ run_dataset("test.csv",                          │       │
│  │             "output.csv",                         │       │
│  │             "Test Dataset")                       │       │
│  │                                                  │       │
│  │ Process:                                         │       │
│  │   1. CSV 로드 (100개 이미지)                     │       │
│  │      ↓                                           │       │
│  │   2. FOR each row in df (100번 반복):            │       │
│  │        ↓                                         │       │
│  │      3. classify_omni_final(image_path)          │       │
│  │         ↓                                        │       │
│  │      4. results.append({'id': id, 'label': label})│       │
│  │        ↓                                         │       │
│  │   5. Save to output.csv ⭐ (대회 제출용)         │       │
│  │   6. Save to output_detailed.csv                 │       │
│  │                                                  │       │
│  │ Output:                                          │       │
│  │   - output.csv (id, label) ← 대회 제출          │       │
│  │   - output_detailed.csv (id, label, reason)      │       │
│  └──────────────┬───────────────────────────────────┘       │
│                 ↓                                            │
│  print("🎉 All Analyses Finished!")                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 run_multi_agent_test.py

```
┌─────────────────────────────────────────────────────────────┐
│          run_multi_agent_test.py CLI 워크플로우              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  START: python run_multi_agent_test.py [--mode MODE]        │
│    ↓                                                         │
│  argparse → args.mode                                        │
│    ↓                                                         │
│  ┌────────────────────────────────────────────┐             │
│  │ Mode 선택:                                 │             │
│  │ - example (기본값)                         │             │
│  │ - test                                     │             │
│  │ - both                                     │             │
│  └────────┬───────────────────────────────────┘             │
│           ↓                                                  │
│  ┌────────────────────────────────────────────────┐         │
│  │ IF mode in ["example", "both"]:                │         │
│  │   run_multi_agent_test(                        │         │
│  │     "example_images.csv",                      │         │
│  │     "output_multi_example.csv"                 │         │
│  │   )                                            │         │
│  │                                                │         │
│  │ Process:                                       │         │
│  │   1. Load CSV (20 images)                      │         │
│  │      ↓                                         │         │
│  │   2. FOR each image:                           │         │
│  │        classify_multi_agent(image_path)        │         │
│  │        ↓                                       │         │
│  │      3. results.append({'id': id, 'label': label})│      │
│  │        ↓                                       │         │
│  │   4. Save to output_multi_example.csv          │         │
│  │                                                │         │
│  │ Output: output_multi_example.csv               │         │
│  └────────┬───────────────────────────────────────┘         │
│           ↓                                                  │
│  ┌────────────────────────────────────────────────┐         │
│  │ IF mode in ["test", "both"]:                   │         │
│  │   run_multi_agent_test(                        │         │
│  │     "test.csv",                                │         │
│  │     "output_multi_test.csv"                    │         │
│  │   )                                            │         │
│  │                                                │         │
│  │ Process:                                       │         │
│  │   1. Load CSV (100 images)                     │         │
│  │      ↓                                         │         │
│  │   2. FOR each image:                           │         │
│  │        classify_multi_agent(image_path)        │         │
│  │        ↓                                       │         │
│  │      3. results.append({'id': id, 'label': label})│      │
│  │        ↓                                       │         │
│  │   4. Save to output_multi_test.csv             │         │
│  │                                                │         │
│  │ Output: output_multi_test.csv                  │         │
│  └────────────────────────────────────────────────┘         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. 데이터 플로우

### 7.1 이미지 → 결과 전체 플로우

```
┌─────────────────────────────────────────────────────────────┐
│               전체 시스템 데이터 플로우                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [1] 입력 데이터                                             │
│      test.csv                                                │
│        ↓                                                     │
│      ┌────────────────────────┐                             │
│      │ id          img_url    │                             │
│      ├────────────────────────┤                             │
│      │ TEST_000    ./test/... │                             │
│      │ TEST_001    ./test/... │                             │
│      │ ...         ...        │                             │
│      │ TEST_099    ./test/... │                             │
│      └────────────────────────┘                             │
│              ↓                                               │
│  [2] 이미지 로드 & 전처리                                    │
│      - 파일 읽기: _load_image_bytes()                       │
│      - Base64 인코딩: base64.b64encode()                    │
│      - ROI 크롭: crop_body_roi(), crop_lead_roi()           │
│              ↓                                               │
│      ┌──────────────────────┐                               │
│      │ Full View (base64)   │                               │
│      │ Body Zoom (base64)   │                               │
│      │ Lead Zoom (base64)   │                               │
│      └──────────────────────┘                               │
│              ↓                                               │
│  [3] Vision Agent 분석                                       │
│      classify_jtav_triple() / classify_fusion()             │
│              ↓                                               │
│      Judge → Think → Act → Verify                           │
│              ↓                                               │
│      ┌──────────────────────┐                               │
│      │ label = 0 or 1       │                               │
│      │ reason = "..."       │                               │
│      └──────────────────────┘                               │
│              ↓                                               │
│  [4] Knowledge Agent 강화 (선택적)                           │
│      similarity_search(reason)                              │
│              ↓                                               │
│      ┌──────────────────────┐                               │
│      │ similar_cases = [...] │                              │
│      │ kb_context = "..."   │                               │
│      └──────────────────────┘                               │
│              ↓                                               │
│  [5] Report Agent (선택적)                                   │
│      enhanced_reason = reason + kb_context                  │
│              ↓                                               │
│      ┌──────────────────────┐                               │
│      │ final_label = 0/1    │                               │
│      │ final_reason = "..." │                               │
│      └──────────────────────┘                               │
│              ↓                                               │
│  [6] 결과 수집                                               │
│      results.append({                                        │
│        'id': 'TEST_000',                                     │
│        'label': 1,                                           │
│        'reason': "..."                                       │
│      })                                                      │
│              ↓                                               │
│  [7] CSV 저장                                                │
│      ┌──────────────────────────────┐                       │
│      │ output.csv (대회 제출용)     │                       │
│      ├──────────────────────────────┤                       │
│      │ id          label            │                       │
│      ├──────────────────────────────┤                       │
│      │ TEST_000    1                │                       │
│      │ TEST_001    0                │                       │
│      │ ...         ...              │                       │
│      │ TEST_099    1                │                       │
│      └──────────────────────────────┘                       │
│      +                                                       │
│      ┌──────────────────────────────────────┐               │
│      │ output_detailed.csv (디버깅용)       │               │
│      ├──────────────────────────────────────┤               │
│      │ id       label  reason               │               │
│      ├──────────────────────────────────────┤               │
│      │ TEST_000 1      "Lead connectivity..."│              │
│      │ TEST_001 0      "No defects found"   │               │
│      │ ...      ...    ...                  │               │
│      └──────────────────────────────────────┘               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 API 호출 플로우

```
Python Code
    ↓
saltlux_client._post_chat(messages)
    ↓
requests.post(
    url = "https://bridge.luxiacloud.com/llm/openai/chat/completions/{model}/create"
    headers = {"apikey": API_KEY}
    json = {
        "model": "luxia3-llm-32b-0731",
        "messages": [
            {"role": "system", "content": "..."},
            {"role": "user", "content": [
                {"type": "text", "text": "..."},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
            ]}
        ],
        "stream": False
    }
)
    ↓
[Saltlux API Server]
    ↓
Response:
{
    "choices": [
        {
            "message": {
                "content": "JSON response or text"
            }
        }
    ]
}
    ↓
Extract: response.json()["choices"][0]["message"]["content"]
    ↓
Parse JSON (if needed)
    ↓
Return to Agent
```

---

## 📝 요약

이 문서는 Luxia AI Agent 시스템의 **모든 워크플로우**를 상세히 정리했습니다:

1. ✅ **전체 시스템 아키텍처** - 4개 레이어 구조
2. ✅ **Multi-Model Agent** - Judge-Think-Act-Verify 4단계
3. ✅ **Luxia Enhanced Agent** - RAG + 보고서 + 앙상블 3단계
4. ✅ **Fusion Agent** - Balanced → Sensitive → Precision 3단계
5. ✅ **Final Omni-Agent** - Vision + Knowledge + Report 통합
6. ✅ **실행 스크립트** - run_full_analysis, run_multi_agent_test
7. ✅ **데이터 플로우** - 이미지 → API → 결과 전체 흐름

**핵심 강점**: 각 Agent의 실행 흐름을 시각적으로 완벽하게 이해할 수 있습니다.

→ **설계한 플로우의 장점**을 체계적으로 정리한 문서: [플로우_설계_장점.md](./플로우_설계_장점.md)

---

**생성 일시**: 2026-01-27
**문서 버전**: 1.0
**작성자**: Claude Code Assistant
**프로젝트**: 산업AI_Agent_해커톤
