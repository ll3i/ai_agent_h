# 제조공정 이미지 분류 AI Agent - 개발 계획서

**프로젝트명**: 한양대 × 현대엔지비 멀티모달 LLM 기반 제조 AI Agent  
**제출 마감**: 2026년 1월 28일 (수) 13:00  
**작성일**: 2026년 1월 27일

---

## 1. 프로젝트 개요

### 1.1 목표
- 제조공정 이미지 100장(개발용 20장 + 평가용 100장)을 정상/비정상으로 분류
- Binary F1-Score 기반 성능 평가
- End-to-End 자동화된 AI Agent 시스템 구현

### 1.2 주요 특성
- **멀티모달 처리**: 이미지 데이터 분석 + 텍스트 기반 추론
- **에이전트 기반**: Judge-Think-Act-Verify 반복 프로세스
- **API 기반**: Saltlux LUXIA PLATFORM API 사용 (필수)
- **자동화 요건**: 입력 → 전처리 → 추론 → 결과 생성까지 자동화

### 1.3 평가 기준
| 항목 | 설명 |
|------|------|
| **Public Score** | 전체 테스트 데이터 50% (100장 중 50장) |
| **Private Score** | 전체 테스트 데이터 100% (100장 전체) |
| **평가 지표** | Binary F1-Score |
| **평가 방식** | 2단계: Public 리더보드 → Private 최종 평가 |

---

## 2. 기술 스택 및 아키텍처

### 2.1 사용 기술
```
┌─────────────────────────────────────────────────────────┐
│                    AI Agent System                       │
├─────────────────────────────────────────────────────────┤
│ Language: Python 3.8+                                   │
│ Framework: Jupyter Notebook (.ipynb)                    │
│ LLM API: Saltlux LUXIA PLATFORM API                    │
│ Image Processing: OpenCV, Pillow                        │
│ Data Processing: Pandas, NumPy                          │
└─────────────────────────────────────────────────────────┘
```

### 2.2 시스템 아키텍처

```
[이미지 입력 (100장)]
        ↓
┌─────────────────────────────────┐
│   1. 데이터 전처리 모듈         │
│   - 이미지 로드                 │
│   - 정규화/리사이징             │
│   - 메타데이터 추출             │
└─────────────────────────────────┘
        ↓
┌─────────────────────────────────┐
│   2. AI Agent 추론 모듈         │
│   ┌───────────────────────────┐ │
│   │ Vision Analysis           │ │ → Saltlux API
│   │ (이미지 특징 추출)        │ │
│   └───────────────────────────┘ │
│   ┌───────────────────────────┐ │
│   │ Multi-step Reasoning      │ │
│   │ (정상/비정상 판단)        │ │
│   └───────────────────────────┘ │
│   ┌───────────────────────────┐ │
│   │ Verification             │ │
│   │ (신뢰도 검증)            │ │
│   └───────────────────────────┘ │
└─────────────────────────────────┘
        ↓
┌─────────────────────────────────┐
│   3. 결과 생성 모듈             │
│   - 분류 결과 (Normal/Abnormal) │
│   - 신뢰도 점수                 │
│   - CSV 파일 출력              │
└─────────────────────────────────┘
        ↓
[output.csv (이미지명, 예측값)]
```

### 2.3 AI Agent 구성 요소

| 모듈 | 역할 | 상세 |
|------|------|------|
| **Image Processor** | 이미지 전처리 | 로드, 리사이징, 정규화 |
| **Vision Analyzer** | 이미지 특징 분석 | Saltlux API로 이미지 분석 |
| **Reasoner** | 추론 엔진 | 다단계 논리적 판단 (Think step) |
| **Decision Maker** | 최종 판단 | 정상/비정상 분류 (Act step) |
| **Verifier** | 신뢰도 검증 | 결과 신뢰성 평가 (Verify step) |
| **Output Manager** | 결과 저장 | CSV 형식으로 최종 결과 생성 |

---

## 3. Saltlux LUXIA PLATFORM API 활용 방안

### 3.1 API 설정
```python
# API 키 설정 (환경변수)
import os
from dotenv import load_dotenv

load_dotenv()

SALTLUX_API_KEY = os.getenv('SALTLUX_API_KEY')
BRIDGE_URL = "https://bridge.luxiacloud.com/llm/openai/chat/completions/gpt-4o-mini/create"
MODEL = "gpt-4o-mini-2024-07-18"
HEADERS = {"apikey": SALTLUX_API_KEY, "Content-Type": "application/json"}
```

### 3.2 사용 모델
- **Vision Model**: 이미지 분석용 (제조환경 특성 반영)
- **Language Model**: 추론 및 판단용 (다국어, 도메인 최적화)

### 3.3 API 호출 전략
1. **배치 처리**: 100장을 효율적으로 처리 (API 호출 제한 고려)
2. **에러 처리**: 타임아웃, 속도 제한 대응
3. **재시도 로직**: 실패 시 자동 재시도
4. **로깅**: 전체 추론 과정 기록

### 3.4 프롬프트 설계
```
[이미지 분석 프롬프트]
"이 제조공정 이미지를 분석하고 다음을 판단하세요:
1. 주요 부품/설비 식별
2. 이상 신호 감지
3. 정상 상태와의 비교
4. 최종 판단: Normal/Abnormal

이유를 상세히 설명하세요."
```

---

## 4. 개발 계획 및 일정

### 4.1 단계별 구현 계획

#### **Phase 1: 환경 구성 및 기초 설정** (1월 27일) ✅ 완료
- [x] 프로젝트 폴더 구조 생성
- [x] Saltlux API 크레덴셜 설정
- [x] 필요 라이브러리 설치 및 테스트
- [x] 개발용 데이터(20장) 확인 및 분석

**산출물**:
- `requirements.txt`: 필요 패키지 목록 ✅
- `config.py`: API 설정 파일 ✅
- `.env`: 환경 변수 설정 ✅

---

#### **Phase 2: 데이터 전처리 모듈 개발** (1월 27일) ✅ 완료
- [x] 이미지 로딩 함수 작성
- [x] 이미지 정규화/리사이징 로직
- [x] 메타데이터 추출
- [x] 에러 처리 및 로깅

**산출물**:
- `image_processor.py`: 전처리 모듈 ✅
- `utils.py`: 유틸리티 함수 ✅

**테스트 코드**:
```python
# 샘플 10장으로 전처리 테스트
test_images = load_test_images(sample_size=10)
assert len(test_images) == 10
assert all(img.shape == (224, 224, 3) for img in test_images)
```

---

#### **Phase 3: Saltlux API 연동** (1월 27일) ✅ 완료
- [x] API 클라이언트 구현
- [x] 이미지 업로드 및 분석 함수
- [x] 응답 처리 및 파싱
- [x] Rate limiting 및 재시도 로직

**산출물**:
- `saltlux_client.py`: API 클라이언트 ✅
- `vision_analyzer.py`: 이미지 분석 모듈 ✅
- `integrated_agent.py`: 통합 Agent (Saltlux API 연동 포함) ✅

**API 연동 방식**:
```python
# OpenAI ChatCompletions 형식의 Saltlux Bridge API 사용
BRIDGE_URL = "https://bridge.luxiacloud.com/llm/openai/chat/completions/gpt-4o-mini/create"
MODEL = "gpt-4o-mini-2024-07-18"
HEADERS = {"apikey": API_KEY, "Content-Type": "application/json"}
```

---

#### **Phase 4: AI Agent 핵심 로직 개발** (1월 27-28일) ✅ 완료
- [x] Vision Analyzer: 이미지 특징 추출
- [x] Reasoner: 다단계 추론 로직
- [x] Decision Maker: 정상/비정상 분류 결정
- [x] Verifier: 신뢰도 검증

**산출물**:
- `agent_core.py`: Agent 핵심 로직 ✅
- `reasoner.py`: 추론 엔진 ✅
- `decision_maker.py`: 의사결정 모듈 ✅
- `verifier.py`: 검증 모듈 ✅
- `integrated_agent.py`: 통합 AI Agent (Judge-Think-Act-Verify 구조) ✅

**핵심 구현** (integrated_agent.py):
```python
def classify_agent_integrated(img_url: str) -> Dict[str, Any]:
    """
    통합 AI Agent (Judge-Think-Act-Verify)

    Flow:
    1. JUDGE(Observe): LLM으로 이미지 분석 → 결함 체크리스트(JSON)
    2. THINK(Analyze): 결함 지표 분석 및 신뢰도 추정
    3. ACT(Decide): 규칙 기반 정상/비정상 판단
    4. VERIFY(Review): 검증 및 필요시 보수적 재검토
    """
    # Step 1: JUDGE - 1차 관찰
    obs1 = observe(img_url, strict=False)

    # Step 2: THINK - 분석
    reasoning1 = think(obs1)

    # Step 3: ACT - 판단
    label1, uncertain = act(reasoning1)

    # Step 4: VERIFY - 검증 (필요시 재검토)
    if uncertain:
        obs2 = observe(img_url, strict=True)  # 보수적 재검토
        # ...

    return verification
```

---

#### **Phase 5: 통합 및 자동화** (1월 28일 오전)
- [ ] 전체 파이프라인 통합
- [ ] End-to-End 테스트 (개발 데이터 20장)
- [ ] 배치 처리 스크립트
- [ ] 오류 처리 및 로깅 완성

**산출물**:
- `main_agent.py`: 통합 메인 스크립트
- `batch_processor.py`: 배치 처리 모듈
- `test_results_dev.csv`: 개발 데이터 결과

**자동화 요구사항**:
```python
def process_all_images(image_dir, output_csv):
    """
    자동화된 파이프라인:
    입력 → 전처리 → 추론 → 결과 저장
    """
    images = load_images(image_dir)  # 입력
    preprocessed = [preprocess(img) for img in images]  # 전처리
    results = [agent.analyze(img) for img in preprocessed]  # 추론
    save_results(results, output_csv)  # 결과 저장
```

---

#### **Phase 6: 성능 최적화 및 검증** (1월 28일 오전)
- [ ] Public Score 확인 (50장 기준)
- [ ] 성능 분석 및 문제점 파악
- [ ] 프롬프트 튜닝 (필요시)
- [ ] 신뢰도 임계값 조정

**측정 지표**:
- Precision, Recall, F1-Score
- Confusion Matrix
- 오분류 사례 분석

---

#### **Phase 7: 최종 Jupyter Notebook 작성** (1월 28일 오전)
- [ ] 전체 코드를 `.ipynb` 형식으로 통합
- [ ] Markdown 문서화 추가
- [ ] 실행 흐름 설명
- [ ] 결과 시각화

**구성**:
1. 프로젝트 개요 및 설계
2. 필요 라이브러리 설치
3. 데이터 전처리
4. AI Agent 구현
5. 추론 실행
6. 결과 분석
7. 결론 및 개선 방안

---

#### **Phase 8: 발표자료 준비** (1월 28일 오전)
- [ ] PDF 발표자료 작성 (5분 분량)
- [ ] 2차 평가 항목 포함
- [ ] 설계 과정 및 결과 반영
- [ ] 파일 크기 확인 (20MB 미만)

**발표 구성**:
1. **프로젝트 배경** (30초)
   - 제조공정의 도전과제
   - AI Agent의 필요성
   
2. **시스템 설계** (1분)
   - 아키텍처 다이어그램
   - 핵심 기술 선택 이유
   
3. **구현 방법** (1분 30초)
   - Saltlux API 활용
   - Agent 구성 및 프롬프트
   - 자동화 전략
   
4. **결과 및 성능** (1분)
   - Public/Private Score
   - F1-Score 및 분석
   - 오류 사례 분석
   
5. **개선 및 결론** (30초)
   - 향후 개선 방향
   - 산업 적용 가능성

---

### 4.2 일정표
```
2026-01-27 (월)
├─ 13:00-14:00: Phase 1 (환경 구성)
├─ 14:00-15:30: Phase 2 (데이터 전처리)
├─ 15:30-17:00: Phase 3 (API 연동)
└─ 17:00-19:00: Phase 4 (Agent 로직) - Part 1

2026-01-28 (수)
├─ 09:00-10:00: Phase 4 (Agent 로직) - Part 2
├─ 10:00-11:00: Phase 5 (통합 및 자동화)
├─ 11:00-12:00: Phase 6 (성능 최적화)
├─ 12:00-12:30: Phase 7 (Notebook 작성)
└─ 12:30-13:00: Phase 8 (발표자료) + 최종 제출
```

---

## 5. 평가 기준 및 성과 목표

### 5.1 2차 평가 (발표 평가) 상세 기준 (총 100점)

#### **1️⃣ 리더보드 성능 (30점)**
| 평가 항목 | 설명 |
|----------|------|
| **1차 평가 환산 점수** | Public Score 기반 F1-Score 변환 |
| **평가 방식** | 전체 100장 이미지에 대한 Binary F1-Score |
| **목표** | > 0.85 (우수), > 0.80 (양호), > 0.75 (보통) |

---

#### **2️⃣ 문제 접근 방식 및 설계 논리 (25점)**

| 세부 기준 | 평가 항목 | 설명 | 배점 |
|----------|----------|------|------|
| **① 문제 이해도** | 요구사항 및 제약조건 정확성 | • 제조공정 이미지 분류의 목표 명확히 파악<br>• 정상/비정상 이진 분류 이해<br>• Saltlux API 사용 필수 조건 인식<br>• End-to-End 자동화 요구사항 충족 | 6.25점 |
| **② 접근 구조 설정** | AI Agent 기반 설계 | • 단순 LLM 호출이 아닌 Agent 패러다임 도입<br>• Judge-Think-Act-Verify 구조 설계<br>• 멀티모달 처리 전략 수립<br>• 자동화 파이프라인 구성 | 6.25점 |
| **③ 설계 논리** | 구조의 논리적 일관성 | • 전체 Agent 흐름이 명확하고 체계적<br>• 각 모듈 간 연결이 논리적<br>• 데이터 흐름이 명확히 정의됨<br>• 예외 상황에 대한 처리 방안 포함 | 6.25점 |
| **④ 전략 적합성** | 문제 특성에 대한 적합성 | • 제조공정 이미지 분류에 Agent 기반 접근이 적절<br>• 멀티모달 LLM의 강점 활용<br>• 신뢰도 검증 프로세스 포함<br>• 실제 현장 적용 가능성 고려 | 6.25점 |

---

#### **3️⃣ AI Agent Flow 완성도 (35점)**

| 세부 기준 | 평가 항목 | 설명 | 배점 |
|----------|----------|------|------|
| **① 판단 구조** | LLM 해석 및 판단 단계 | • LLM 출력 결과를 체계적으로 파싱<br>• 판단을 수행하는 명확한 Logic 존재<br>• 신뢰도 임계값 기반 판단 구현<br>• 여러 관점의 판단 통합 | 8.75점 |
| **② 행동 결정 구조** | 조건부 의사결정 구조 | • 판단 결과 → 다음 행동으로의 명확한 조건부 흐름<br>• LLM 출력값 기준의 분기 로직<br>• 재추론 vs 최종 결정의 조건 명확<br>• 상태 전이(State Transition) 정의 | 8.75점 |
| **③ 종료 조건** | 반복 종료 기준 정의 | • 명확한 종료 조건 설정 (예: 신뢰도 임계값 달성)<br>• 논리적이고 추적 가능한 종료 기준<br>• 최대 재시도 횟수 제한<br>• 종료 조건 검증 로직 포함 | 8.75점 |
| **④ 구조 명확성** | Agent vs 단순 LLM 호출 구분 | • 단순 LLM 호출과 명확히 구분되는 Agent 구조<br>• 반복적인 사고-행동-검증 프로세스 구현<br>• 메모리/상태 추적 메커니즘<br>• 명확한 Agent 패턴 적용 | 8.75점 |

---

#### **4️⃣ 효율성 및 실용성 (10점)**

| 세부 기준 | 평가 항목 | 설명 | 배점 |
|----------|----------|------|------|
| **① 호출 효율** | LLM 호출 최적화 | • 불필요한 중복 호출 없음<br>• 배치 처리로 효율성 확보<br>• API 비용 고려 설계<br>• 캐싱 또는 메모이제이션 활용 | 2.5점 |
| **② 구조 단순성** | 복잡도 최소화 | • 문제 해결 목표 대비 적절한 수준의 복잡도<br>• 불필요한 기능 배제<br>• 코드 가독성 및 유지보수성<br>• 모듈화된 구조 | 2.5점 |
| **③ 실용성** | 실제 적용 가능성 | • 현장 환경에서의 배포 가능성<br>• 사용자 친화적 인터페이스<br>• 에러 처리 및 로깅 완성도<br>• 확장성 고려 설계 | 2.5점 |
| **④ 재현 가능성** | 반복 실행 가능성 | • 동일 환경에서 일관된 결과 도출<br>• 의존성 명확히 문서화<br>• 재현 불가능한 요소 제거<br>• 시드값 고정으로 결정성 보장 | 2.5점 |

---

### 5.2 핵심 성과 목표

#### **리더보드 성능 목표**
| 지표 | 목표치 |
|------|--------|
| **F1-Score** | > 0.85 (30점 만점 환산) |
| **Precision** | > 0.85 |
| **Recall** | > 0.85 |
| **정확도 (Accuracy)** | > 0.85 |

#### **설계 및 구현 목표**
| 항목 | 달성 기준 |
|------|---------|
| **문제 이해** | 4가지 평가 기준 모두 충족 |
| **Agent Flow** | 4단계 판단-행동-검증 명확히 구분 |
| **효율성** | API 호출 최소화 + 안정적 재현 |

---

### 5.3 시스템 특성 및 차별성

#### **필수 특성**
- ✅ **자동화**: 100% 자동화된 End-to-End 파이프라인
- ✅ **에이전트 구조**: 단순 LLM 호출이 아닌 Judge-Think-Act-Verify 반복
- ✅ **재현성**: 동일 입력에 대한 일관된 결과
- ✅ **신뢰성**: 신뢰도 점수와 함께 결과 제시

#### **차별 포인트**
1. **멀티모달 이해**: 이미지 시각정보 + 텍스트 기반 추론
2. **Agent 기반**: 단순 분류가 아닌 사고-행동-검증 반복 프로세스
3. **도메인 최적화**: 제조공정 특성에 맞춘 프롬프트 설계
4. **안정성**: 에러 처리, 재시도 로직, 자동 복구 메커니즘
5. **투명성**: 판단 근거와 신뢰도를 명확히 제시

---

### 5.4 발표 시 강조할 포인트

#### **1️⃣ 문제 접근 (설계 논리 - 25점 확보)**
```
❌ 피할 점: "LLM에 이미지를 입력하고 정상/비정상 분류"
✅강조할 점: 
   - 제조공정의 복잡성 이해
   - 왜 Agent가 필요한가? (판단-재검토-검증의 반복)
   - 멀티모달 AI의 장점 활용
   - Saltlux API 선택 이유
```

#### **2️⃣ Agent Flow (완성도 - 35점 확보)**
```
명확한 4단계 구분:

Step 1: Judge (판단)
  ↓ LLM 분석 결과 해석
  
Step 2: Think (사고)
  ↓ 신뢰도 평가 및 재검토 필요성 판단
  
Step 3: Act (행동)
  ↓ 최종 결정 또는 재추론 실행
  
Step 4: Verify (검증)
  ↓ 결과 검증 및 확신도 확인
  
[종료 조건: 신뢰도 > 임계값 또는 최대 재시도 횟수 도달]
```

#### **3️⃣ 효율성 (10점 확보)**
```
- API 호출 횟수 최적화 설명
- 배치 처리로 시간 단축
- 메모리 효율성
- 재현 가능성 보증
```

---

## 6. 리스크 및 대응 방안

### 6.1 기술적 리스크

| 리스크 | 영향도 | 대응 방안 |
|--------|--------|---------|
| **API 속도 제한** | 높음 | Batch 처리, 큐 시스템 구현 |
| **API 오류 발생** | 높음 | 재시도 로직, 폴백 메커니즘 |
| **메모리 부족** | 중간 | 이미지 스트리밍 처리, 메모리 최적화 |
| **분류 성능 부족** | 높음 | 프롬프트 튜닝, 임계값 조정 |

### 6.2 일정상 리스크

| 리스크 | 영향도 | 대응 방안 |
|--------|--------|---------|
| **개발 지연** | 높음 | 병렬 개발, 모듈화 구조 |
| **마지막 제출 실수** | 높음 | 사전 제출 테스트, 체크리스트 |
| **데이터 손상** | 높음 | 지속적인 버전 관리, 백업 |

---

## 7. 최종 제출 체크리스트

### 7.1 코드 제출 (`deadline: 2026-01-28 13:00`)

```
📦 제출 폴더 구조
├── 📄 ai_agent.ipynb ⭐ (필수)
│   ├── 1. 개요 및 설계
│   ├── 2. 라이브러리 설치
│   ├── 3. 데이터 전처리
│   ├── 4. AI Agent 구현
│   ├── 5. 배치 처리
│   ├── 6. 결과 분석
│   └── 7. 결론
│
├── 📄 presentation.pdf ⭐ (필수, <20MB)
│   └── 5분 발표 자료
│
├── 📄 output.csv (평가 결과)
│   └── image_name, prediction
│
├── 📁 data/
│   └── [개발용 이미지 20장]
│
├── 📁 src/
│   ├── config.py
│   ├── image_processor.py
│   ├── saltlux_client.py
│   ├── agent_core.py
│   └── utils.py
│
├── 📄 requirements.txt
└── 📄 README.md
```

### 7.2 최종 검증 항목

- [ ] **코드 완성도**
  - [ ] End-to-End 자동화 파이프라인 동작
  - [ ] 100장 모두 처리 가능 확인
  - [ ] 오류 처리 및 로깅 완성
  
- [ ] **성능 확인**
  - [ ] Public Score 확인
  - [ ] F1-Score 계산 정확성
  - [ ] 결과 파일 형식 (CSV, UTF-8)
  
- [ ] **문서화**
  - [ ] Jupyter Notebook 완성
  - [ ] 코드 주석 및 설명
  - [ ] README 작성
  
- [ ] **발표자료**
  - [ ] PDF 형식 확인
  - [ ] 파일 크기 < 20MB
  - [ ] 2차 평가 항목 포함
  - [ ] 5분 분량 분량 조정

---

## 8. 참고 자료 및 추가 정보

### 8.1 Saltlux LUXIA PLATFORM 문서
- [공식 API 문서]
- [모델 목록 및 성능]
- [베스트 프랙티스]

### 8.2 F1-Score 계산
```
Precision = TP / (TP + FP)
Recall = TP / (TP + FN)
F1-Score = 2 * (Precision * Recall) / (Precision + Recall)
```

### 8.3 Binary Classification 평가 예시
```
예측값: [1, 0, 1, 1, 0, ...]  (1=Abnormal, 0=Normal)
실제값: [1, 0, 0, 1, 0, ...]

Confusion Matrix:
           Predicted
         Normal | Abnormal
Actual Normal   | TN | FP
      Abnormal  | FN | TP
```

---

## 9. 개발 완료 후 체크리스트

```
[x] Phase 1: 환경 구성 완료 ✅
[x] Phase 2: 데이터 전처리 모듈 완료 ✅
[x] Phase 3: API 연동 완료 ✅
[x] Phase 4: Agent 로직 완료 ✅
[ ] Phase 5: 통합 및 자동화 완료 (진행 중)
[ ] Phase 6: 성능 최적화 완료
[ ] Phase 7: Jupyter Notebook 완료
[ ] Phase 8: 발표자료 완료

[ ] 최종 테스트 (100장 전체 처리)
[ ] CSV 파일 생성 (UTF-8 인코딩)
[x] README 작성 ✅
[ ] 모든 파일 단일 .ipynb로 통합
[ ] 제출 전 마지막 검수

🎯 제출 완료!
```

---

**작성자**: AI Assistant
**최종 수정**: 2026-01-27
**상태**: Phase 1-4 완료, Phase 5 진행 중
