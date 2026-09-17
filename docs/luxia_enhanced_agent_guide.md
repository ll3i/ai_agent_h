# luxia_enhanced_agent.py 상세 가이드

## 📋 개요

**역할**: Luxia Native 모델들(Embeddings, Search, Text Gen, Reranking)을 활용한 향상된 AI Agent

**핵심 아이디어**: 기존 JUDGE-THINK-ACT-VERIFY 파이프라인에 Luxia 고유 기능(RAG, 자동 보고서, 앙상블 최적화)을 추가하여 신뢰도와 품질을 극대화

## 🏗️ 아키텍처

### 강화 계층 구조

```
기존 Agent (JUDGE → THINK → ACT → VERIFY)
    ↓
    + SEARCH (유사 사례 검색 → 신뢰도 부스트)
    + GENERATE (자동 기술 보고서 생성)
    + RERANK (다중 모델 앙상블 최적화)
    ↓
Luxia Enhanced Agent
```

### 4대 핵심 컴포넌트

```
┌──────────────────────────────────────────────────────┐
│         Luxia Enhanced Agent 시스템                   │
├──────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────────┐    ┌──────────────────┐         │
│  │ 1. Knowledge    │    │ 2. Report        │         │
│  │    Base (RAG)   │    │    Generator     │         │
│  │                 │    │                  │         │
│  │ • Embeddings    │    │ • Text Gen       │         │
│  │ • Search        │    │ • Auto Reports   │         │
│  └─────────────────┘    └──────────────────┘         │
│                                                       │
│  ┌─────────────────┐    ┌──────────────────┐         │
│  │ 3. Ensemble     │    │ 4. Integration   │         │
│  │    Reranker     │    │    Layer         │         │
│  │                 │    │                  │         │
│  │ • Multi-Model   │    │ • Complete Flow  │         │
│  │ • Optimization  │    │ • Coordination   │         │
│  └─────────────────┘    └──────────────────┘         │
│                                                       │
└──────────────────────────────────────────────────────┘
```

## 📂 주요 구성 요소

### 1. DefectKnowledgeBase (결함 지식 데이터베이스)

**목적**: 과거 결함 사례들을 임베딩으로 저장하고, 새로운 결함과의 유사도를 검색하여 신뢰도 향상

#### 사례 데이터베이스 구조

```python
defect_cases = [
    {
        'id': 'case_001',                  # 사례 고유 ID
        'description': '패키지에서 미세한 흰색 크랙 발견...',  # 상세 설명
        'severity': 0.95,                  # 심각도 (0.0-1.0)
        'final_label': 1,                  # 최종 판정 (0=Normal, 1=Abnormal)
        'confidence': 0.98,                # 신뢰도
        'keywords': {'crack', 'package', 'damage', ...}  # 키워드 집합
    },
    # ... 5개의 샘플 사례
]
```

**사례 카테고리**:
- **case_001**: 패키지 크랙 (치명적 결함) - severity 0.95
- **case_002**: 솔더 브리지 (전기적 단락 위험) - severity 0.90
- **case_003**: 소자 위치 이탈 (정렬 불량) - severity 0.80
- **case_004**: 정상 사례 (결함 없음) - severity 0.10
- **case_005**: 경미한 휨 (기능상 문제 없음) - severity 0.40

#### 핵심 메서드

##### embed_text() - Luxia Embeddings API 호출

```python
def embed_text(self, text: str) -> List[float]:
    """
    텍스트를 1024차원 벡터로 변환

    API Endpoint: https://bridge.luxiacloud.com/luxia/v1/embedding
    Model: luxia-embedding-small
    Dimension: 1024

    Returns:
        List[float]: 1024차원 임베딩 벡터
    """
```

**API 호출 예시**:
```python
payload = {
    "inputs": ["패키지에서 미세한 크랙이 발견됨"]
}

response = requests.post(
    "https://bridge.luxiacloud.com/luxia/v1/embedding",
    headers={"apikey": API_KEY, "Content-Type": "application/json"},
    json=payload,
    timeout=10
)

embedding = response.json()["data"][0]["embedding"]  # 1024차원 벡터
```

##### similarity_search() - 하이브리드 검색

```python
def similarity_search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    유사 사례 검색 (Keyword-based Jaccard Similarity)

    Args:
        query: 검색 쿼리 (결함 설명)
        top_k: 반환할 상위 사례 개수

    Returns:
        [
            {
                'case': {...},                # 사례 정보
                'similarity_score': 0.75      # 유사도 점수 (0.0-1.0)
            },
            ...
        ]
    """
```

**검색 전략**:
1. **쿼리 키워드 추출**: 3글자 이상 단어 필터링
2. **Jaccard Similarity 계산**: `intersection / union`
3. **정렬**: 유사도 내림차순
4. **Top-K 반환**: 상위 K개 사례

**예시**:
```python
query = "패키지 크랙, 응력 집중"
results = kb.similarity_search(query, top_k=3)

# 출력:
# [
#   {'case': case_001, 'similarity_score': 0.75},  # 패키지 크랙
#   {'case': case_003, 'similarity_score': 0.45},  # 응력 관련
#   {'case': case_004, 'similarity_score': 0.20}   # 일반 사례
# ]
```

##### boost_confidence() - 신뢰도 부스팅

```python
def boost_confidence(self, decision: int, similar_cases: List[Dict]) -> float:
    """
    유사 사례들을 기반으로 신뢰도 향상

    로직:
    1. 같은 판정을 한 사례 개수 계산
    2. 유사도 가중 평균 계산
    3. 신뢰도 부스트 계산 (10% ~ 30%)

    Returns:
        float: 부스트 값 (0.10 ~ 0.30)
    """
```

**계산 공식**:
```
matching_count = 같은 판정을 한 사례 개수
weighted_sum = Σ(같은 판정 사례의 similarity_score)
total_sum = Σ(모든 사례의 similarity_score)

match_rate = weighted_sum / total_sum
boost = 0.10 + (match_rate × 0.20)  # 최소 10%, 최대 30%
```

**예시**:
```python
decision = 1  # Abnormal
similar_cases = [
    {'case': {'final_label': 1}, 'similarity_score': 0.80},  # 일치
    {'case': {'final_label': 1}, 'similarity_score': 0.60},  # 일치
    {'case': {'final_label': 0}, 'similarity_score': 0.40},  # 불일치
]

# 계산:
# weighted_sum = 0.80 + 0.60 = 1.40
# total_sum = 0.80 + 0.60 + 0.40 = 1.80
# match_rate = 1.40 / 1.80 = 0.78
# boost = 0.10 + (0.78 × 0.20) = 0.256 ≈ 0.26

boost = kb.boost_confidence(decision, similar_cases)  # 0.26
```

---

### 2. DefectReportGenerator (자동 보고서 생성)

**목적**: Luxia Text Generation으로 전문적인 기술 보고서 자동 생성

#### 핵심 메서드

##### generate_report() - 보고서 생성

```python
@staticmethod
def generate_report(analysis_result: Dict[str, Any]) -> str:
    """
    분석 결과 → 기술 보고서 자동 생성

    프로세스:
    1. 분석 결과를 자연어로 포맷 (_format_narrative)
    2. Luxia Text Gen 프롬프트 구성
    3. API 호출 (현재는 템플릿 기반 시뮬레이션)
    4. 전문 기술 보고서 반환

    Returns:
        str: 마크다운 형식의 기술 보고서
    """
```

**프롬프트 구조**:
```python
prompt = f"""
다음 반도체 검사 결과를 기반으로 전문적인 기술 보고서를 작성하세요.

[검사 결과]
{narrative}  # 분석 결과 자연어 형식

[보고서 작성 요구사항]
1. 발견된 결함 요약 (한문장)
2. 결함별 상세 설명
3. 심각도 평가
4. 제조 공정상 원인 분석
5. 권장 조치사항

형식: 기술 문서 스타일, 정중한 톤
"""
```

##### _format_narrative() - 자연어 포맷팅

```python
@staticmethod
def _format_narrative(result: Dict[str, Any]) -> str:
    """
    분석 결과를 자연어로 변환

    구조:
    - 이미지 ID 및 검사 시간
    - 발견된 결함 목록
    - 심각도 점수 및 신뢰도
    - 상세 분석 내용
    """
```

**출력 예시**:
```
이미지 ID: DEV_005
검사 시간: 2026-01-27 13:30:00

발견된 결함:
- package_damage
- lead_bend

심각도 점수: 0.85/1.0
신뢰도: 95%

분석 상세:
패키지 손상이 발견되어 즉시 불량 처리 필요
```

##### _template_report() - 템플릿 기반 보고서

```python
@staticmethod
def _template_report(result: Dict[str, Any]) -> str:
    """
    시뮬레이션: 템플릿 기반 전문 보고서

    실제 배포 시: Luxia Text Gen API로 대체
    현재: 구조화된 템플릿 사용
    """
```

**보고서 섹션**:
1. **발견된 결함**: 결함 목록 및 설명
2. **심각도 평가**: 점수 및 등급 (높음/중간/낮음)
3. **원인 분석**: 제조 공정상 가능한 원인
4. **권장 조치**: 개선 방안 및 후속 조치
5. **신뢰도**: 검사 신뢰도 및 생성 방식

**출력 예시**:
```markdown
[기술 검사 보고서]

이미지 ID: DEV_005
검사 일시: 2026-01-27 13:30:00

[1. 발견된 결함]
  - 패키지 손상 (크랙, 파손)
  - 리드 휨

[2. 심각도 평가]
심각도 점수: 0.85/1.0
평가: 높음

[3. 원인 분석]
  패키지 손상: 응력 관리 및 취급 절차 검토 필요
  리드 변형: 취급 과정에서의 물리적 손상

[4. 권장 조치]
- 조립 공정 재검토
- 온도 제어 확인
- 품질 기준 재교육

[5. 신뢰도]
검사 신뢰도: 95%

보고서 생성: 자동화 시스템
```

---

### 3. EnsembleReranker (앙상블 재정렬)

**목적**: 여러 모델의 판정 결과를 Luxia Reranking으로 최적화

#### 핵심 메서드

##### rerank_decisions() - 다중 모델 재정렬

```python
@staticmethod
def rerank_decisions(model_results: List[Dict[str, Any]],
                    context: str) -> Dict[str, Any]:
    """
    여러 모델의 판정을 Luxia Reranking으로 최적화

    Args:
        model_results: [
            {'model': 'gpt-4o-mini', 'decision': 1, 'confidence': 0.85},
            {'model': 'claude', 'decision': 1, 'confidence': 0.90},
            {'model': 'luxia', 'decision': 0, 'confidence': 0.75},
        ]
        context: "Defects: package_damage, lead_bend"

    Returns:
        {
            'decision': 1,
            'confidence': 0.88,
            'score_0': 0.12,
            'score_1': 0.88,
            'method': 'weighted_ensemble'
        }
    """
```

##### _weighted_ensemble() - 가중 앙상블

```python
@staticmethod
def _weighted_ensemble(model_results: List[Dict]) -> Dict[str, Any]:
    """
    모델별 가중치를 고려한 앙상블 최적화

    모델 가중치:
    - gpt-4o: 1.0 (최강 모델)
    - gpt-4o-mini: 1.0 (비전 분석 전문)
    - claude: 0.9 (추론 전문)
    - luxia: 0.8 (한국어 최적)
    - gpt-3.5-turbo: 0.7 (빠른 판단)
    """
```

**앙상블 알고리즘**:
```
For each model_result:
    weight = model_weights[model]
    weighted_value = weight × confidence

    If decision == 0:
        weighted_score_0 += weighted_value
    Else:
        weighted_score_1 += weighted_value

    total_weight += weight

# 정규화
final_confidence_0 = weighted_score_0 / total_weight
final_confidence_1 = weighted_score_1 / total_weight

# 최종 판정
final_decision = 1 if final_confidence_1 > final_confidence_0 else 0
final_confidence = max(final_confidence_0, final_confidence_1)
```

**계산 예시**:
```python
model_results = [
    {'model': 'gpt-4o-mini', 'decision': 1, 'confidence': 0.85},  # weight=1.0
    {'model': 'claude', 'decision': 1, 'confidence': 0.90},       # weight=0.9
    {'model': 'gpt-3.5-turbo', 'decision': 0, 'confidence': 0.75} # weight=0.7
]

# 계산:
# weighted_score_0 = 0.7 × 0.75 = 0.525
# weighted_score_1 = 1.0 × 0.85 + 0.9 × 0.90 = 1.66
# total_weight = 1.0 + 0.9 + 0.7 = 2.6

# final_confidence_0 = 0.525 / 2.6 = 0.20
# final_confidence_1 = 1.66 / 2.6 = 0.64

# final_decision = 1 (0.64 > 0.20)
# final_confidence = 0.64
```

---

### 4. LuxiaEnhancedAgent (통합 강화 Agent)

**목적**: Luxia Native 모델들을 활용한 완전한 강화 시스템

#### 통합 아키텍처

```python
class LuxiaEnhancedAgent:
    def __init__(self):
        self.kb = DefectKnowledgeBase()        # RAG 검색
        self.report_gen = DefectReportGenerator()  # 자동 보고서
        self.reranker = EnsembleReranker()     # 앙상블 최적화
```

#### 핵심 메서드

##### enhance_decision() - 신뢰도 향상

```python
def enhance_decision(self,
                    decision: int,
                    confidence: float,
                    defect_description: str,
                    analysis_result: Dict[str, Any]) -> Tuple[int, float]:
    """
    Luxia Embeddings + Search로 신뢰도 향상

    프로세스:
    1. 유사 사례 검색 (similarity_search)
    2. 신뢰도 부스트 계산 (boost_confidence)
    3. 향상된 신뢰도 반환 (최대 0.99)

    Returns:
        (decision, enhanced_confidence)
    """
```

**워크플로우**:
```
Input: decision=1, confidence=0.85, description="패키지 크랙"
  ↓
1. 유사 사례 검색
   → similar_cases = [case_001 (0.75), case_002 (0.45), ...]
  ↓
2. 신뢰도 부스트 계산
   → boost = 0.12 (12%)
  ↓
3. 향상된 신뢰도
   → enhanced_confidence = min(0.85 + 0.12, 0.99) = 0.97
  ↓
Output: (1, 0.97)
```

##### generate_full_report() - 완전한 보고서 생성

```python
def generate_full_report(self,
                       analysis_result: Dict[str, Any],
                       model_results: List[Dict],
                       final_decision: int) -> str:
    """
    최종 분석 결과 + 여러 모델 판정 + 자동 보고서 생성

    프로세스:
    1. 여러 모델 결과 재정렬 (rerank_decisions)
    2. 최종 결과 통합
    3. 전문 보고서 생성 (generate_report)

    Returns:
        str: 완전한 기술 보고서
    """
```

**통합 데이터 구조**:
```python
enhanced_result = {
    # 원본 분석 결과
    'image_id': 'DEV_005',
    'defects': ['package_damage'],
    'severity': 0.85,

    # 추가된 정보
    'final_decision': 1,
    'ensemble_analysis': {
        'decision': 1,
        'confidence': 0.88,
        'method': 'weighted_ensemble'
    },
    'model_votes': [
        {'model': 'gpt-4o-mini', 'decision': 1, 'confidence': 0.85},
        {'model': 'claude', 'decision': 1, 'confidence': 0.90},
    ]
}
```

##### process_complete() - 완전한 처리 파이프라인

```python
def process_complete(self,
                    img_url: str,
                    initial_analysis: Dict[str, Any],
                    model_results: List[Dict]) -> Dict[str, Any]:
    """
    완전한 처리: 분석 → 향상 → 보고서 → 최종 결과

    통합 워크플로우:
    1. 초기 판정 추출
    2. 신뢰도 향상 (enhance_decision)
    3. 자동 보고서 생성 (generate_full_report)
    4. 최종 결과 반환

    Returns:
        {
            'final_decision': 1,
            'confidence': 0.97,
            'report': "...",
            'enhancements_applied': [
                'semantic_search',
                'text_generation',
                'reranking'
            ]
        }
    """
```

---

## 🔄 통합 워크플로우

### 전체 실행 흐름

```
┌─────────────────────────────────────────────┐
│      초기 분석 결과 (Judge-Think-Act)        │
│  decision=1, confidence=0.85, defects=[...] │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  Step 1: enhance_decision()                 │
│  • similarity_search(description)           │
│  • boost_confidence(decision, cases)        │
│  → enhanced_confidence = 0.97               │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  Step 2: generate_full_report()             │
│  • rerank_decisions(model_results)          │
│  • 최종 결과 통합                            │
│  • generate_report(enhanced_result)         │
│  → professional_report                      │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│        최종 결과 (LuxiaEnhancedAgent)        │
│  final_decision: 1                          │
│  confidence: 0.97                           │
│  report: "..."                              │
│  enhancements: [search, gen, rerank]        │
└─────────────────────────────────────────────┘
```

---

## 📊 실행 예제

### 예제 1: 신뢰도 향상

```python
from src.luxia_enhanced_agent import LuxiaEnhancedAgent

agent = LuxiaEnhancedAgent()

# 초기 분석 결과
analysis_result = {
    'image_id': 'DEV_005',
    'timestamp': '2026-01-27 13:30:00',
    'description': '패키지에서 미세한 크랙이 발견됨, 응력 집중점',
    'defects': ['package_damage', 'lead_bend'],
    'severity': 0.85,
    'analysis': '패키지 손상이 발견되어 즉시 불량 처리 필요'
}

# 신뢰도 향상
decision, enhanced_conf = agent.enhance_decision(
    decision=1,
    confidence=0.85,
    defect_description='패키지 크랙, 응력 집중',
    analysis_result=analysis_result
)

# 출력:
# [ENHANCE] Searching similar cases...
#   [SEARCH] Similar cases: 2/3
#   [SEARCH] Confidence boost: +0.12
#   Original confidence: 0.85
#   Enhanced confidence: 0.97

print(f"판정: {decision}, 신뢰도: {enhanced_conf:.2f}")
# 출력: 판정: 1, 신뢰도: 0.97
```

### 예제 2: 자동 보고서 생성

```python
# 여러 모델의 판정
model_results = [
    {'model': 'gpt-4o-mini', 'decision': 1, 'confidence': 0.85},
    {'model': 'claude', 'decision': 1, 'confidence': 0.90},
    {'model': 'gpt-3.5-turbo', 'decision': 0, 'confidence': 0.75},
]

# 자동 보고서 생성
analysis_result['confidence'] = enhanced_conf
report = agent.generate_full_report(analysis_result, model_results, decision)

print(report)
# 출력:
# [기술 검사 보고서]
#
# 이미지 ID: DEV_005
# 검사 일시: 2026-01-27 13:30:00
#
# [1. 발견된 결함]
#   - 패키지 손상 (크랙, 파손)
#   - 리드 휨
# ...
```

### 예제 3: 완전한 처리 파이프라인

```python
# 완전한 처리
final_result = agent.process_complete(
    img_url='./test/DEV_005.png',
    initial_analysis=analysis_result,
    model_results=model_results
)

print(f"[최종 결과]")
print(f"판정: {final_result['final_decision']}")
print(f"신뢰도: {final_result['confidence']:.2f}")
print(f"적용된 강화: {final_result['enhancements_applied']}")

# 출력:
# [최종 결과]
# 판정: 1
# 신뢰도: 0.97
# 적용된 강화: ['semantic_search', 'text_generation', 'reranking']
```

---

## 🎯 장점 및 특징

### 1. RAG (Retrieval-Augmented Generation)
- **과거 사례 활용**: 5개 샘플 사례 데이터베이스
- **유사도 검색**: Jaccard Similarity 기반 키워드 매칭
- **신뢰도 부스트**: 10% ~ 30% 향상
- **확장 가능**: Luxia Embeddings API로 확장 가능

### 2. 자동 보고서 생성
- **전문 문서**: 5개 섹션 구조화 보고서
- **템플릿 시스템**: 즉시 사용 가능한 템플릿
- **Luxia Text Gen 준비**: API 연동 코드 포함
- **다국어 지원**: 한국어 기본, 확장 가능

### 3. 앙상블 최적화
- **다중 모델 통합**: 5개 모델 지원
- **가중치 기반**: 모델별 특성 반영
- **정규화**: 0.0-1.0 범위 신뢰도
- **Reranking 준비**: Luxia API 연동 준비

### 4. 통합 시스템
- **3단계 강화**: Search → Generate → Rerank
- **완전한 파이프라인**: 입력 → 분석 → 강화 → 보고서
- **모듈화 설계**: 개별 컴포넌트 독립 사용 가능
- **확장성**: 새로운 모델/기능 추가 용이

---

## ⚙️ 설정 및 커스터마이징

### API 설정

```python
# .env 파일
SALTLUX_API_KEY=your_api_key_here

# luxia_enhanced_agent.py
EMBEDDING_API_URL = "https://bridge.luxiacloud.com/luxia/v1/embedding"
HEADERS = {"apikey": API_KEY, "Content-Type": "application/json"}
```

### 사례 데이터베이스 확장

```python
# 새로운 사례 추가
new_case = {
    'id': 'case_006',
    'description': '리드 3개 중 1개 완전 절단, 연결 불가',
    'severity': 1.0,
    'final_label': 1,
    'confidence': 0.99,
    'keywords': {'lead', 'cut', 'broken', 'missing', 'connectivity'}
}

kb = DefectKnowledgeBase()
kb.defect_cases.append(new_case)
```

### 모델 가중치 조정

```python
# EnsembleReranker._weighted_ensemble()
model_weights = {
    'gpt-4o-mini': 1.0,
    'claude': 0.9,
    'gpt-3.5-turbo': 0.7,
    'luxia': 0.8,
    'gpt-4o': 1.0,
    'custom-model': 0.85,  # 새로운 모델 추가
}
```

### 신뢰도 부스트 범위 변경

```python
# DefectKnowledgeBase.boost_confidence()
# 기본: 10% ~ 30%
boost = 0.10 + (match_rate * 0.20)

# 더 공격적: 15% ~ 40%
boost = 0.15 + (match_rate * 0.25)

# 더 보수적: 5% ~ 15%
boost = 0.05 + (match_rate * 0.10)
```

---

## 🔍 디버깅 및 로깅

### 로그 레벨 설정

```python
import logging
logging.basicConfig(level=logging.INFO)  # INFO 레벨 로그
```

### 주요 로그 메시지

```
[ENHANCE] Searching similar cases...
  [SEARCH] Similar cases: 2/3
  [SEARCH] Confidence boost: +0.12
  Original confidence: 0.85
  Enhanced confidence: 0.97

[RERANK] Score 0: 0.20, Score 1: 0.64
[RERANK] Final decision: 1, Confidence: 0.64

[GENERATE] Creating technical report...
```

---

## 📈 성능 최적화 팁

### 1. 임베딩 캐싱
```python
from functools import lru_cache

class DefectKnowledgeBase:
    @lru_cache(maxsize=100)
    def embed_text(self, text: str) -> List[float]:
        # 동일 텍스트 재호출 방지
        pass
```

### 2. 사례 데이터베이스 사전 임베딩
```python
def __init__(self):
    # 시작 시 모든 사례 임베딩 (한 번만)
    for case in self.defect_cases:
        case['embedding'] = self.embed_text(case['description'])
```

### 3. 병렬 처리
```python
from concurrent.futures import ThreadPoolExecutor

def batch_enhance(self, decisions: List[Dict]) -> List[Dict]:
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(self.enhance_decision, decisions))
    return results
```

---

## 🚀 실행 방법

### 단일 이미지 처리

```bash
python -c "
from src.luxia_enhanced_agent import LuxiaEnhancedAgent
agent = LuxiaEnhancedAgent()
result = agent.process_complete(
    './test/TEST_001.png',
    {'description': 'sample'},
    [{'model': 'gpt-4o', 'decision': 1, 'confidence': 0.85}]
)
print(result)
"
```

### 스크립트 모드

```bash
python src/luxia_enhanced_agent.py
```

---

## 📝 요약

**luxia_enhanced_agent.py**는 Luxia Native 모델들(Embeddings, Text Gen, Reranking)을 활용하여:

1. **RAG 검색**: 과거 사례와의 유사도 기반 신뢰도 향상 (10-30%)
2. **자동 보고서**: 전문 기술 문서 자동 생성
3. **앙상블 최적화**: 다중 모델 결과의 가중 평균 최적화
4. **통합 시스템**: 3단계 강화 파이프라인 완성

을 수행하는 **Luxia 강화 AI Agent 시스템**입니다.

**핵심 강점**: Luxia 고유 기능들을 최대한 활용하여 기존 Agent의 신뢰도와 품질을 극대화합니다.
