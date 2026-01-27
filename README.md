# 제조공정 이미지 분류 AI Agent

한양대 × 현대엔지비 산업체 제조 환경 기반 AI Agent 해커톤

## 📋 프로젝트 개요

제조공정을 촬영한 이미지(100장)를 정상/비정상으로 분류하는 멀티모달 LLM 기반 AI Agent 시스템

### 주요 특징
- **멀티모달 처리**: 이미지 + 텍스트 기반 추론
- **Agent 기반**: Judge-Think-Act-Verify 반복 프로세스
- **자동화**: End-to-End 파이프라인 (수동 개입 없음)
- **신뢰성**: 신뢰도 점수 기반 검증

## 📁 프로젝트 구조

```
산업AI_Agnet_해커톤/
├── DEVELOPMENT_PLAN.md          # 상세 개발 계획서
├── README.md                     # 이 파일
├── QUICKSTART.md                 # 빠른 시작 가이드
├── requirements.txt              # Python 의존성
├── .env.example                  # 환경 설정 예시
├── .env                          # 환경 설정 (API 키 포함, 직접 생성)
│
├── run_agent.py                  # 메인 실행 스크립트
├── validate_system.py            # 시스템 검증 스크립트
├── baseline.py                   # Baseline 참고 코드
├── data.csv                      # 개발용 데이터 (이미지 URL 목록)
│
├── src/                          # 소스 코드
│   ├── __init__.py
│   ├── config.py                 # 설정 관리
│   ├── integrated_agent.py       # 통합 AI Agent (핵심 실행 파일)
│   ├── agent_core.py             # Agent 핵심 로직 (상태 관리)
│   ├── image_processor.py        # 이미지 전처리
│   ├── saltlux_client.py         # Saltlux API 클라이언트
│   ├── vision_analyzer.py        # 이미지 분석기
│   ├── reasoner.py               # 추론 엔진
│   ├── decision_maker.py         # 의사결정 모듈
│   ├── verifier.py               # 검증 모듈
│   └── utils.py                  # 유틸리티 함수
│
├── data/                         # 데이터 폴더
│   └── (이미지 파일 저장 시 사용)
│
├── notebooks/
│   └── ai_agent.ipynb            # 최종 Jupyter Notebook
│
├── outputs/
│   └── output.csv                # 최종 예측 결과 (id, label)
│
└── logs/                         # 실행 로그
    └── agent_*.log               # 상세 로그 파일
```

## 🚀 설치 및 실행

### 1. 환경 구성

```bash
# Python 3.8+ 확인
python --version

# 의존성 설치
pip install -r requirements.txt

# 환경 설정
cp .env.example .env
# .env 파일 편집하여 API 키 설정
```

### 2. API 키 설정

`.env` 파일을 편집하여 Saltlux API 키를 설정합니다:

```bash
# .env 파일 내용
SALTLUX_API_KEY=YOUR_ACTUAL_API_KEY_HERE
SALTLUX_API_BASE_URL=https://bridge.luxiacloud.com/llm/openai/chat/completions/gpt-4o-mini/create
```

### 3. 데이터 확인

```bash
# 개발용 데이터 CSV 파일 확인
# data.csv 파일에 이미지 URL 목록이 포함되어 있음
# 형식: id, img_url
```

### 4. 실행 방법

**방법 1: Python 스크립트 실행 (권장)**
```bash
python run_agent.py
```

**방법 2: 통합 Agent 직접 실행**
```bash
python -m src.integrated_agent
```

**방법 3: Jupyter Notebook**
```bash
jupyter notebook notebooks/ai_agent.ipynb
```

### 5. 결과 확인

```
outputs/output.csv 파일 생성
- 형식: id, label (0=Normal, 1=Abnormal)
- 인코딩: UTF-8

예시:
id,label
DEV_000,0
DEV_001,1
...
```

## 🤖 AI Agent 아키텍처

### Flow Chart

```
┌─────────────────────┐
│  이미지 입력 (100장) │
└──────────┬──────────┘
           ↓
┌─────────────────────────────────┐
│   1. 데이터 전처리              │
│   - 로드, 리사이징, 정규화      │
└──────────┬──────────────────────┘
           ↓
┌──────────────────────────────────────────┐
│   2. AI Agent 추론 반복 (Judge-Act)     │
│  ┌───────────────────────────────────┐  │
│  │ A. Vision Analysis                │  │
│  │    (Saltlux API → 이미지 분석)    │  │
│  └─────────────┬─────────────────────┘  │
│                ↓                         │
│  ┌───────────────────────────────────┐  │
│  │ B. Reasoning (Think)              │  │
│  │    (다단계 추론 로직)             │  │
│  └─────────────┬─────────────────────┘  │
│                ↓                         │
│  ┌───────────────────────────────────┐  │
│  │ C. Decision Making (Act)          │  │
│  │    (최종 판단: Normal/Abnormal)   │  │
│  └─────────────┬─────────────────────┘  │
│                ↓                         │
│  ┌───────────────────────────────────┐  │
│  │ D. Verification (Verify)          │  │
│  │    (신뢰도 검증)                  │  │
│  └─────────────┬─────────────────────┘  │
│                ↓                         │
│          [종료 조건?]                   │
│         /            \                   │
│      ✅ Yes         ❌ No                 │
│       /                \                 │
│      ↓                  ↓                │
│  [종료]          [재추론 (Step A로)]    │
└──────────────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│   3. 결과 생성                  │
│   - CSV 파일 (UTF-8)           │
└──────────┬──────────────────────┘
           ↓
┌─────────────────────┐
│  output.csv 생성    │
└─────────────────────┘
```

## 📊 평가 기준 (총 100점)

| 항목 | 배점 | 설명 |
|------|------|------|
| **리더보드 성능** | 30점 | F1-Score 기반 평가 |
| **문제 접근 & 설계 논리** | 25점 | Agent 기반 설계의 논리성 |
| **Agent Flow 완성도** | 35점 | Judge-Think-Act-Verify 구조 명확성 |
| **효율성 & 실용성** | 10점 | API 호출 효율, 재현 가능성 |

## 🔧 Saltlux API 사용

### API 설정

```python
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('SALTLUX_API_KEY')
BRIDGE_URL = "https://bridge.luxiacloud.com/llm/openai/chat/completions/gpt-4o-mini/create"
MODEL = "gpt-4o-mini-2024-07-18"
```

### 이미지 분석 (OpenAI ChatCompletions 형식)

```python
import requests

headers = {"apikey": API_KEY, "Content-Type": "application/json"}

payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "너는 제조공정 소자 검사 이미지 분석기다."},
        {"role": "user", "content": [
            {"type": "text", "text": "이미지를 분석해 결함 여부를 JSON으로 출력해."},
            {"type": "image_url", "image_url": {"url": img_url}},
        ]},
    ],
    "stream": False
}

response = requests.post(BRIDGE_URL, headers=headers, json=payload, timeout=90)
result = response.json()["choices"][0]["message"]["content"]
```

### 관찰 항목 (결함 체크리스트)

| 항목 | 설명 |
|------|------|
| package_damage | 크랙/파손/깨짐 등 패키지 손상 |
| lead_missing_or_broken | 리드 결손/단선 |
| lead_severe_bend_or_contact | 심한 휨 또는 리드끼리 접촉 |
| solder_bridge_or_blob | 솔더 브리지 또는 납땜 뭉침 |
| misalignment_severe | 소자 위치가 과도하게 틀어짐 |

## 📈 성능 지표

| 지표 | 목표 |
|------|------|
| **F1-Score** | > 0.85 |
| **Precision** | > 0.85 |
| **Recall** | > 0.85 |

## 📝 개발 일정

- **2026-01-27**: Phase 1-4 (환경 구성, API 연동, Agent 로직)
- **2026-01-28**: Phase 5-8 (통합, 최적화, Notebook, 발표자료)

## ⚠️ 주의사항

1. **Saltlux API만 사용**: 다른 LLM API 사용 금지
2. **외부 데이터 불가**: 제공된 데이터만 사용
3. **자동화 필수**: 수동 개입 없이 자동으로 처리
4. **제출 마감**: 2026-01-28 13:00 (UTC+9)

## 📄 제출 항목

- [ ] `ai_agent.ipynb`: Jupyter Notebook
- [ ] `presentation.pdf`: 발표자료 (< 20MB)
- [ ] `output.csv`: 최종 예측 결과

## 🔗 참고 링크

- [Saltlux LUXIA PLATFORM](https://www.saltlux.com/)
- [Dacon 해커톤](https://dacon.io/)
- [한양대 산업AI](https://www.hanyang.ac.kr/)

## 📧 문의

해커톤 운영진: [경쟁 사이트 문의]

---

**Last Updated**: 2026-01-27
**Project Status**: Phase 1-4 완료, Phase 5 진행 중
