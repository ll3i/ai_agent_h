# 📚 Python 파일 완전 가이드 인덱스

## 개요

프로젝트의 모든 Python 파일에 대한 상세 설명 및 사용법을 정리한 문서입니다.

---

## 📂 파일 분류

### 🎯 핵심 Agent 시스템 (6개) - 상세 문서 있음

#### 1. [multi_model_agent.py](./multi_model_agent_guide.md)
- **역할**: Judge-Think-Act-Verify 다중 모델 오케스트레이션
- **모델**: gpt-4o-mini, claude-3.5-sonnet, gpt-3.5-turbo, gpt-4o
- **특징**: 각 단계마다 최적화된 모델 사용

#### 2. [luxia_enhanced_agent.py](./luxia_enhanced_agent_guide.md)
- **역할**: Luxia Native 기능 통합 (RAG + 보고서 + 앙상블)
- **구성**: DefectKnowledgeBase, DefectReportGenerator, EnsembleReranker
- **특징**: 신뢰도 10-30% 향상

#### 3. [fusion_agent.py](./fusion_agent_guide.md)
- **역할**: 3가지 방식의 장점 결합 (FN/FP 동시 최소화)
- **전략**: Balanced → Sensitive → Precision
- **특징**: Triple Vision (Full + Body + Lead)

#### 4. [final_omni_agent.py](./final_omni_agent_guide.md)
- **역할**: Vision + Knowledge + Report 최종 통합 시스템
- **정확도**: 74% (Best)
- **특징**: Best-of-Breed 통합

#### 5. [run_full_analysis.py](./run_full_analysis_guide.md)
- **역할**: 전체 데이터셋 자동 분석 실행 스크립트
- **출력**: output.csv (대회 제출용)
- **특징**: Example + Test 순차 분석

#### 6. [run_multi_agent_test.py](./run_multi_agent_test_guide.md)
- **역할**: Multi-Agent 독립 검증 스크립트
- **CLI**: --mode example/test/both
- **특징**: 빠른 테스트 가능

---

### ⚙️ 설정 및 유틸리티 (3개) - 상세 문서 있음

#### 7. [config.py](./python_files/config_py_guide.md) ⭐
- **역할**: 프로젝트 전체 설정 관리
- **내용**: 경로, API, 모델, Agent 설정
- **특징**: 환경 변수 지원, 유효성 검증

#### 8. utils.py
```python
# 주요 함수:
- setup_logging(): 로깅 설정
- save_results_to_csv(): CSV 저장
- calculate_metrics(): 성능 지표 계산
- Timer: 실행 시간 측정 클래스
```

#### 9. roi_cropper.py
```python
# 주요 함수:
- crop_body_roi(): 패키지 중심 확대
- crop_lead_roi(): 리드 영역 확대
```
**사용처**: fusion_agent.py

---

### 🔬 Vision Agent 시스템 (4개)

#### 10. jtav_triple_vision.py
- **역할**: Judge-Think-Act-Verify + Triple Vision
- **모델**: Luxia 32B
- **정확도**: 74% (최고)
- **사용처**: final_omni_agent.py

#### 11. triple_vision_agent.py
- **역할**: 3개 이미지 동시 분석
- **전략**: Full + Body + Lead
- **특징**: ROI 기반 집중 분석

#### 12. hybrid_agent.py
- **역할**: 하이브리드 분석 방식
- **특징**: 여러 전략 결합

#### 13. multi_agent.py
- **역할**: Multi-Agent 로직
- **사용처**: run_multi_agent_test.py

---

### 🧠 Agent 핵심 컴포넌트 (6개)

#### 14. agent_core.py
```python
# Agent 핵심 로직
class AgentCore:
    - execute(): 메인 실행 함수
    - iterate(): 반복 로직
```

#### 15. vision_analyzer.py
```python
# 비전 분석
class VisionAnalyzer:
    - analyze_image(): 이미지 분석
    - extract_features(): 특징 추출
```

#### 16. reasoner.py
```python
# 추론 엔진
class Reasoner:
    - reason(): 추론 실행
    - assess_confidence(): 신뢰도 평가
```

#### 17. decision_maker.py
```python
# 의사결정
class DecisionMaker:
    - make_decision(): 판정 실행
    - apply_rules(): 규칙 적용
```

#### 18. verifier.py
```python
# 검증 시스템
class Verifier:
    - verify(): 검증 실행
    - confirm(): 최종 확인
```

#### 19. saltlux_client.py
```python
# Saltlux API 클라이언트
class SaltluxClient:
    - post_chat(): API 호출
    - handle_retry(): 재시도 처리
```

---

### 🔧 이미지 처리 (2개)

#### 20. image_processor.py
```python
# 이미지 전처리
class ImageProcessor:
    - resize(): 리사이즈
    - normalize(): 정규화
    - to_base64(): Base64 변환
```

#### 21. advanced_preprocessor.py
```python
# 고급 전처리
- enhance_image(): 이미지 향상
- remove_noise(): 노이즈 제거
```

---

### 🚀 통합 Agent 시스템 (3개)

#### 22. integrated_agent.py
```python
# 통합 Agent (기본)
class IntegratedAgent:
    - analyze(): 전체 분석 실행
```

#### 23. integrated_agent_enhanced.py
```python
# 통합 Agent (강화)
- 추가 기능 포함
```

#### 24. complete_enhanced_agent.py
```python
# 완전 강화 Agent
- 모든 기능 통합
```

#### 25. enhanced_jtav_v2.py
```python
# JTAV 강화 버전 2
- 성능 개선 버전
```

---

## 📊 파일 의존성 트리

```
run_full_analysis.py (실행 스크립트)
├── final_omni_agent.py (최종 통합)
│   ├── jtav_triple_vision.py (Vision Agent)
│   │   ├── roi_cropper.py (이미지 크롭)
│   │   ├── saltlux_client.py (API)
│   │   └── config.py (설정)
│   └── luxia_enhanced_agent.py (강화 기능)
│       └── config.py
├── utils.py (유틸리티)
└── config.py (설정)

run_multi_agent_test.py (테스트 스크립트)
└── multi_agent.py
    ├── multi_model_agent.py
    │   ├── config.py
    │   └── utils.py
    └── fusion_agent.py
        └── roi_cropper.py
```

---

## 🎯 파일 사용 시나리오

### 시나리오 1: 대회 제출 (최종)
```
사용 파일:
1. run_full_analysis.py (실행)
2. final_omni_agent.py (Agent)
3. jtav_triple_vision.py (Vision)
4. luxia_enhanced_agent.py (강화)
5. config.py (설정)
6. utils.py (유틸)
```

### 시나리오 2: Multi-Agent 검증
```
사용 파일:
1. run_multi_agent_test.py (실행)
2. multi_agent.py (Agent)
3. multi_model_agent.py (다중 모델)
4. config.py (설정)
```

### 시나리오 3: Fusion Agent 테스트
```
사용 파일:
1. fusion_agent.py (Fusion)
2. roi_cropper.py (이미지)
3. config.py (설정)
```

---

## 📝 빠른 참조

### API 관련
- `saltlux_client.py`: API 호출
- `config.py`: API 키 및 URL 설정

### 이미지 처리
- `image_processor.py`: 기본 처리
- `advanced_preprocessor.py`: 고급 처리
- `roi_cropper.py`: ROI 크롭

### Agent 로직
- `agent_core.py`: 핵심 로직
- `vision_analyzer.py`: 비전 분석
- `reasoner.py`: 추론
- `decision_maker.py`: 의사결정
- `verifier.py`: 검증

### 유틸리티
- `utils.py`: 로깅, CSV, 메트릭
- `config.py`: 전체 설정

---

## 🔍 파일 찾기

**Q: Vision 분석은 어디에?**
→ `jtav_triple_vision.py`, `vision_analyzer.py`

**Q: ROI 크롭은?**
→ `roi_cropper.py`

**Q: API 호출은?**
→ `saltlux_client.py`

**Q: 설정 파일은?**
→ `config.py`

**Q: 최종 통합 시스템은?**
→ `final_omni_agent.py`

**Q: 실행 스크립트는?**
→ `run_full_analysis.py`, `run_multi_agent_test.py`

---

## 📖 문서 읽는 순서 (권장)

### 초급: 시작하기
1. **config.py** - 설정 이해
2. **run_full_analysis.py** - 실행 방법
3. **final_omni_agent.py** - 최종 시스템

### 중급: 깊이 이해
4. **jtav_triple_vision.py** - Vision Agent
5. **luxia_enhanced_agent.py** - 강화 기능
6. **fusion_agent.py** - Fusion 전략

### 고급: 내부 구조
7. **multi_model_agent.py** - 다중 모델
8. **roi_cropper.py** - 이미지 처리
9. **utils.py** - 유틸리티

---

## 🆕 최신 업데이트

**2026-01-27**:
- ✅ 6개 핵심 Agent md 문서 작성 완료
- ✅ config.py 상세 문서 작성 완료
- ✅ Python 파일 전체 인덱스 생성 완료

---

## 📞 문의

각 파일에 대한 상세 정보는 해당 .md 문서를 참조하세요.

프로젝트 관련 질문은 프로젝트 관리자에게 문의하세요.

---

**생성 일시**: 2026-01-27
**문서 버전**: 1.0
**작성자**: Claude Code Assistant
**프로젝트**: 산업AI_Agent_해커톤
