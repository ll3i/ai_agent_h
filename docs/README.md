# 📚 Luxia AI Agent 시스템 문서 인덱스

## 개요

이 디렉터리는 Luxia AI Agent 시스템의 핵심 파이썬 파일들에 대한 상세한 문서를 포함하고 있습니다.

## 🗂️ 문서 카테고리

### 📚 전체 Python 파일 인덱스
**[PYTHON_FILES_INDEX.md](./PYTHON_FILES_INDEX.md)** ⭐
- **내용**: 프로젝트의 **모든 25개** Python 파일 완전 가이드
- **특징**: 파일 분류, 의존성 트리, 사용 시나리오, 빠른 참조
- **용도**: 전체 프로젝트 구조 파악 및 파일 검색

### ⚙️ 설정 및 유틸리티
**[config.py 가이드](./python_files/config_py_guide.md)** ⭐
- **내용**: 프로젝트 전체 설정 관리 (API, 모델, 경로, Agent)
- **특징**: 환경 변수 지원, 유효성 검증
- **용도**: 설정 이해 및 커스터마이징

---

## 📖 상세 Agent 문서 목록

### 1. 핵심 AI Agent 로직

#### [multi_model_agent_guide.md](./multi_model_agent_guide.md)
**파일**: `src/multi_model_agent.py`

**주요 내용**:
- Judge-Think-Act-Verify 오케스트레이션
- 4개 모델 사용 (gpt-4o-mini, claude-3.5-sonnet, gpt-3.5-turbo, gpt-4o)
- 6개 결함 분류 시스템
- 적응형 재검토 메커니즘
- 신뢰도 관리 및 부스팅

**핵심 특징**: 각 단계마다 최적화된 LLM 모델을 사용하여 정확도와 신뢰도 극대화

---

#### [luxia_enhanced_agent_guide.md](./luxia_enhanced_agent_guide.md)
**파일**: `src/luxia_enhanced_agent.py`

**주요 내용**:
- DefectKnowledgeBase: RAG 기반 유사도 검색
- DefectReportGenerator: 자동 기술 보고서 생성
- EnsembleReranker: 다중 모델 앙상블 최적화
- LuxiaEnhancedAgent: 3대 기능 통합

**핵심 특징**: Luxia Native 모델들(Embeddings, Text Gen, Reranking)을 활용한 신뢰도 및 품질 향상

---

#### [fusion_agent_guide.md](./fusion_agent_guide.md)
**파일**: `src/fusion_agent.py`

**주요 내용**:
- 3가지 방식의 장점 결합 (Single-Agent + Triple Vision + J-T-A-V)
- 3단계 Adaptive 전략 (Balanced → Sensitive → Precision)
- Triple Vision 이미지 전략 (Full + Body + Lead)
- FN/FP 동시 최소화

**핵심 특징**: False Positive와 False Negative를 동시에 최소화하는 Fusion 전략

---

#### [final_omni_agent_guide.md](./final_omni_agent_guide.md)
**파일**: `src/final_omni_agent.py`

**주요 내용**:
- LuxiaOmniAgent: Vision + Knowledge + Report 통합
- Vision Agent: 74% 최고 정확도 (classify_jtav_triple)
- Knowledge Agent: 과거 사례 검색 및 신뢰도 향상
- Report Agent: 자동 컨텍스트 추가

**핵심 특징**: Best-of-Breed 통합으로 정확도, 신뢰도, 설명력 모두 극대화

---

### 2. 실행 스크립트

#### [run_full_analysis_guide.md](./run_full_analysis_guide.md)
**파일**: `run_full_analysis.py`

**주요 내용**:
- Omni-Agent를 사용한 전체 데이터셋 자동 분석
- Example 이미지 + Test 이미지 순차 분석
- 표준 CSV + 상세 로그 자동 생성
- 에러 처리 및 로깅

**핵심 특징**: 한 번의 명령으로 전체 데이터셋 자동 분석 및 대회 제출용 결과 생성

---

#### [run_multi_agent_test_guide.md](./run_multi_agent_test_guide.md)
**파일**: `run_multi_agent_test.py`

**주요 내용**:
- Multi-Agent 로직 독립 검증
- CLI 인터페이스 (--mode example/test/both)
- 간단한 출력 (id, label만)
- 유연한 실행 모드

**핵심 특징**: Multi-Agent 로직을 독립적으로 검증하고 Example 데이터로 빠른 테스트 가능

---

## 🗺️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────┐
│              Luxia AI Agent 시스템                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│  핵심 Agent 로직:                                    │
│  ┌──────────────────────────────────────┐           │
│  │ 1. multi_model_agent.py              │           │
│  │    - Judge-Think-Act-Verify          │           │
│  │    - 4개 모델 오케스트레이션         │           │
│  └──────────────────────────────────────┘           │
│  ┌──────────────────────────────────────┐           │
│  │ 2. luxia_enhanced_agent.py           │           │
│  │    - RAG (Knowledge Base)            │           │
│  │    - 자동 보고서 생성                │           │
│  │    - 앙상블 재정렬                   │           │
│  └──────────────────────────────────────┘           │
│  ┌──────────────────────────────────────┐           │
│  │ 3. fusion_agent.py                   │           │
│  │    - Triple Vision                   │           │
│  │    - FN/FP 최소화                    │           │
│  └──────────────────────────────────────┘           │
│  ┌──────────────────────────────────────┐           │
│  │ 4. final_omni_agent.py ⭐            │           │
│  │    - Vision + Knowledge + Report     │           │
│  │    - 최종 통합 시스템                │           │
│  └──────────────────────────────────────┘           │
│                                                      │
│  실행 스크립트:                                      │
│  ┌──────────────────────────────────────┐           │
│  │ run_full_analysis.py ⭐              │           │
│  │    - 전체 데이터셋 자동 분석         │           │
│  │    - 대회 제출용 결과 생성           │           │
│  └──────────────────────────────────────┘           │
│  ┌──────────────────────────────────────┐           │
│  │ run_multi_agent_test.py              │           │
│  │    - Multi-Agent 독립 검증           │           │
│  │    - Example/Test 선택 실행          │           │
│  └──────────────────────────────────────┘           │
│                                                      │
└─────────────────────────────────────────────────────┘

⭐ = 최종 제출용 권장
```

---

## 🚀 빠른 시작 가이드

### 1. 환경 설정

```bash
# 패키지 설치
pip install pandas requests python-dotenv

# API 키 설정 (.env 파일)
SALTLUX_API_KEY=your_api_key_here
```

### 2. 빠른 테스트 (Example 데이터)

```bash
# Omni-Agent로 Example 이미지 분석
python -c "
from run_full_analysis import run_dataset
run_dataset('example_images.csv', 'output_example.csv', 'Example')
"
```

### 3. 전체 분석 실행 (대회 제출용)

```bash
# 100개 Test 이미지 전체 분석
python run_full_analysis.py

# 결과 확인
cat output.csv
```

---

## 📊 문서 읽는 순서 (권장)

### 초급: 시스템 이해하기
1. **final_omni_agent_guide.md**: 전체 시스템 개요
2. **run_full_analysis_guide.md**: 실행 방법
3. **multi_model_agent_guide.md**: 핵심 로직 이해

### 중급: 각 컴포넌트 깊이 이해
4. **luxia_enhanced_agent_guide.md**: RAG 및 강화 기능
5. **fusion_agent_guide.md**: FN/FP 최소화 전략

### 고급: 시스템 커스터마이징
6. **run_multi_agent_test_guide.md**: Multi-Agent 검증
7. 모든 가이드의 "설정 및 커스터마이징" 섹션

---

## 🔍 주요 개념 빠른 참조

### Agent 타입

| Agent | 파일 | 특징 | 정확도 |
|-------|------|------|--------|
| **Omni-Agent** | final_omni_agent.py | Vision+Knowledge+Report 통합 | 74% (Best) |
| **Multi-Model** | multi_model_agent.py | 4개 모델 오케스트레이션 | 72% |
| **Fusion** | fusion_agent.py | Triple Vision + FN/FP 최소화 | 70% |
| **Enhanced** | luxia_enhanced_agent.py | RAG + 보고서 + 앙상블 | 기존 Agent 강화 |

### 실행 스크립트

| 스크립트 | 용도 | 출력 |
|---------|------|------|
| **run_full_analysis.py** | 대회 제출용 전체 분석 | output.csv (100개) |
| **run_multi_agent_test.py** | Multi-Agent 검증 | output_multi_*.csv |

---

## 📝 문서 작성 기준

모든 가이드는 다음 섹션을 포함합니다:

1. **📋 개요**: 역할 및 핵심 아이디어
2. **🏗️ 아키텍처**: 시스템 구조 및 다이어그램
3. **📂 주요 구성 요소**: 클래스, 함수, 데이터 구조
4. **🔧 핵심 함수 상세 설명**: 코드 예제 포함
5. **🔄 통합 워크플로우**: 실행 흐름도
6. **📊 실행 예제**: 실제 사용 사례
7. **🎯 장점 및 특징**: 핵심 강점
8. **⚙️ 설정 및 커스터마이징**: 확장 방법
9. **🔍 디버깅 및 로깅**: 문제 해결
10. **📈 성능 최적화 팁**: 속도/메모리 개선
11. **🚀 실행 방법**: 명령어 및 옵션
12. **📝 요약**: 핵심 정리

---

## 🆘 도움말

### 문서에서 정보 찾기

**Q: Agent 선택 기준이 뭔가요?**
→ [final_omni_agent_guide.md](./final_omni_agent_guide.md) - "Omni-Agent vs Multi-Agent" 섹션 참조

**Q: FN(놓친 결함)을 줄이고 싶어요**
→ [fusion_agent_guide.md](./fusion_agent_guide.md) - "Step 2: Sensitive Recheck" 섹션 참조

**Q: 신뢰도를 어떻게 높이나요?**
→ [luxia_enhanced_agent_guide.md](./luxia_enhanced_agent_guide.md) - "DefectKnowledgeBase" 섹션 참조

**Q: 100개 이미지를 빠르게 분석하려면?**
→ [run_full_analysis_guide.md](./run_full_analysis_guide.md) - "성능 최적화 팁" 섹션 참조

**Q: Multi-Model Agent의 각 단계는 뭔가요?**
→ [multi_model_agent_guide.md](./multi_model_agent_guide.md) - "4단계 AI Agent 파이프라인" 섹션 참조

---

## 📞 연락처

문서 관련 질문이나 개선 제안은 프로젝트 관리자에게 문의하세요.

---

**생성 일시**: 2026-01-27
**문서 버전**: 1.0
**작성자**: Claude Code Assistant
**프로젝트**: 산업AI_Agent_해커톤
