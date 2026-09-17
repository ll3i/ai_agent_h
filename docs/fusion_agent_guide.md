# fusion_agent.py 상세 가이드

## 📋 개요

**역할**: 3가지 방식의 장점을 결합한 Fusion Agent - Single-Agent(높은 Recall) + Triple Vision(균형) + J-T-A-V(높은 Precision)

**핵심 아이디어**: 각 방식의 강점을 살리고 약점을 보완하는 3단계 Adaptive 전략으로 False Positive와 False Negative를 동시에 최소화

## 🏗️ 아키텍처

### 3가지 방식의 장단점 분석

| 방식 | 강점 | 약점 | 활용 시점 |
|------|------|------|-----------|
| **Single-Agent** | Recall 높음 (FN=6) | FP 많음 (과도한 민감도) | Normal 재검증 |
| **Triple Vision** | 균형잡힌 성능 (72%) | 경계 케이스 취약 | 기본 판정 |
| **J-T-A-V** | Precision 높음 (FP=1) | 계산 비용 높음 | Abnormal 검증 |

### Fusion 전략

```
┌─────────────────────────────────────────────────────────┐
│              Fusion Agent 3-Step Strategy                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Step 1: Balanced Check (Triple Vision)                 │
│  ┌────────────────────────────────────────────┐         │
│  │ 3개 이미지 분석 (Full + Body + Lead)        │         │
│  │ → 균형잡힌 기본 판정                         │         │
│  └────────┬───────────────────────────────────┘         │
│           ↓                                              │
│     ┌─────────────┐                                      │
│     │ 결함 개수?  │                                      │
│     └─────┬───────┘                                      │
│           ↓                                              │
│  ┌────────┴────────┬────────────────────┐               │
│  │ 0개 (Normal)    │ 1개 (경계)         │ 2개+ (다중)   │
│  ↓                 ↓                    ↓               │
│                                                          │
│  Step 2: Sensitive Recheck (FN 방지)                    │
│  ┌────────────────────────────────────────────┐         │
│  │ 민감도 증가 재검사 (놓친 결함 탐지)         │         │
│  │ → "과도하게 찾기" 모드                      │         │
│  └────────┬───────────────────────────────────┘         │
│           ↓                                              │
│     ┌─────────────┐                                      │
│     │ 결함 발견?  │                                      │
│     └─────┬───────┘                                      │
│           ↓                                              │
│  ┌────────┴────────┐                                    │
│  │ Yes → Abnormal  │ No → Normal (Double-checked)       │
│  └─────────────────┘                                    │
│                                                          │
│  Step 3: Precision Verify (FP 방지)                     │
│  ┌────────────────────────────────────────────┐         │
│  │ 정밀 검증 (실제 결함 vs 그림자/노이즈)      │         │
│  │ → "엄격하게 검증" 모드                      │         │
│  └────────┬───────────────────────────────────┘         │
│           ↓                                              │
│     ┌─────────────┐                                      │
│     │ 실제 결함?  │                                      │
│     └─────┬───────┘                                      │
│           ↓                                              │
│  ┌────────┴────────┐                                    │
│  │ Yes → Abnormal  │ No → Normal (False alarm)          │
│  └─────────────────┘                                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Triple Vision 이미지 전략

```
원본 이미지 (Full View)
    ↓
┌────────────────────────────────┐
│ crop_body_roi()  crop_lead_roi()│
├──────────────────┬──────────────┤
│ Body Zoom        │ Lead Zoom    │
│ (패키지 중심 확대)│ (리드 영역 확대)│
└──────────────────┴──────────────┘
        ↓
3개 이미지를 동시에 LLM에 전달
→ 종합적 분석
```

## 📂 주요 구성 요소

### 1. 프롬프트 시스템

#### BALANCED_PROMPT (균형잡힌 기본 분석)

```python
BALANCED_PROMPT = """
You are analyzing a **TO-92 Transistor** with **3 IMAGES**:
【IMAGE 1】Full view  【IMAGE 2】Body zoom  【IMAGE 3】Lead zoom

【DEFECT DETECTION】
1. component_missing: Black body completely absent?
2. lead_connectivity_fail: Any lead cut, broken, touching, or missing? (EXACTLY 3 leads required)
3. body_broken_severe: Internal chip exposed through damage?
4. posture_bad: Component lying down or upside down?
5. rotation_severe: Rotation >= 45 degrees?

【BACKGROUND】
- Orange stripboard with horizontal copper traces
- IGNORE copper traces, focus on VERTICAL leads

Output ONLY this JSON:
{"component_missing": false, "lead_connectivity_fail": false, ...}
"""
```

**특징**:
- 5개 핵심 결함 분류
- 3개 이미지 동시 분석
- JSON 출력 강제 (파싱 오류 방지)
- 배경 노이즈 무시 가이드

#### SENSITIVE_PROMPT (민감도 증가 재검사)

```python
SENSITIVE_PROMPT = """
⚠️ SECOND CHECK - BE AGGRESSIVE! ⚠️

Look at the 3 images again. The first check said NORMAL.
Your job: Find ANY defect that was MISSED!

CHECK VERY CAREFULLY:
- Are there EXACTLY 3 leads visible?
- Is ANY lead shorter, bent, or damaged?
- Do the leads look unusual in ANY way?
- Is the component rotated or tilted?

RULE: If ANYTHING looks suspicious → Mark TRUE!
RULE: When uncertain → Mark TRUE (over-detect is better!)

Output ONLY this JSON:
{"lead_connectivity_fail": false, "any_defect_found": false}
"""
```

**특징**:
- 공격적 탐지 모드 ("과도하게 찾기")
- 불확실할 때 결함으로 판정
- 리드 연결성 집중 검사
- FN(놓침) 최소화 목표

#### PRECISION_PROMPT (정밀 검증)

```python
PRECISION_PROMPT = """
⚠️ VERIFICATION CHECK - BE STRICT! ⚠️

Previous check detected: {defect_type}

Look at the 3 images CAREFULLY. Is this a REAL defect or just a shadow/noise?

REAL DEFECT:
- Physical gap or break in the lead
- Lead is truly missing or cut
- Clear damage visible

SHADOW/NOISE (NOT a defect):
- Dark area but lead is continuous
- Lead goes from body to board without break
- Just lighting/shadow effect

Output ONLY this JSON:
{"is_real_defect": true, "reason": "explanation"}
"""
```

**특징**:
- 엄격한 검증 모드
- 실제 결함 vs 그림자/노이즈 구분
- 물리적 손상 여부 확인
- FP(오탐) 최소화 목표

### 2. 이미지 처리 함수

#### _prepare_images() - 3개 이미지 준비

```python
def _prepare_images(image_path: str) -> Tuple[str, str, str]:
    """
    이미지 로드 및 Base64 인코딩

    Returns:
        (full_b64, body_b64, lead_b64)
    """
    full_bytes = _load_image_bytes(image_path)
    body_bytes = crop_body_roi(image_path)  # src/roi_cropper.py
    lead_bytes = crop_lead_roi(image_path)  # src/roi_cropper.py

    return (
        base64.b64encode(full_bytes).decode('utf-8'),
        base64.b64encode(body_bytes).decode('utf-8'),
        base64.b64encode(lead_bytes).decode('utf-8')
    )
```

**ROI Cropping 전략**:
- **Body ROI**: 패키지 중심부 확대 (크랙, 손상 감지)
- **Lead ROI**: 리드 영역 확대 (연결성, 휨 감지)
- **Full View**: 전체 맥락 파악 (정렬, 자세)

#### _build_image_content() - 메시지 구성

```python
def _build_image_content(full_b64: str, body_b64: str, lead_b64: str, prompt: str) -> list:
    """3개 이미지 + 프롬프트 메시지 구성"""
    return [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{full_b64}"}},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{body_b64}"}},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{lead_b64}"}}
    ]
```

### 3. API 통신 함수

#### _post_chat() - LLM API 호출

```python
def _post_chat(messages, timeout=90) -> str:
    """LLM API 호출"""
    payload = {
        "model": MODEL,  # luxia3-llm-32b-0731
        "messages": messages,
        "stream": False
    }

    r = requests.post(BRIDGE_URL, headers=HEADERS, json=payload, timeout=timeout)

    if r.status_code != 200:
        raise RuntimeError(f"API Error: {r.status_code}")

    return r.json()["choices"][0]["message"]["content"].strip()
```

#### _safe_json_extract() - JSON 안전 추출

```python
def _safe_json_extract(s: str) -> dict:
    """JSON 안전 추출 (LLM 응답 파싱)"""
    try:
        return json.loads(s)
    except:
        # Fallback: 정규식으로 JSON 찾기
        m = re.search(r"\{.*\}", s, flags=re.S)
        if m:
            return json.loads(m.group(0))
    return {}
```

---

## 🔧 핵심 함수 상세 설명

### Step 1: step1_balanced_check()

**역할**: Triple Vision 균형잡힌 기본 분석

```python
def step1_balanced_check(full_b64: str, body_b64: str, lead_b64: str) -> Dict:
    """
    Step 1: Triple Vision 균형 잡힌 기본 분석

    프로세스:
    1. 3개 이미지 + BALANCED_PROMPT 구성
    2. LLM API 호출
    3. JSON 응답 파싱

    Returns:
        {
            "component_missing": false,
            "lead_connectivity_fail": false,
            "body_broken_severe": false,
            "posture_bad": false,
            "rotation_severe": false
        }
    """
    logger.info("  [Step1] Balanced Triple Vision check...")

    response = _post_chat([
        {"role": "system", "content": "You are a quality inspector."},
        {"role": "user", "content": _build_image_content(full_b64, body_b64, lead_b64, BALANCED_PROMPT)}
    ])

    result = _safe_json_extract(response)
    logger.info(f"  [Step1] Result: {result}")
    return result
```

**출력 예시**:
```python
# Normal 케이스
{
    "component_missing": False,
    "lead_connectivity_fail": False,
    "body_broken_severe": False,
    "posture_bad": False,
    "rotation_severe": False
}

# Abnormal 케이스 (리드 연결 문제)
{
    "component_missing": False,
    "lead_connectivity_fail": True,  # ← 결함 발견
    "body_broken_severe": False,
    "posture_bad": False,
    "rotation_severe": False
}
```

---

### Step 2: step2_sensitive_recheck()

**역할**: Normal 판정 시 민감도 증가 재검사 (FN 방지)

```python
def step2_sensitive_recheck(full_b64: str, body_b64: str, lead_b64: str) -> bool:
    """
    Step 2: Normal 판정 시 민감도 증가 재검사 (FN 방지)

    전략:
    - 공격적 탐지 모드 (over-detect)
    - 불확실하면 결함으로 판정
    - 리드 연결성 집중 검사

    Returns:
        bool: True = 놓친 결함 발견, False = 정말 정상
    """
    logger.info("  [Step2] Sensitive recheck for missed defects...")

    response = _post_chat([
        {"role": "system", "content": "You are an AGGRESSIVE defect finder. Find what was missed!"},
        {"role": "user", "content": _build_image_content(full_b64, body_b64, lead_b64, SENSITIVE_PROMPT)}
    ])

    result = _safe_json_extract(response)
    any_defect = result.get("lead_connectivity_fail", False) or result.get("any_defect_found", False)

    logger.info(f"  [Step2] Defect found: {any_defect}")
    return any_defect
```

**동작 시나리오**:

**시나리오 1: 놓친 결함 발견**
```
Step1 결과: 모든 결함 False (Normal)
  ↓
Step2 실행: "리드 3개 중 하나가 짧아 보임, 연결 불확실"
  ↓
Step2 판정: lead_connectivity_fail=True (공격적 모드)
  ↓
최종 결과: ABNORMAL (FN 방지 성공)
```

**시나리오 2: 정말 정상**
```
Step1 결과: 모든 결함 False (Normal)
  ↓
Step2 실행: "3개 리드 모두 정상, 패키지 손상 없음"
  ↓
Step2 판정: any_defect_found=False
  ↓
최종 결과: NORMAL (double-checked)
```

---

### Step 3: step3_precision_verify()

**역할**: Abnormal 판정 시 정밀 검증 (FP 방지)

```python
def step3_precision_verify(full_b64: str, body_b64: str, lead_b64: str, defect_type: str) -> bool:
    """
    Step 3: Abnormal 판정 시 정밀 검증 (FP 방지)

    전략:
    - 실제 결함 vs 그림자/노이즈 구분
    - 물리적 손상 여부 확인
    - 엄격한 검증 모드

    Args:
        defect_type: "lead_connectivity_fail", "body_broken_severe" 등

    Returns:
        bool: True = 실제 결함, False = 오탐 (그림자/노이즈)
    """
    logger.info(f"  [Step3] Precision verification for: {defect_type}")

    prompt = PRECISION_PROMPT.format(defect_type=defect_type)

    response = _post_chat([
        {"role": "system", "content": "You are a strict quality verifier."},
        {"role": "user", "content": _build_image_content(full_b64, body_b64, lead_b64, prompt)}
    ])

    result = _safe_json_extract(response)
    is_real = result.get("is_real_defect", True)  # 기본값: True (보수적)
    reason = result.get("reason", "N/A")

    logger.info(f"  [Step3] Real defect: {is_real}, Reason: {reason}")
    return is_real
```

**검증 시나리오**:

**시나리오 1: 실제 결함**
```
Step1 결과: lead_connectivity_fail=True (단일 결함)
  ↓
Step3 실행: "리드 중간에 물리적 절단 확인, 명확한 갭"
  ↓
Step3 판정: is_real_defect=True, reason="Physical gap visible"
  ↓
최종 결과: ABNORMAL (실제 결함 확정)
```

**시나리오 2: 오탐 (그림자)**
```
Step1 결과: lead_connectivity_fail=True (단일 결함)
  ↓
Step3 실행: "어두운 영역이지만 리드는 연속적, 그림자 효과"
  ↓
Step3 판정: is_real_defect=False, reason="Shadow effect, lead is continuous"
  ↓
최종 결과: NORMAL (FP 방지 성공)
```

---

## 🔄 통합 워크플로우

### classify_fusion() - 메인 분류 함수

```python
def classify_fusion(image_path: str) -> Tuple[int, str]:
    """
    Fusion Agent: 3가지 방식의 장점 결합

    Returns:
        (label, reason)
        - label: 0 (Normal) 또는 1 (Abnormal)
        - reason: 판정 근거
    """
    logger.info(f"[FUSION] Classifying: {image_path}")

    try:
        # 이미지 준비
        full_b64, body_b64, lead_b64 = _prepare_images(image_path)

        # Step 1: 균형 잡힌 기본 분석
        step1_result = step1_balanced_check(full_b64, body_b64, lead_b64)

        # 결함 목록 추출
        defects = [k for k, v in step1_result.items() if v]

        if len(defects) == 0:
            # Normal 판정 → Step 2: 민감도 증가 재검사
            has_missed_defect = step2_sensitive_recheck(full_b64, body_b64, lead_b64)

            if has_missed_defect:
                logger.info("  [FUSION] Step2 found missed defect → ABNORMAL")
                return 1, "Defect found in sensitive recheck"
            else:
                logger.info("  [FUSION] No defects in both checks → NORMAL")
                return 0, "No defects found (double-checked)"

        elif len(defects) >= 2:
            # 다중 결함 → 즉시 ABNORMAL
            logger.info(f"  [FUSION] Multiple defects ({len(defects)}) → ABNORMAL")
            return 1, f"Multiple defects: {', '.join(defects)}"

        else:
            # 단일 결함 → Step 3: 정밀 검증 (FP 방지)
            defect_type = defects[0]
            is_real = step3_precision_verify(full_b64, body_b64, lead_b64, defect_type)

            if is_real:
                logger.info(f"  [FUSION] Single defect verified → ABNORMAL")
                return 1, f"Verified defect: {defect_type}"
            else:
                logger.info(f"  [FUSION] Single defect rejected (shadow) → NORMAL")
                return 0, f"Rejected as shadow: {defect_type}"

    except Exception as e:
        logger.error(f"  [ERROR] {e}")
        return 0, f"Error: {e}"
```

### 실행 흐름도

```
START: classify_fusion(image_path)
  ↓
이미지 준비 (Full + Body + Lead)
  ↓
┌──────────────────────────────────────┐
│ Step 1: Balanced Check               │
│ → 5개 결함 분류                       │
└──────────┬───────────────────────────┘
           ↓
     결함 개수 평가
           ↓
  ┌────────┴────────┬─────────────┐
  │ 0개             │ 1개         │ 2개+
  ↓                 ↓             ↓
┌──────────────┐  ┌─────────┐  ┌──────────┐
│ Step 2:      │  │ Step 3: │  │ 즉시     │
│ Sensitive    │  │Precision│  │ ABNORMAL │
│ Recheck      │  │ Verify  │  └──────────┘
└──┬───────────┘  └────┬────┘
   ↓                   ↓
┌──┴──────┐      ┌─────┴─────┐
│놓친 결함?│      │실제 결함? │
└──┬──────┘      └─────┬─────┘
   ↓                   ↓
┌──┴──────────┐  ┌─────┴──────────┐
│Yes→ABNORMAL │  │Yes→ABNORMAL    │
│No→NORMAL    │  │No→NORMAL(FP방지)│
└─────────────┘  └────────────────┘
```

---

## 📊 실행 예제

### 예제 1: Normal 케이스 (double-checked)

```python
from src.fusion_agent import classify_fusion

label, reason = classify_fusion('./test/TEST_000.png')

# 로그 출력:
# [FUSION] Classifying: ./test/TEST_000.png
#   [Step1] Balanced Triple Vision check...
#   [Step1] Result: {'component_missing': False, 'lead_connectivity_fail': False, ...}
#   [Step2] Sensitive recheck for missed defects...
#   [Step2] Defect found: False
#   [FUSION] No defects in both checks → NORMAL

print(f"Result: {label}, Reason: {reason}")
# 출력: Result: 0, Reason: No defects found (double-checked)
```

### 예제 2: 놓친 결함 발견 (FN 방지)

```python
label, reason = classify_fusion('./test/TEST_022.png')

# 로그 출력:
# [FUSION] Classifying: ./test/TEST_022.png
#   [Step1] Balanced Triple Vision check...
#   [Step1] Result: {'component_missing': False, ...} (모두 False)
#   [Step2] Sensitive recheck for missed defects...
#   [Step2] Defect found: True  # ← 재검사에서 발견
#   [FUSION] Step2 found missed defect → ABNORMAL

print(f"Result: {label}, Reason: {reason}")
# 출력: Result: 1, Reason: Defect found in sensitive recheck
```

### 예제 3: 다중 결함 (즉시 판정)

```python
label, reason = classify_fusion('./test/TEST_045.png')

# 로그 출력:
# [FUSION] Classifying: ./test/TEST_045.png
#   [Step1] Balanced Triple Vision check...
#   [Step1] Result: {'lead_connectivity_fail': True, 'posture_bad': True, ...}
#   [FUSION] Multiple defects (2) → ABNORMAL

print(f"Result: {label}, Reason: {reason}")
# 출력: Result: 1, Reason: Multiple defects: lead_connectivity_fail, posture_bad
```

### 예제 4: 단일 결함 검증 (FP 방지)

```python
label, reason = classify_fusion('./test/TEST_012.png')

# 로그 출력:
# [FUSION] Classifying: ./test/TEST_012.png
#   [Step1] Balanced Triple Vision check...
#   [Step1] Result: {'lead_connectivity_fail': True, ...} (단일 결함)
#   [Step3] Precision verification for: lead_connectivity_fail
#   [Step3] Real defect: False, Reason: Shadow effect, lead is continuous
#   [FUSION] Single defect rejected (shadow) → NORMAL

print(f"Result: {label}, Reason: {reason}")
# 출력: Result: 0, Reason: Rejected as shadow: lead_connectivity_fail
```

---

## 🎯 장점 및 특징

### 1. Adaptive 3-Step 전략
- **Step 1**: 균형잡힌 기본 분석 (Triple Vision)
- **Step 2**: 민감도 증가 재검사 (FN 방지)
- **Step 3**: 정밀 검증 (FP 방지)

### 2. Triple Vision 이미지 전략
- **Full View**: 전체 맥락 파악
- **Body Zoom**: 패키지 손상 확대
- **Lead Zoom**: 리드 연결성 확대

### 3. 오류 최소화
- **FN 감소**: Step 2의 공격적 재검사
- **FP 감소**: Step 3의 엄격한 검증
- **경계 케이스 처리**: 단일 결함 특별 처리

### 4. 효율성
- **Normal 케이스**: 2단계 (Step 1 + Step 2)
- **다중 결함**: 1단계 (Step 1 → 즉시 판정)
- **단일 결함**: 2단계 (Step 1 + Step 3)

---

## ⚙️ 설정 및 커스터마이징

### API 설정

```python
# .env 파일
SALTLUX_API_KEY=your_api_key_here
MODEL_JUDGE=luxia3-llm-32b-0731

# fusion_agent.py
BRIDGE_URL = os.getenv('SALTLUX_API_BASE_URL',
    'https://bridge.luxiacloud.com/llm/openai/chat/completions/{model}/create')
```

### 프롬프트 커스터마이징

```python
# 더 공격적인 Step 2
SENSITIVE_PROMPT = """
ULTRA AGGRESSIVE MODE!
Mark TRUE if ANYTHING seems even SLIGHTLY unusual!
"""

# 더 보수적인 Step 3
PRECISION_PROMPT = """
SUPER STRICT MODE!
Only mark as real defect if 100% certain!
When in doubt, mark as shadow/noise.
"""
```

### 결함 카테고리 추가

```python
# BALANCED_PROMPT에 새로운 결함 추가
6. surface_contamination: Visible dirt or foreign material?
```

---

## 🔍 디버깅 및 로깅

### 로그 레벨 설정

```python
import logging
logging.basicConfig(level=logging.INFO)
```

### 주요 로그 메시지

```
[FUSION] Classifying: ./test/TEST_001.png
  [Step1] Balanced Triple Vision check...
  [Step1] Result: {'component_missing': False, ...}
  [Step2] Sensitive recheck for missed defects...
  [Step2] Defect found: True
  [FUSION] Step2 found missed defect → ABNORMAL
```

---

## 📈 성능 최적화 팁

### 1. 이미지 캐싱
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def _prepare_images_cached(image_path: str):
    return _prepare_images(image_path)
```

### 2. 병렬 처리
```python
from concurrent.futures import ThreadPoolExecutor

def batch_classify(image_paths: List[str]) -> List[Tuple[int, str]]:
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(classify_fusion, image_paths))
    return results
```

### 3. Step 건너뛰기 최적화
```python
# 다중 결함 즉시 판정 (Step 2, 3 생략)
if len(defects) >= 2:
    return 1, f"Multiple defects: {', '.join(defects)}"
```

---

## 🚀 실행 방법

### 단일 이미지 분류

```bash
python src/fusion_agent.py ./test/TEST_001.png
```

### 배치 처리

```python
from src.fusion_agent import classify_fusion
import pandas as pd

df = pd.read_csv('test.csv')
results = []

for idx, row in df.iterrows():
    label, reason = classify_fusion(row['img_url'])
    results.append({'id': row['id'], 'label': label, 'reason': reason})

pd.DataFrame(results).to_csv('output_fusion.csv', index=False)
```

---

## 📝 요약

**fusion_agent.py**는 3가지 방식의 장점을 결합하여:

1. **Triple Vision**: 3개 이미지 동시 분석 (Full + Body + Lead)
2. **Adaptive Strategy**: 3단계 적응형 전략 (Balanced → Sensitive → Precision)
3. **FN 방지**: Step 2의 공격적 재검사로 놓친 결함 발견
4. **FP 방지**: Step 3의 엄격한 검증으로 오탐 제거

을 수행하는 **Fusion AI Agent 시스템**입니다.

**핵심 강점**: Single-Agent(높은 Recall), Triple Vision(균형), J-T-A-V(높은 Precision)의 장점을 상황에 맞게 결합하여 정확도를 극대화합니다.
