# multi_model_agent.py 상세 가이드

## 📋 개요

**역할**: Judge-Think-Act-Verify 오케스트레이션을 통한 다중 모델 AI Agent

**핵심 아이디어**: 각 단계마다 최적화된 LLM 모델을 사용하여 반도체 품질 검사의 정확도와 신뢰도를 극대화

## 🏗️ 아키텍처

### 4단계 AI Agent 파이프라인

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ JUDGE   │ -> │ THINK   │ -> │  ACT    │ -> │ VERIFY  │
│gpt-4o-  │    │claude-  │    │gpt-3.5- │    │ gpt-4o  │
│ mini    │    │3.5-son  │    │ turbo   │    │         │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
  빠른 관찰      깊은 추론      빠른 판단      강력한 검증
```

### 모델 선택 근거

| 단계 | 모델 | 선택 이유 | 특징 |
|------|------|-----------|------|
| **JUDGE** | `gpt-4o-mini` | 빠른 비전 분석, 비용 효율 | 초기 결함 감지 (속도 우선) |
| **THINK** | `claude-3.5-sonnet` | 깊이 있는 추론 능력 | 전문가 수준 분석 (품질 우선) |
| **ACT** | `gpt-3.5-turbo` | 빠른 의사결정 | 규칙 기반 빠른 판단 |
| **VERIFY** | `gpt-4o` | 최고 성능 모델 | 최종 검증 (신뢰도 우선) |

## 📂 주요 구성 요소

### 1. 관찰 항목 정의 (OBS_ITEMS)

```python
OBS_ITEMS = [
    ("package_damage", "크랙/파손/깨짐 등 패키지 손상 (치명적 결함)"),
    ("lead_missing_or_broken", "리드 결손/단선 (신뢰성 저하)"),
    ("lead_severe_bend_or_contact", "심한 휨 또는 리드끼리 접촉 (단락 위험)"),
    ("solder_bridge_or_blob", "솔더 브리지 또는 납땜 뭉침 (전기적 결함)"),
    ("misalignment_severe", "소자 위치가 과도하게 틀어짐 (조립 오류)"),
]
```

**특징**:
- 도메인 전문가 지식 반영
- 제조 공정 관점의 분류
- 각 결함의 심각도 가중치 포함

### 2. 결함 심각도 가중치 (DEFECT_SEVERITY)

```python
DEFECT_SEVERITY = {
    "package_damage": 1.0,              # 최고 심각도
    "lead_missing_or_broken": 0.95,     # 매우 심각
    "lead_severe_bend_or_contact": 0.90,
    "solder_bridge_or_blob": 0.85,
    "misalignment_severe": 0.80,        # 상대적으로 낮은 심각도
}
```

**활용**:
- 신뢰도 추정에 사용
- 재검토 여부 결정
- 최종 검증 강도 조절

## 🔧 핵심 함수 상세 설명

### Step 1: JUDGE (judge_step)

**역할**: 빠른 비전 분석으로 초기 결함 감지

```python
def judge_step(img_url: str, strict: bool = False) -> Dict[str, bool]:
    """
    Args:
        img_url: 이미지 URL 또는 base64 data URI
        strict: True면 보수적 판단 (재검토 시 사용)

    Returns:
        {
            "package_damage": False,
            "lead_missing_or_broken": False,
            ...
        }
    """
```

**프롬프트 전략**:
- JSON만 출력하도록 강제 → 파싱 오류 방지
- 도메인 지식 주입 (반도체 제조)
- 각 관찰 항목에 대한 명확한 기준 제시

**출력 예제**:
```json
{
  "package_damage": false,
  "lead_missing_or_broken": true,
  "lead_severe_bend_or_contact": false,
  "solder_bridge_or_blob": false,
  "misalignment_severe": false
}
```

### Step 2: THINK (think_step)

**역할**: Claude의 깊이 있는 추론으로 전문가 수준 분석

```python
def think_step(obs: Dict[str, bool]) -> Dict[str, Any]:
    """
    Args:
        obs: JUDGE 단계의 관찰 결과

    Returns:
        {
            'total_defects': 결함 개수,
            'defect_items': 결함 목록,
            'severity_score': 심각도 점수,
            'has_critical_defect': 치명적 결함 여부,
            'observation_result': 원본 관찰 결과,
            'analysis': LLM 분석 결과,
            'confidence_level': 신뢰도 수준
        }
    """
```

**분석 내용**:
1. 각 결함의 심각도 평가 (1-10 점수)
2. 제조 공정상 원인 분석
3. 신뢰성 영향도 평가
4. 최종 분류 추천 (0 또는 1)

**신뢰도 추정 로직**:
```python
def _estimate_confidence(defect_count: int, has_critical: bool) -> str:
    if has_critical:
        return 'VERY_HIGH'  # 99%
    elif defect_count >= 2:
        return 'HIGH'       # 95%
    elif defect_count == 1:
        return 'MEDIUM'     # 70%
    else:
        return 'LOW'        # 60%
```

### Step 3: ACT (act_step)

**역할**: 빠른 규칙 기반 의사결정

```python
def act_step(reasoning: Dict[str, Any]) -> Tuple[int, bool]:
    """
    Args:
        reasoning: THINK 단계의 추론 결과

    Returns:
        (label, uncertain)
        - label: 0 (Normal) 또는 1 (Abnormal)
        - uncertain: 재검토 필요 여부
    """
```

**판단 규칙**:
```python
# 치명적 결함(패키지, 리드) → 무조건 1(Abnormal)
# 2개 이상 결함 → 1(Abnormal)
# 1개 이상 결함 → 1(Abnormal)
# 결함 없음 → 0(Normal)
```

**불확실성 판단**:
```python
uncertain = (reasoning['total_defects'] == 0) or (reasoning['total_defects'] == 1)
```
- 결함 0개: 놓친 결함이 있을 가능성
- 결함 1개: 경계 케이스 (그림자/노이즈 가능성)

### Step 4: VERIFY (verify_step)

**역할**: GPT-4o로 최종 검증 및 신뢰도 극대화

```python
def verify_step(label: int, reasoning: Dict[str, Any], is_review: bool = False) -> Dict[str, Any]:
    """
    Args:
        label: ACT 단계의 판단 결과
        reasoning: THINK 단계의 추론 결과
        is_review: 재검토 여부

    Returns:
        {
            'verified': True,
            'decision': 최종 판단 (0 또는 1),
            'decision_label': 'Normal' 또는 'Abnormal',
            'confidence': 최종 신뢰도 (0.0-1.0),
            'verification_detail': 검증 상세 정보,
            'reasoning': 판단 근거
        }
    """
```

**검증 체크리스트**:
1. 판단의 논리적 타당성 확인
2. 도메인 지식과의 일치도 검증
3. 놓친 결함이 있을 가능성 평가
4. 신뢰도 점수 재계산

**신뢰도 부스트 로직**:
```python
if is_review and label == LABEL_ABNORMAL:
    final_confidence = min(base_confidence + 0.05, 0.99)
```
- 재검토 후 Abnormal 판정 → 신뢰도 5% 증가

## 🔄 통합 워크플로우

### classify_multi_model_agent()

```python
def classify_multi_model_agent(img_url: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    완전한 다중 모델 Agent 실행

    Returns:
        {
            'prediction': 최종 라벨 (0 또는 1),
            'confidence': 신뢰도,
            'verified': 검증 완료 여부,
            'iterations': 반복 횟수 (1 또는 2),
            'models_used': 사용된 모델 목록
        }
    """
```

### 실행 흐름도

```
START
  ↓
JUDGE (gpt-4o-mini) → obs1
  ↓
THINK (claude) → reasoning1
  ↓
ACT (gpt-3.5-turbo) → label1, uncertain
  ↓
[치명적 결함 OR 확실함]? ──YES──→ VERIFY → END
  ↓NO
[재검토 필요]
  ↓
JUDGE (strict=True) → obs2
  ↓
THINK → reasoning2
  ↓
ACT → label2
  ↓
[치명적 결함 OR Abnormal]? ──YES──→ VERIFY (review) → END
  ↓NO
VERIFY (1차 결과) → END
```

## 📊 실행 예제

### 예제 1: 치명적 결함 (즉시 판정)

```python
# 입력 이미지: 패키지 크랙 명확
img_url = "data:image/png;base64,..."

result = classify_multi_model_agent(img_url)

# 출력:
{
    'prediction': 1,  # Abnormal
    'confidence': 0.99,
    'verified': True,
    'iterations': 1,  # 재검토 없이 즉시 판정
    'models_used': ['gpt-4o-mini', 'claude-3.5-sonnet', 'gpt-3.5-turbo', 'gpt-4o']
}
```

### 예제 2: 경계 케이스 (재검토)

```python
# 입력 이미지: 미세한 리드 휨 (그림자 가능성)
result = classify_multi_model_agent(img_url)

# 출력:
{
    'prediction': 0,  # Normal (재검토 후 정상 판정)
    'confidence': 0.88,
    'verified': True,
    'iterations': 2,  # 재검토 수행
    'models_used': ['gpt-4o-mini', 'claude-3.5-sonnet', 'gpt-3.5-turbo', 'gpt-4o']
}
```

## 🎯 장점 및 특징

### 1. 각 모델의 강점 활용
- **gpt-4o-mini**: 빠른 비전 처리 (비용 효율)
- **claude**: 깊이 있는 추론 (품질)
- **gpt-3.5-turbo**: 빠른 판단 (속도)
- **gpt-4o**: 강력한 검증 (신뢰도)

### 2. 적응형 재검토 메커니즘
- 확실한 경우: 1회 검증으로 종료
- 불확실한 경우: 보수적 재검토 수행
- 치명적 결함: 즉시 판정

### 3. 신뢰도 관리
- 단계별 신뢰도 추적
- 재검토 시 신뢰도 부스트
- 최종 검증으로 품질 보증

### 4. 오류 복구
- 최대 3회 재시도
- 지수 백오프 (Exponential Backoff)
- 네트워크 불안정 대응

## ⚙️ 설정 및 커스터마이징

### 모델 변경

```python
# src/config.py에서 수정
LUXIA_MODELS = {
    'judge': 'gpt-4o-mini',
    'think': 'claude-3.5-sonnet',
    'act': 'gpt-3.5-turbo',
    'verify': 'gpt-4o'
}
```

### 관찰 항목 추가

```python
OBS_ITEMS = [
    # 기존 항목...
    ("새로운_결함", "새로운 결함 설명"),
]

DEFECT_SEVERITY["새로운_결함"] = 0.75  # 심각도 가중치
```

### 신뢰도 임계값 조정

```python
def _estimate_confidence(defect_count, has_critical):
    if has_critical:
        return 'VERY_HIGH'  # 0.99 → 변경 가능
    # ...
```

## 🔍 디버깅 및 로깅

### 로그 레벨 설정

```python
import logging
logging.basicConfig(level=logging.DEBUG)  # 상세 로그
```

### 주요 로그 메시지

```
[JUDGE] Using model: gpt-4o-mini
[THINK] Severity: 0.95, Critical: True
[ACT] Decision: 1, Uncertain: False
[VERIFY] Final Confidence: 0.99
```

## 📈 성능 최적화 팁

### 1. 병렬 처리
```python
# 여러 이미지를 동시에 처리
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(classify_multi_model_agent, image_urls))
```

### 2. 캐싱
```python
# 동일 이미지 재처리 방지
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_classify(img_url):
    return classify_multi_model_agent(img_url)
```

### 3. 타임아웃 조정
```python
# 느린 API 대응
_post_chat_with_model(model, messages, timeout=120)  # 기본 90초 → 120초
```

## 🚀 실행 방법

### 단일 이미지 분류

```bash
python -c "
from src.multi_model_agent import classify_multi_model_agent
result = classify_multi_model_agent('./test/TEST_001.png')
print(result)
"
```

### CSV 배치 처리

```bash
python src/multi_model_agent.py
# data.csv → output/output.csv
```

## 📝 요약

**multi_model_agent.py**는 4개의 최적화된 LLM을 오케스트레이션하여:
1. 빠른 초기 관찰 (JUDGE)
2. 깊이 있는 전문가 분석 (THINK)
3. 신속한 의사결정 (ACT)
4. 강력한 최종 검증 (VERIFY)

을 수행하는 **다중 모델 AI Agent 시스템**입니다.

**핵심 강점**: 각 모델의 장점을 최대한 활용하여 정확도와 신뢰도를 극대화합니다.
