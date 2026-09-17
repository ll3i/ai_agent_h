# config.py 상세 가이드

## 📋 개요

**파일 위치**: `src/config.py`

**역할**: 프로젝트 전체 설정 및 환경 변수 관리를 담당하는 중앙 설정 파일

**핵심 아이디어**: 모든 설정을 한 곳에서 관리하여 유지보수성과 일관성을 보장

## 🏗️ 구조

### Config 클래스

```python
class Config:
    """프로젝트 설정 클래스 - 모든 설정을 클래스 변수로 관리"""

    # 1. 경로 설정
    # 2. API 설정
    # 3. 다중 모델 설정
    # 4. 모델 프로필
    # 5. 프로젝트 설정
    # 6. Agent 설정
    # 7. 이미지 처리 설정
    # 8. 출력 설정
    # 9. 분류 레이블
```

---

## 📂 주요 구성 요소

### 1. 경로 설정

```python
PROJECT_ROOT = Path(__file__).parent.parent  # 프로젝트 루트
DATA_DIR = PROJECT_ROOT / "data"             # 데이터 디렉터리
DEV_DATA_DIR = DATA_DIR / "dev"              # 개발 데이터
TEST_DATA_DIR = DATA_DIR / "test"            # 테스트 데이터
OUTPUT_DIR = PROJECT_ROOT / "outputs"        # 출력 디렉터리
LOGS_DIR = PROJECT_ROOT / "logs"             # 로그 디렉터리
```

**특징**:
- `Path` 객체 사용으로 OS 독립적
- 상대 경로 기반으로 이식성 보장
- 모든 파일 접근은 이 경로 기준

**디렉터리 구조**:
```
project_root/
├── data/
│   ├── dev/     # 개발용 이미지
│   └── test/    # 테스트 이미지
├── outputs/     # 결과 CSV 파일
├── logs/        # 로그 파일
└── src/
    └── config.py
```

---

### 2. API 설정

```python
SALTLUX_API_KEY = os.getenv('SALTLUX_API_KEY', 'your_api_key_here')
SALTLUX_API_BASE_URL = os.getenv('SALTLUX_API_BASE_URL',
    'https://api.luxiaplatform.com/v1')
SALTLUX_API_TIMEOUT = 30  # seconds
SALTLUX_MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
```

**환경 변수 우선순위**:
1. `.env` 파일에서 로드
2. 시스템 환경 변수
3. 기본값 (fallback)

**.env 파일 예시**:
```bash
SALTLUX_API_KEY=your_actual_api_key_here
SALTLUX_API_BASE_URL=https://bridge.luxiacloud.com/llm/openai/chat/completions/{model}/create
MAX_RETRIES=5
```

---

### 3. 다중 모델 설정 (LUXIA_MODELS)

```python
LUXIA_MODELS = {
    'judge': 'luxia3-llm-32b-0731',   # 관찰 - 상세 이미지 분석
    'think': 'luxia3-llm-32b-0731',   # 추론 - 깊이 있는 분석
    'act': 'luxia3-llm-13b-0731',     # 의사결정 - 빠른 판단
    'verify': 'luxia3-llm-32b-0731',  # 검증 - 최종 확인
}
```

**모델 선택 전략**:

| 단계 | 모델 | 크기 | 용도 | 이유 |
|------|------|------|------|------|
| **JUDGE** | luxia3-llm-32b-0731 | 32B | 상세 비전 분석 | 높은 정확도 필요 |
| **THINK** | luxia3-llm-32b-0731 | 32B | 깊은 추론 | 복잡한 분석 |
| **ACT** | luxia3-llm-13b-0731 | 13B | 빠른 판단 | 속도 + 정확도 균형 |
| **VERIFY** | luxia3-llm-32b-0731 | 32B | 최종 검증 | 신뢰도 최우선 |

**모델 변경 예시**:
```python
# OpenAI 모델로 변경
LUXIA_MODELS = {
    'judge': 'gpt-4o-mini-2024-07-18',
    'think': 'claude-3.5-sonnet',
    'act': 'gpt-3.5-turbo',
    'verify': 'gpt-4o-2024-11-20',
}
```

---

### 4. 모델 프로필 (MODEL_PROFILES)

```python
MODEL_PROFILES = {
    'judge': {
        'purpose': 'Detailed Vision Analysis (상세 이미지 분석)',
        'capabilities': ['detailed_analysis', 'korean_optimized', 'technical_description'],
        'cost_level': 'medium',
        'response_time': 'fast',
        'reasoning_depth': 'detailed'
    },
    # ... 다른 모델들
}
```

**프로필 항목 설명**:
- `purpose`: 모델의 주 용도
- `capabilities`: 모델이 가진 능력 목록
- `cost_level`: 비용 수준 (low/medium/high)
- `response_time`: 응답 속도 (very_fast/fast/medium/slow)
- `reasoning_depth`: 추론 깊이 (minimal/moderate/detailed/very_deep)

**사용 예시**:
```python
# Judge 모델 프로필 조회
profile = Config.MODEL_PROFILES['judge']
print(f"Purpose: {profile['purpose']}")
print(f"Cost: {profile['cost_level']}")
```

---

### 5. 사용 가능한 모델 목록 (AVAILABLE_MODELS)

```python
AVAILABLE_MODELS = [
    # Luxia 최신 모델 (한국어 최적화)
    'luxia3-llm-32b-0731',   # 32B, 최고 성능
    'luxia3-llm-13b-0731',   # 13B, 고성능
    'luxia3-llm-8b-0731',    # 8B, 기본

    # OpenAI Models
    'gpt-4o-2024-11-20',
    'gpt-4o-mini-2024-07-18',
    'gpt-3.5-turbo',

    # Claude Models
    'claude-3.5-sonnet',
    'claude-3-opus',
    'claude-3-haiku',
]
```

**모델 선택 가이드**:

**한국어 최적화 필요 시**:
- `luxia3-llm-32b-0731` (최고 성능)
- `luxia3-llm-13b-0731` (균형)

**비용 최적화 필요 시**:
- `gpt-4o-mini-2024-07-18` (저비용)
- `luxia3-llm-8b-0731` (저비용)

**최고 성능 필요 시**:
- `gpt-4o-2024-11-20` (OpenAI 최신)
- `claude-3.5-sonnet` (Claude 최신)

---

### 6. 프로젝트 설정

```python
PROJECT_NAME = os.getenv('PROJECT_NAME', 'Manufacturing_AI_Agent')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  # DEBUG, INFO, WARNING, ERROR
```

**로그 레벨**:
- `DEBUG`: 모든 상세 정보
- `INFO`: 일반 정보 (기본값)
- `WARNING`: 경고만
- `ERROR`: 에러만

---

### 7. Agent 설정

```python
CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.85'))
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '5'))
MAX_AGENT_ITERATIONS = 3  # Agent 최대 반복 횟수
```

**설정 의미**:
- `CONFIDENCE_THRESHOLD`: 신뢰도 임계값 (0.85 = 85%)
- `BATCH_SIZE`: 배치 처리 크기
- `MAX_AGENT_ITERATIONS`: 재검토 최대 횟수

**조정 예시**:
```bash
# .env 파일
CONFIDENCE_THRESHOLD=0.90  # 더 엄격한 기준
BATCH_SIZE=10              # 더 큰 배치
```

---

### 8. 이미지 처리 설정

```python
IMAGE_SIZE = int(os.getenv('IMAGE_SIZE', '224'))
IMAGE_QUALITY = int(os.getenv('IMAGE_QUALITY', '95'))
IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
```

**설정 가이드**:
- `IMAGE_SIZE`: 이미지 리사이즈 크기 (픽셀)
- `IMAGE_QUALITY`: JPEG 품질 (0-100)
- `IMAGE_EXTENSIONS`: 지원하는 이미지 확장자

---

### 9. 분류 레이블

```python
CLASS_LABELS = {
    0: 'Normal',
    1: 'Abnormal'
}

REVERSE_LABELS = {
    'Normal': 0,
    'Abnormal': 1,
    'normal': 0,
    'abnormal': 1
}
```

**사용 예시**:
```python
# 숫자 → 문자열
label = 1
label_str = Config.CLASS_LABELS[label]  # 'Abnormal'

# 문자열 → 숫자
label_str = 'Normal'
label_num = Config.REVERSE_LABELS[label_str]  # 0
```

---

## 🔧 주요 메서드

### get() - 설정값 조회

```python
@classmethod
def get(cls, key: str, default: Any = None) -> Any:
    """설정값 조회 (없으면 default 반환)"""
    return getattr(cls, key, default)
```

**사용 예시**:
```python
# API 키 조회
api_key = Config.get('SALTLUX_API_KEY')

# 존재하지 않는 키 (기본값 반환)
custom_val = Config.get('CUSTOM_KEY', 'default_value')
```

---

### to_dict() - 딕셔너리 변환

```python
@classmethod
def to_dict(cls) -> Dict[str, Any]:
    """설정을 딕셔너리로 변환 (대문자 변수만)"""
    config_dict = {}
    for attr in dir(cls):
        if not attr.startswith('_') and attr.isupper():
            config_dict[attr] = getattr(cls, attr)
    return config_dict
```

**사용 예시**:
```python
# 모든 설정 조회
all_config = Config.to_dict()
print(json.dumps(all_config, indent=2, default=str))
```

---

### validate() - 설정 유효성 검증

```python
@classmethod
def validate(cls) -> bool:
    """
    설정 유효성 검증

    검증 항목:
    1. API 키 설정 확인
    2. 필수 디렉터리 생성
    3. 데이터 디렉터리 존재 확인

    Returns:
        bool: 검증 성공 여부
    """
```

**사용 예시**:
```python
if Config.validate():
    print("✅ Configuration is valid!")
else:
    print("❌ Configuration has errors!")
```

**출력 예시**:
```
⚠️  SALTLUX_API_KEY is not set. Please configure .env file.
⚠️  Development data directory not found: /path/to/data/dev
```

---

## 📊 실행 예제

### 예제 1: 설정 로드 및 검증

```python
from src.config import Config

# 설정 검증
if not Config.validate():
    print("설정을 확인하세요!")
    exit(1)

# 주요 설정 출력
print(f"프로젝트: {Config.PROJECT_NAME}")
print(f"API 키: {Config.SALTLUX_API_KEY[:20]}...")
print(f"신뢰도 임계값: {Config.CONFIDENCE_THRESHOLD}")
```

### 예제 2: 모델 설정 조회

```python
# Judge 모델 확인
judge_model = Config.LUXIA_MODELS['judge']
judge_profile = Config.MODEL_PROFILES['judge']

print(f"Judge Model: {judge_model}")
print(f"Purpose: {judge_profile['purpose']}")
print(f"Capabilities: {', '.join(judge_profile['capabilities'])}")
```

### 예제 3: 경로 설정 사용

```python
import pandas as pd

# 출력 파일 경로
output_path = Config.OUTPUT_DIR / Config.OUTPUT_CSV_FILENAME
print(f"결과 저장 위치: {output_path}")

# CSV 저장
df = pd.DataFrame({'id': ['TEST_001'], 'label': [0]})
df.to_csv(output_path, index=False)
```

---

## ⚙️ 설정 커스터마이징

### 1. .env 파일로 설정 변경

```bash
# .env 파일 생성
cat > .env << EOF
SALTLUX_API_KEY=sk-xxxxxxxxxxxxx
CONFIDENCE_THRESHOLD=0.90
BATCH_SIZE=10
LOG_LEVEL=DEBUG
MAX_RETRIES=5
EOF
```

### 2. 코드에서 직접 변경

```python
# config.py 수정
class Config:
    # ... 기존 설정

    # 커스텀 설정 추가
    CUSTOM_TIMEOUT = 60
    USE_CACHING = True
    CACHE_SIZE = 100
```

### 3. 런타임 동적 변경

```python
# 실행 중 설정 변경 (권장하지 않음)
Config.CONFIDENCE_THRESHOLD = 0.95
Config.BATCH_SIZE = 20
```

---

## 🔍 디버깅 및 테스트

### 설정 검증 테스트

```bash
# config.py 직접 실행
python src/config.py
```

**출력**:
```
🔧 Configuration:
  Project Root: C:\Users\work4\OneDrive\바탕 화면\산업AI_Agnet_해커톤
  Data Dir: C:\Users\work4\OneDrive\바탕 화면\산업AI_Agnet_해커톤\data
  Output Dir: C:\Users\work4\OneDrive\바탕 화면\산업AI_Agnet_해커톤\outputs
  Confidence Threshold: 0.85
  Batch Size: 5

✅ Configuration loaded successfully!
```

### API 키 확인

```python
from src.config import Config
import os

print(f"API Key from Config: {Config.SALTLUX_API_KEY[:20]}...")
print(f"API Key from env: {os.getenv('SALTLUX_API_KEY', 'Not set')[:20]}...")
```

---

## 📝 모범 사례

### 1. 환경별 설정 분리

```bash
# .env.development
SALTLUX_API_KEY=dev_key
LOG_LEVEL=DEBUG
BATCH_SIZE=1

# .env.production
SALTLUX_API_KEY=prod_key
LOG_LEVEL=INFO
BATCH_SIZE=10
```

```python
# 환경별 로드
import os
env = os.getenv('ENVIRONMENT', 'development')
load_dotenv(f'.env.{env}')
```

### 2. 설정 유효성 검증

```python
# 프로그램 시작 시 필수 검증
if __name__ == '__main__':
    if not Config.validate():
        print("❌ Configuration error!")
        exit(1)

    # 메인 로직 실행
    main()
```

### 3. 타입 힌트 사용

```python
from typing import Optional

class Config:
    SALTLUX_API_KEY: str
    CONFIDENCE_THRESHOLD: float
    BATCH_SIZE: int
    LUXIA_MODELS: Dict[str, str]
```

---

## 🆘 문제 해결

### Q: API 키가 인식되지 않아요
```bash
# .env 파일 위치 확인
ls -la .env

# .env 파일 내용 확인
cat .env | grep SALTLUX_API_KEY

# Python에서 확인
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('SALTLUX_API_KEY'))"
```

### Q: 디렉터리가 없다고 나와요
```python
# 디렉터리 자동 생성
Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
```

### Q: 설정 변경이 반영 안돼요
```python
# Python 재시작 필요 (import 캐시 때문)
# 또는 importlib 사용
import importlib
import src.config
importlib.reload(src.config)
```

---

## 📝 요약

**config.py**는:

1. **중앙 설정 관리**: 모든 설정을 한 곳에서 관리
2. **환경 변수 지원**: .env 파일 및 시스템 환경 변수 통합
3. **다중 모델 설정**: Luxia/OpenAI/Claude 모델 유연하게 관리
4. **유효성 검증**: validate() 메서드로 설정 자동 검증
5. **확장성**: 새로운 설정 쉽게 추가 가능

을 제공하는 **프로젝트 설정 관리 핵심 파일**입니다.

**핵심 강점**: 설정을 코드와 분리하여 유지보수성과 보안성을 향상시킵니다.
