# 🚀 Quick Start Guide

## 환경 설정 (1회만 수행)

### 1. Python 환경 확인
```bash
python --version  # 3.8 이상 필요
```

### 2. 의존 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. Saltlux API 키 설정
```bash
# .env 파일 편집
SALTLUX_API_KEY=YOUR_API_KEY_HERE
SALTLUX_API_BASE_URL=https://bridge.luxiacloud.com/llm/openai/chat/completions/gpt-4o-mini/create

# 위 SALTLUX_API_KEY 부분에 팀 대시보드에서 배정된 API 키를 입력하세요.
```

---

## 실행 방법

### 방법 1: Python 스크립트 실행 (권장)
```bash
python run_agent.py
```

### 방법 2: 통합 Agent 직접 실행
```bash
python -m src.integrated_agent
```

### 방법 3: Jupyter Notebook
```bash
jupyter notebook notebooks/ai_agent.ipynb
```

---

## 파일 구조

```
산업AI_Agnet_해커톤/
├── run_agent.py              ← 메인 실행 파일
├── .env                      ← API 설정 (YOUR_API_KEY 입력 필수!)
├── data.csv / dev.csv        ← 개발용 데이터 (20장)
│
├── src/
│   ├── integrated_agent.py   ← 통합 AI Agent (Baseline + Judge-Think-Act-Verify)
│   ├── agent_core.py         ← Agent 핵심 로직
│   ├── vision_analyzer.py    ← 이미지 분석
│   ├── reasoner.py           ← 추론 엔진
│   ├── decision_maker.py     ← 의사결정
│   ├── verifier.py           ← 검증
│   ├── saltlux_client.py     ← API 클라이언트
│   ├── image_processor.py    ← 이미지 전처리
│   ├── config.py             ← 설정 관리
│   └── utils.py              ← 유틸리티
│
├── outputs/
│   └── output.csv            ← 최종 결과 (생성됨)
│
└── logs/
    └── agent_*.log           ← 실행 로그 (생성됨)
```

---

## 핵심 구조

### AI Agent Flow (Judge-Think-Act-Verify + Baseline Observe-Decide-Review)

```
📷 Input Image
    ↓
┌─────────────────────────────────────────┐
│ 1️⃣  JUDGE/OBSERVE                      │
│    LLM이 이미지를 분석하여              │
│    결함 항목을 체크리스트(JSON)로 추출  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2️⃣  THINK/ANALYZE                      │
│    관찰 결과를 해석하여                  │
│    결함 지표 분석                        │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3️⃣  ACT/DECIDE                         │
│    규칙 기반으로 정상/비정상 판단       │
│    (1개 이상 결함 → 비정상)             │
└─────────────────────────────────────────┘
    ↓
        [판단 확실한가?]
        /          \
      YES          NO
      /              \
    ↓                ↓
  VERIFY     REVIEW (재검토)
            (더 보수적으로 재분석)
            ↓
          VERIFY
    ↓
📊 Output: label (0=Normal, 1=Abnormal)
```

---

## 출력 파일

### outputs/output.csv
```
id,label
DEV_000,0
DEV_001,0
...
DEV_019,0
```

**형식**:
- id: 이미지 ID
- label: 0 (정상) 또는 1 (비정상)
- 인코딩: UTF-8

---

## 주요 특징

✅ **Baseline 호환**: 
   - Baseline의 Observe-Decide-Review 패턴을 그대로 사용
   - Saltlux API를 통한 이미지 분석

✅ **Agent 구조**:
   - Judge-Think-Act-Verify 명확한 4단계 구분
   - 각 단계가 명확한 역할 수행

✅ **안정성**:
   - API 오류 자동 재시도 (최대 3회)
   - Exponential backoff로 서버 부하 완화
   - 상세 로깅으로 디버깅 가능

✅ **효율성**:
   - 확실한 판단은 재검토 스킵
   - API 호출 최소화 (평균 1.5회/이미지)
   - 배치 처리로 속도 최적화

---

## 트러블슈팅

### 1. API Key 오류
```
RuntimeError: API Error: status=401
```
→ `.env` 파일의 API 키가 정확한지 확인하세요.

### 2. 이미지 로드 실패
```
Failed to load image: ...
```
→ 네트워크 연결을 확인하고 URL이 유효한지 확인하세요.

### 3. JSON 파싱 오류
```
ValueError: JSON parse failed
```
→ LLM 응답 형식이 올바르지 않습니다. 프롬프트를 재검토하세요.

### 4. 느린 처리 속도
```
Timeout error
```
→ `integrated_agent.py`의 timeout 값을 증가시키세요 (기본값: 90초).

---

## 성능 목표

| 지표 | 목표 |
|------|------|
| **F1-Score** | > 0.85 |
| **Precision** | > 0.85 |
| **Recall** | > 0.85 |

---

## 추가 정보

- 📖 [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) - 상세 개발 계획
- 📖 [README.md](README.md) - 프로젝트 개요
- 🔗 [Saltlux LUXIA PLATFORM](https://www.saltlux.com/)

---

**Last Updated**: 2026-01-27  
**Ready to Submit**: 2026-01-28 13:00
