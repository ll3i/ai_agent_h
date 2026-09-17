# run_full_analysis.py 상세 가이드

## 📋 개요

**역할**: Luxia Omni-Agent를 사용한 전체 데이터셋 자동 분석 실행 스크립트

**핵심 아이디어**: Example 이미지와 Test 이미지를 순차적으로 분석하여 표준 CSV와 상세 로그를 자동 생성

## 🏗️ 아키텍처

### 실행 흐름

```
┌─────────────────────────────────────────────────────┐
│        run_full_analysis.py 실행 흐름                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  START: python run_full_analysis.py                 │
│    ↓                                                 │
│  ┌──────────────────────────────────────────┐       │
│  │ 1. Example Dataset 분석                  │       │
│  │    Input: example_images.csv             │       │
│  │    Output: output_example.csv            │       │
│  │            output_example_detailed.csv   │       │
│  └──────────────┬───────────────────────────┘       │
│                 ↓                                    │
│  ┌──────────────────────────────────────────┐       │
│  │ 2. Test Dataset 분석                     │       │
│  │    Input: test.csv                       │       │
│  │    Output: output.csv (대회 제출용)       │       │
│  │            output_detailed.csv           │       │
│  └──────────────┬───────────────────────────┘       │
│                 ↓                                    │
│  ┌──────────────────────────────────────────┐       │
│  │ 3. 완료 메시지                           │       │
│  │    "🎉 All Analyses Finished!"          │       │
│  └──────────────────────────────────────────┘       │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## 📂 파일 구조

### 입력 파일

```
project_root/
├── example_images.csv          # 예제 이미지 목록
│   └── 형식: id, img_url
├── test.csv                    # 테스트 이미지 목록 (100개)
│   └── 형식: id, img_url
└── run_full_analysis.py        # 실행 스크립트
```

### 출력 파일

```
project_root/
├── output_example.csv          # 예제 결과 (id, label)
├── output_example_detailed.csv # 예제 상세 로그 (id, label, reason)
├── output.csv                  # 테스트 결과 (대회 제출용)
└── output_detailed.csv         # 테스트 상세 로그
```

---

## 🔧 핵심 함수 상세 설명

### run_dataset() - 데이터셋 분석 실행

```python
def run_dataset(input_csv, output_csv, dataset_name):
    """
    단일 데이터셋에 대한 전체 분석 실행

    Args:
        input_csv: 입력 CSV 파일 경로 (예: 'test.csv')
        output_csv: 출력 CSV 파일 경로 (예: 'output.csv')
        dataset_name: 데이터셋 이름 (로그용, 예: 'Test Dataset')

    Process:
        1. CSV 파일 존재 확인
        2. DataFrame 로드
        3. 각 이미지 순차 분석 (Omni-Agent)
        4. 결과 수집
        5. 표준 CSV 저장 (id, label)
        6. 상세 CSV 저장 (id, label, reason)

    Output Files:
        - output.csv: 대회 제출용 (id, label만)
        - output_detailed.csv: 디버깅용 (reason 포함)
    """
    print(f"\n🚀 Running Analysis on {dataset_name}...")
    print(f"📂 Input: {input_csv}")

    # 파일 존재 확인
    if not os.path.exists(input_csv):
        print(f"❌ File not found: {input_csv}")
        return

    # CSV 로드
    df = pd.read_csv(input_csv)
    results = []

    total = len(df)
    for idx, row in df.iterrows():
        image_id = row['id']
        image_path = row['img_url']

        print(f"[{idx+1}/{total}] Analyzing {image_id}...", end='\r')

        try:
            # Omni-Agent Call
            label, reason = classify_omni_final(image_path)
            results.append({
                'id': image_id,
                'label': label,
                'reason': reason  # Optional: Save reason if needed, but CSV usually just label
            })
            # Adjust CSV columns as per competition requirement (id, label)

        except Exception as e:
            logger.error(f"Error on {image_id}: {e}")
            results.append({'id': image_id, 'label': 0, 'reason': f"Error: {e}"})

    print(f"\n✅ Completed {dataset_name}")

    # Save standard output (id, label)
    out_df = pd.DataFrame(results)[['id', 'label']]
    out_df.to_csv(output_csv, index=False)
    print(f"📄 Saved to: {output_csv}")

    # Save detailed output (with reason)
    detailed_csv = output_csv.replace('.csv', '_detailed.csv')
    pd.DataFrame(results).to_csv(detailed_csv, index=False)
    print(f"📄 Detailed log: {detailed_csv}")
```

---

### main() - 메인 실행 함수

```python
def main():
    """
    전체 분석 워크플로우 실행

    워크플로우:
    1. Example 이미지 분석 (검증용)
    2. Test 이미지 분석 (제출용)
    3. 완료 메시지 출력

    실행:
        python run_full_analysis.py
    """
    print("="*60)
    print("🔮 Luxia Omni-Agent: Full Analysis Start")
    print("="*60)

    # 1. Analyze Example Images
    run_dataset("example_images.csv", "output_example.csv", "Example Dataset")

    # 2. Analyze Test Images
    run_dataset("test.csv", "output.csv", "Test Dataset")

    print("\n🎉 All Analyses Finished!")
```

---

## 📊 실행 예제

### 예제 1: 기본 실행

```bash
cd "c:\Users\work4\OneDrive\바탕 화면\산업AI_Agnet_해커톤"
python run_full_analysis.py
```

**출력**:
```
============================================================
🔮 Luxia Omni-Agent: Full Analysis Start
============================================================

🚀 Running Analysis on Example Dataset...
📂 Input: example_images.csv
[1/10] Analyzing EXAMPLE_001...
[2/10] Analyzing EXAMPLE_002...
...
[10/10] Analyzing EXAMPLE_010...
✅ Completed Example Dataset
📄 Saved to: output_example.csv
📄 Detailed log: output_example_detailed.csv

🚀 Running Analysis on Test Dataset...
📂 Input: test.csv
[1/100] Analyzing TEST_000...
[2/100] Analyzing TEST_001...
...
[100/100] Analyzing TEST_099...
✅ Completed Test Dataset
📄 Saved to: output.csv
📄 Detailed log: output_detailed.csv

🎉 All Analyses Finished!
```

### 예제 2: 가상환경에서 실행

```bash
# Windows
.\.venv\Scripts\python.exe run_full_analysis.py

# Linux/Mac
.venv/bin/python run_full_analysis.py
```

### 예제 3: 로그 리디렉션

```bash
python run_full_analysis.py > analysis.log 2>&1
```

**analysis.log 내용**:
```
============================================================
🔮 Luxia Omni-Agent: Full Analysis Start
============================================================
...
[OMNI-AGENT] Starting analysis for: ./test/TEST_000.png
  [KNOWLEDGE] Found similar case: case_004 (Score: 0.35)
...
```

---

## 🎯 출력 파일 형식

### output.csv (대회 제출용)

```csv
id,label
TEST_000,0
TEST_001,1
TEST_002,0
TEST_003,0
TEST_004,0
TEST_005,0
TEST_006,1
...
TEST_099,1
```

**형식**:
- **컬럼**: `id`, `label`
- **label**: `0` (Normal) 또는 `1` (Abnormal)
- **인덱스**: 없음 (`index=False`)

### output_detailed.csv (상세 로그)

```csv
id,label,reason
TEST_000,0,No defects found, all leads connected properly
TEST_001,1,Lead connectivity fail detected (Similar to case_002: 두 개의 리드 간 솔더 브리지 형성...)
TEST_002,0,Component in normal position, no damage
...
```

**형식**:
- **컬럼**: `id`, `label`, `reason`
- **reason**: 판정 근거 + 유사 사례 컨텍스트
- **용도**: 디버깅, 오류 분석, 성능 개선

---

## 🔍 디버깅 및 로깅

### 로깅 설정

```python
from src.utils import setup_logging
from src.config import Config

setup_logging(Config.LOGS_DIR)
logger = logging.getLogger(__name__)
```

**로그 파일 위치**: `logs/agent_YYYYMMDD_HHMMSS.log`

### 로그 레벨

```python
# src/config.py
LOG_LEVEL = logging.INFO  # DEBUG, INFO, WARNING, ERROR
```

### 에러 처리

```python
try:
    label, reason = classify_omni_final(image_path)
    results.append({
        'id': image_id,
        'label': label,
        'reason': reason
    })
except Exception as e:
    logger.error(f"Error on {image_id}: {e}")
    results.append({
        'id': image_id,
        'label': 0,  # 기본값: Normal
        'reason': f"Error: {e}"
    })
```

**에러 발생 시**:
- 로그에 에러 기록
- 결과에 `label=0` (보수적 판정)
- reason에 에러 메시지 저장
- 분석 계속 진행 (중단 없음)

---

## ⚙️ 설정 및 커스터마이징

### 입력 파일 변경

```python
def main():
    # 다른 입력 파일 사용
    run_dataset("custom_images.csv", "output_custom.csv", "Custom Dataset")
```

### 출력 경로 변경

```python
def main():
    # 출력 디렉터리 지정
    os.makedirs("results", exist_ok=True)
    run_dataset("test.csv", "results/output.csv", "Test Dataset")
```

### 진행 표시 개선

```python
from tqdm import tqdm

def run_dataset(input_csv, output_csv, dataset_name):
    # ... (기존 코드)

    for idx, row in tqdm(df.iterrows(), total=len(df), desc=dataset_name):
        # ... (분석 코드)
```

**출력 예시**:
```
Test Dataset: 100%|██████████| 100/100 [05:30<00:00,  3.30s/it]
```

### 병렬 처리 (선택사항)

```python
from concurrent.futures import ThreadPoolExecutor

def run_dataset_parallel(input_csv, output_csv, dataset_name, max_workers=5):
    df = pd.read_csv(input_csv)

    def process_row(row):
        try:
            label, reason = classify_omni_final(row['img_url'])
            return {'id': row['id'], 'label': label, 'reason': reason}
        except Exception as e:
            return {'id': row['id'], 'label': 0, 'reason': f"Error: {e}"}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_row, [row for _, row in df.iterrows()]))

    # 저장 로직 동일
    # ...
```

---

## 📈 성능 최적화 팁

### 1. 프로그레스 바 추가

```bash
pip install tqdm
```

```python
from tqdm import tqdm

for idx, row in tqdm(df.iterrows(), total=len(df)):
    # ...
```

### 2. 메모리 최적화

```python
# 배치 처리 (메모리 절약)
def run_dataset_batched(input_csv, output_csv, dataset_name, batch_size=10):
    df = pd.read_csv(input_csv)
    total = len(df)

    for start_idx in range(0, total, batch_size):
        end_idx = min(start_idx + batch_size, total)
        batch = df.iloc[start_idx:end_idx]

        # 배치 처리
        batch_results = []
        for idx, row in batch.iterrows():
            # ... (분석)
            batch_results.append(result)

        # 배치 결과 저장 (append mode)
        mode = 'a' if start_idx > 0 else 'w'
        pd.DataFrame(batch_results).to_csv(
            output_csv,
            mode=mode,
            header=(start_idx == 0),
            index=False
        )
```

### 3. 캐싱 활용

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_classify(image_path: str):
    return classify_omni_final(image_path)
```

---

## 🚀 실행 방법

### 방법 1: 직접 실행

```bash
python run_full_analysis.py
```

### 방법 2: 모듈로 실행

```bash
python -m run_full_analysis
```

### 방법 3: 특정 데이터셋만 실행

```python
# run_single_dataset.py
from run_full_analysis import run_dataset

run_dataset("test.csv", "output.csv", "Test Dataset")
```

```bash
python run_single_dataset.py
```

---

## 📝 의존성

### 필수 패키지

```python
import os
import sys
import pandas as pd
from pathlib import Path
import logging
from dotenv import load_dotenv
```

**설치**:
```bash
pip install pandas python-dotenv
```

### 프로젝트 모듈

```python
from src.final_omni_agent import classify_omni_final
from src.utils import setup_logging
from src.config import Config
```

### 환경 설정

**.env 파일**:
```bash
SALTLUX_API_KEY=your_api_key_here
```

---

## 🎓 사용 시나리오

### 시나리오 1: 대회 제출 준비

```bash
# 1. Test 데이터셋 분석
python run_full_analysis.py

# 2. output.csv 확인
head output.csv

# 3. 대회 제출
# output.csv 업로드
```

### 시나리오 2: 성능 검증

```bash
# 1. Example 데이터셋 먼저 테스트
python -c "
from run_full_analysis import run_dataset
run_dataset('example_images.csv', 'output_example.csv', 'Example')
"

# 2. 결과 확인
cat output_example.csv

# 3. 정확도 만족하면 Test 실행
python run_full_analysis.py
```

### 시나리오 3: 에러 분석

```bash
# 1. 상세 로그와 함께 실행
python run_full_analysis.py > full_log.txt 2>&1

# 2. 에러 검색
grep "Error" full_log.txt

# 3. 상세 CSV에서 에러 확인
python -c "
import pandas as pd
df = pd.read_csv('output_detailed.csv')
errors = df[df['reason'].str.contains('Error', na=False)]
print(errors)
"
```

---

## 💡 모범 사례

### 1. 실행 전 체크리스트

```bash
# ✅ API 키 설정 확인
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('SALTLUX_API_KEY')[:20])"

# ✅ 입력 파일 존재 확인
ls example_images.csv test.csv

# ✅ 의존성 설치 확인
pip list | grep pandas
```

### 2. 실행 중 모니터링

```bash
# 별도 터미널에서 로그 모니터링
tail -f logs/agent_*.log

# 출력 파일 크기 확인
watch -n 5 wc -l output.csv
```

### 3. 실행 후 검증

```python
# 결과 검증 스크립트
import pandas as pd

df = pd.read_csv('output.csv')

# 개수 확인
assert len(df) == 100, f"Expected 100 rows, got {len(df)}"

# 라벨 범위 확인
assert df['label'].isin([0, 1]).all(), "Invalid labels found"

# ID 확인
assert df['id'].nunique() == 100, "Duplicate IDs found"

print("✅ Validation passed!")
```

---

## 📝 요약

**run_full_analysis.py**는:

1. **Example Dataset 분석**: 검증용 예제 이미지 처리
2. **Test Dataset 분석**: 대회 제출용 100개 이미지 처리
3. **자동 저장**: 표준 CSV + 상세 로그 생성
4. **에러 처리**: 견고한 예외 처리 및 로깅

을 수행하는 **Luxia Omni-Agent 전체 분석 실행 스크립트**입니다.

**핵심 강점**: 한 번의 명령으로 전체 데이터셋을 자동 분석하여 대회 제출용 결과를 생성합니다.
