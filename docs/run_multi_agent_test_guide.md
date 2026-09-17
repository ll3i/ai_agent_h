# run_multi_agent_test.py 상세 가이드

## 📋 개요

**역할**: Multi-Agent 방식을 사용한 예제/테스트 이미지 분류 실행 스크립트

**핵심 아이디어**: Multi-Agent 로직만 따로 테스트하기 위한 독립 실행 스크립트로, Example(20개)와 Test(100개) 데이터셋을 선택적으로 분석

## 🏗️ 아키텍처

### 실행 모드

```
┌─────────────────────────────────────────────────────┐
│     run_multi_agent_test.py 실행 모드                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Mode 1: --mode example (기본값)                    │
│  ┌────────────────────────────────────────┐         │
│  │ Example Dataset 분석 (20 images)       │         │
│  │ Input: example_images.csv              │         │
│  │ Output: output_multi_example.csv       │         │
│  └────────────────────────────────────────┘         │
│                                                      │
│  Mode 2: --mode test                                │
│  ┌────────────────────────────────────────┐         │
│  │ Test Dataset 분석 (100 images)         │         │
│  │ Input: test.csv                        │         │
│  │ Output: output_multi_test.csv          │         │
│  └────────────────────────────────────────┘         │
│                                                      │
│  Mode 3: --mode both                                │
│  ┌────────────────────────────────────────┐         │
│  │ Example → Test 순차 실행               │         │
│  │ Output: 두 CSV 파일 모두 생성          │         │
│  └────────────────────────────────────────┘         │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Multi-Agent vs Omni-Agent

| 특징 | Multi-Agent | Omni-Agent |
|------|-------------|------------|
| **실행 스크립트** | run_multi_agent_test.py | run_full_analysis.py |
| **Agent 타입** | multi_agent.py | final_omni_agent.py |
| **핵심 로직** | Multi-Model 로직 테스트 | Vision+Knowledge+Report 통합 |
| **출력 파일** | output_multi_*.csv | output.csv |
| **용도** | Multi-Agent 검증 | 최종 제출용 |

---

## 📂 파일 구조

### 입력 파일

```
project_root/
├── example_images.csv    # 예제 이미지 20개
├── test.csv              # 테스트 이미지 100개
└── run_multi_agent_test.py
```

### 출력 파일

```
project_root/
├── output_multi_example.csv  # Example 결과 (id, label)
└── output_multi_test.csv     # Test 결과 (id, label)
```

---

## 🔧 핵심 함수 상세 설명

### run_multi_agent_test() - Multi-Agent 실행

```python
def run_multi_agent_test(input_csv: str, output_csv: str):
    """
    Multi-Agent 방식으로 이미지 분류 수행

    Args:
        input_csv: 입력 CSV 파일 경로
        output_csv: 출력 CSV 파일 경로

    Process:
        1. CSV 로드
        2. 각 이미지 Multi-Agent 분류 (classify_multi_agent)
        3. 결과 수집 (id, label)
        4. CSV 저장

    Returns:
        DataFrame: 결과 데이터프레임

    Note:
        - reason은 로그에만 출력, CSV에는 저장 안함
        - 에러 발생 시 label=0 (Normal) 기본값
    """
    df = pd.read_csv(input_csv)
    results = []

    for idx, row in df.iterrows():
        image_id = row['id']
        image_path = row['img_url']

        logger.info(f"[{idx+1}/{len(df)}] Processing: {image_id}")

        try:
            label, reason = classify_multi_agent(image_path)
            results.append({'id': image_id, 'label': label})
            logger.info(f"  Result: {'ABNORMAL' if label == 1 else 'NORMAL'}")
        except Exception as e:
            logger.error(f"  Error: {e}")
            results.append({'id': image_id, 'label': 0})

    # 결과 저장
    result_df = pd.DataFrame(results)
    result_df.to_csv(output_csv, index=False)
    logger.info(f"📄 Results saved to: {output_csv}")

    return result_df
```

**특징**:
- **간단한 로깅**: 진행 상황 + 결과만 표시
- **에러 복구**: 예외 발생 시 기본값(0) 사용하여 계속 진행
- **CSV만 저장**: reason은 로그에만, CSV에는 id와 label만
- **반환값**: DataFrame 반환 (추가 분석 가능)

---

### main() - 메인 실행 로직

```python
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["example", "test", "both"], default="example")
    args = parser.parse_args()

    base_dir = Path(__file__).parent

    if args.mode in ["example", "both"]:
        logger.info("=== Running Multi-Agent on EXAMPLE images (20) ===")
        run_multi_agent_test(
            str(base_dir / "example_images.csv"),
            str(base_dir / "output_multi_example.csv")
        )

    if args.mode in ["test", "both"]:
        logger.info("=== Running Multi-Agent on TEST images (100) ===")
        run_multi_agent_test(
            str(base_dir / "test.csv"),
            str(base_dir / "output_multi_test.csv")
        )
```

**CLI 인터페이스**:
- `--mode example`: Example 데이터셋만 (기본값)
- `--mode test`: Test 데이터셋만
- `--mode both`: 두 데이터셋 모두

---

## 📊 실행 예제

### 예제 1: Example 데이터셋 테스트 (기본)

```bash
python run_multi_agent_test.py
```

**출력**:
```
2026-01-27 14:30:00 - === Running Multi-Agent on EXAMPLE images (20) ===
2026-01-27 14:30:01 - [1/20] Processing: EXAMPLE_001
2026-01-27 14:30:05 -   Result: NORMAL
2026-01-27 14:30:06 - [2/20] Processing: EXAMPLE_002
2026-01-27 14:30:10 -   Result: ABNORMAL
...
2026-01-27 14:32:00 - [20/20] Processing: EXAMPLE_020
2026-01-27 14:32:04 -   Result: NORMAL
2026-01-27 14:32:04 - 📄 Results saved to: output_multi_example.csv
```

### 예제 2: Test 데이터셋만 실행

```bash
python run_multi_agent_test.py --mode test
```

**출력**:
```
2026-01-27 14:35:00 - === Running Multi-Agent on TEST images (100) ===
2026-01-27 14:35:01 - [1/100] Processing: TEST_000
2026-01-27 14:35:05 -   Result: NORMAL
2026-01-27 14:35:06 - [2/100] Processing: TEST_001
2026-01-27 14:35:10 -   Result: ABNORMAL
...
2026-01-27 14:45:00 - [100/100] Processing: TEST_099
2026-01-27 14:45:04 -   Result: ABNORMAL
2026-01-27 14:45:04 - 📄 Results saved to: output_multi_test.csv
```

### 예제 3: 두 데이터셋 모두 실행

```bash
python run_multi_agent_test.py --mode both
```

**출력**:
```
2026-01-27 14:50:00 - === Running Multi-Agent on EXAMPLE images (20) ===
...
2026-01-27 14:52:00 - 📄 Results saved to: output_multi_example.csv
2026-01-27 14:52:01 - === Running Multi-Agent on TEST images (100) ===
...
2026-01-27 15:02:00 - 📄 Results saved to: output_multi_test.csv
```

### 예제 4: 로그 파일 저장

```bash
python run_multi_agent_test.py --mode both > multi_agent_log.txt 2>&1
```

**multi_agent_log.txt 내용**:
```
2026-01-27 14:50:00 - === Running Multi-Agent on EXAMPLE images (20) ===
2026-01-27 14:50:01 - [1/20] Processing: EXAMPLE_001
2026-01-27 14:50:05 -   Result: NORMAL
...
```

---

## 🎯 출력 파일 형식

### output_multi_example.csv

```csv
id,label
EXAMPLE_001,0
EXAMPLE_002,1
EXAMPLE_003,0
...
EXAMPLE_020,1
```

### output_multi_test.csv

```csv
id,label
TEST_000,0
TEST_001,1
TEST_002,0
...
TEST_099,1
```

**형식**:
- **컬럼**: `id`, `label`
- **label**: `0` (Normal) 또는 `1` (Abnormal)
- **인덱스**: 없음 (`index=False`)

---

## 🔍 디버깅 및 로깅

### 로깅 설정

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

**로그 포맷**:
```
YYYY-MM-DD HH:MM:SS - 메시지
```

### 로그 레벨 변경

```python
# 더 상세한 로그
logging.basicConfig(level=logging.DEBUG)

# 에러만 표시
logging.basicConfig(level=logging.ERROR)
```

### 에러 처리

```python
try:
    label, reason = classify_multi_agent(image_path)
    results.append({'id': image_id, 'label': label})
    logger.info(f"  Result: {'ABNORMAL' if label == 1 else 'NORMAL'}")
except Exception as e:
    logger.error(f"  Error: {e}")
    results.append({'id': image_id, 'label': 0})  # 기본값: Normal
```

**에러 발생 시**:
- 로그에 에러 메시지 기록
- `label=0` (보수적 판정)
- 다음 이미지 계속 처리

---

## ⚙️ 설정 및 커스터마이징

### 1. 출력 파일명 변경

```python
if args.mode in ["example", "both"]:
    run_multi_agent_test(
        str(base_dir / "example_images.csv"),
        str(base_dir / "results/example_output.csv")  # 커스텀 경로
    )
```

### 2. reason 포함하여 저장

```python
def run_multi_agent_test(input_csv: str, output_csv: str):
    # ... (기존 코드)

    try:
        label, reason = classify_multi_agent(image_path)
        results.append({
            'id': image_id,
            'label': label,
            'reason': reason  # reason 추가
        })
    except Exception as e:
        results.append({
            'id': image_id,
            'label': 0,
            'reason': f"Error: {e}"
        })

    # 저장 (reason 포함)
    result_df = pd.DataFrame(results)
    result_df.to_csv(output_csv, index=False)
```

### 3. 진행 표시 개선 (tqdm)

```bash
pip install tqdm
```

```python
from tqdm import tqdm

def run_multi_agent_test(input_csv: str, output_csv: str):
    df = pd.read_csv(input_csv)
    results = []

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing"):
        # ... (분석 코드)
```

**출력**:
```
Processing: 100%|██████████| 100/100 [10:00<00:00,  6.00s/it]
```

---

## 📈 성능 최적화 팁

### 1. 병렬 처리

```python
from concurrent.futures import ThreadPoolExecutor

def run_multi_agent_test_parallel(input_csv: str, output_csv: str, max_workers=5):
    df = pd.read_csv(input_csv)

    def process_row(row):
        try:
            label, reason = classify_multi_agent(row['img_url'])
            return {'id': row['id'], 'label': label}
        except Exception as e:
            logger.error(f"Error on {row['id']}: {e}")
            return {'id': row['id'], 'label': 0}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(
            process_row,
            [row for _, row in df.iterrows()]
        ))

    result_df = pd.DataFrame(results)
    result_df.to_csv(output_csv, index=False)
    return result_df
```

### 2. 캐싱

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_classify_multi_agent(image_path: str):
    return classify_multi_agent(image_path)
```

### 3. 배치 처리

```python
def run_multi_agent_test_batched(input_csv: str, output_csv: str, batch_size=10):
    df = pd.read_csv(input_csv)

    for start_idx in range(0, len(df), batch_size):
        end_idx = min(start_idx + batch_size, len(df))
        batch = df.iloc[start_idx:end_idx]

        # 배치 처리
        for idx, row in batch.iterrows():
            # ... (분석)

        # 중간 저장 (checkpointing)
        if (end_idx % 50) == 0:
            logger.info(f"Checkpoint: {end_idx}/{len(df)} completed")
```

---

## 🚀 실행 방법

### 방법 1: 기본 실행 (Example)

```bash
python run_multi_agent_test.py
```

### 방법 2: Test 데이터셋

```bash
python run_multi_agent_test.py --mode test
```

### 방법 3: 전체 실행

```bash
python run_multi_agent_test.py --mode both
```

### 방법 4: 가상환경에서 실행

```bash
# Windows
.\.venv\Scripts\python.exe run_multi_agent_test.py --mode both

# Linux/Mac
.venv/bin/python run_multi_agent_test.py --mode both
```

---

## 🎓 사용 시나리오

### 시나리오 1: Multi-Agent 로직 검증

```bash
# 1. Example 데이터셋으로 먼저 테스트 (빠름)
python run_multi_agent_test.py --mode example

# 2. 결과 확인
cat output_multi_example.csv

# 3. 정확도 만족하면 Test 실행
python run_multi_agent_test.py --mode test
```

### 시나리오 2: Omni-Agent vs Multi-Agent 비교

```bash
# 1. Multi-Agent 실행
python run_multi_agent_test.py --mode test

# 2. Omni-Agent 실행
python run_full_analysis.py

# 3. 결과 비교
python -c "
import pandas as pd
multi = pd.read_csv('output_multi_test.csv')
omni = pd.read_csv('output.csv')
diff = (multi['label'] != omni['label']).sum()
print(f'차이 개수: {diff}/100')
"
```

### 시나리오 3: 에러 분석

```bash
# 1. 로그와 함께 실행
python run_multi_agent_test.py --mode both > multi_log.txt 2>&1

# 2. 에러 검색
grep "Error" multi_log.txt

# 3. 에러 발생 이미지 확인
grep -B 1 "Error" multi_log.txt | grep "Processing"
```

---

## 💡 모범 사례

### 1. 실행 전 체크리스트

```bash
# ✅ Multi-Agent 모듈 확인
python -c "from src.multi_agent import classify_multi_agent; print('OK')"

# ✅ API 키 확인
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('SALTLUX_API_KEY')[:20])"

# ✅ 입력 파일 확인
ls example_images.csv test.csv
```

### 2. 결과 검증

```python
# validate_results.py
import pandas as pd

df = pd.read_csv('output_multi_test.csv')

# 개수 확인
assert len(df) == 100, f"Expected 100, got {len(df)}"

# 라벨 유효성 확인
assert df['label'].isin([0, 1]).all(), "Invalid labels"

# ID 중복 확인
assert df['id'].nunique() == 100, "Duplicate IDs"

print("✅ Validation passed!")
```

```bash
python validate_results.py
```

### 3. 성능 비교

```python
# compare_agents.py
import pandas as pd

multi = pd.read_csv('output_multi_test.csv')
omni = pd.read_csv('output.csv')

# 통계 비교
print("Multi-Agent:")
print(f"  Normal: {(multi['label']==0).sum()}")
print(f"  Abnormal: {(multi['label']==1).sum()}")

print("\nOmni-Agent:")
print(f"  Normal: {(omni['label']==0).sum()}")
print(f"  Abnormal: {(omni['label']==1).sum()}")

# 차이 분석
diff_ids = multi[multi['label'] != omni['label']]['id'].tolist()
print(f"\n차이 발생 이미지: {len(diff_ids)}개")
print(diff_ids[:10])  # 처음 10개만 출력
```

---

## 📝 의존성

### 필수 패키지

```python
import os
import sys
import pandas as pd
import logging
from pathlib import Path
from dotenv import load_dotenv
```

**설치**:
```bash
pip install pandas python-dotenv
```

### 프로젝트 모듈

```python
from src.multi_agent import classify_multi_agent
```

**확인**:
```bash
python -c "from src.multi_agent import classify_multi_agent"
```

### 환경 설정

**.env 파일**:
```bash
SALTLUX_API_KEY=your_api_key_here
```

---

## 🆚 Omni-Agent와의 차이점

| 항목 | run_multi_agent_test.py | run_full_analysis.py |
|------|------------------------|---------------------|
| **Agent 타입** | Multi-Agent | Omni-Agent |
| **핵심 모듈** | src/multi_agent.py | src/final_omni_agent.py |
| **출력 파일** | output_multi_*.csv | output.csv |
| **CLI 옵션** | --mode (example/test/both) | 없음 (고정) |
| **로깅 스타일** | 간단 (진행+결과) | 상세 (Agent별) |
| **상세 로그** | 미제공 | *_detailed.csv |
| **용도** | Multi-Agent 검증 | 최종 제출용 |

---

## 📝 요약

**run_multi_agent_test.py**는:

1. **Multi-Agent 테스트**: Multi-Agent 로직 단독 검증
2. **유연한 실행 모드**: Example/Test/Both 선택 가능
3. **간단한 출력**: id, label만 CSV 저장
4. **CLI 인터페이스**: argparse 기반 명령줄 옵션

을 제공하는 **Multi-Agent 전용 테스트 스크립트**입니다.

**핵심 강점**: Multi-Agent 로직을 독립적으로 검증하고, Example 데이터셋으로 빠른 테스트가 가능합니다.

---

## 🔗 관련 파일

- **src/multi_agent.py**: Multi-Agent 구현 모듈
- **run_full_analysis.py**: Omni-Agent 실행 스크립트 (비교용)
- **example_images.csv**: Example 데이터셋 (20개)
- **test.csv**: Test 데이터셋 (100개)
