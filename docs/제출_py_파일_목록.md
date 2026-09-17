# 제출해야 하는 Python(.py) 파일 목록

## 📌 공식 제출 항목 (README / DEVELOPMENT_PLAN 기준)

대회 요청 **제출 물품**에는 다음만 필수로 적혀 있습니다.

- `ai_agent.ipynb` (Jupyter Notebook)
- `presentation.pdf` (발표자료, < 20MB)
- `output.csv` (최종 예측 결과)

**코드 제출** 시 채점/재현을 위해 보통 포함하는 **.py 파일**은 아래를 기준으로 하면 됩니다.

---

## 1. 실행 진입점 (메인 실행 스크립트)

제출하는 **output.csv**를 만드는 실행 파일입니다.  
**그 파일 1개만** 넣어도 되고, 사용한 스크립트를 그대로 넣으면 됩니다.

| 용도 | 파일명 | 비고 |
|------|--------|------|
| README 권장 실행 | `run_agent.py` | `src.integrated_agent` 호출, outputs/output.csv 생성 |
| 대회 문서 예시 | `run_full_analysis.py` | Omni-Agent 기준, output.csv 생성 |
| **리더보드 제출용 (예: V8 0.76)** | `run_v8.py` | `outpu1t_v8.csv` 생성 → 이걸 제출용 output.csv로 복사해도 됨 |

→ **실제로 리더보드에 넣은 결과**를 만든 스크립트를 반드시 포함하는 것이 좋습니다.

---

## 2. src/ 폴더 안에 넣어야 할 .py (실행에 필요)

**DEVELOPMENT_PLAN** 제출 폴더 구조 기준:

- `src/__init__.py`
- `src/config.py`
- `src/image_processor.py` (또는 실제 사용하는 이미지 처리 모듈)
- `src/saltlux_client.py` (또는 Saltlux API 호출 모듈)
- `src/agent_core.py` (또는 Agent 핵심 로직)
- `src/utils.py`

**run_agent.py 경로**를 쓰는 경우, `integrated_agent`가 불러오는 모든 모듈이 필요하므로 예시는 다음과 같습니다.

- `src/__init__.py`
- `src/config.py`
- `src/integrated_agent.py`
- `src/utils.py`
- (그리고 integrated_agent가 import하는 나머지 .py 전부)

**run_v8.py 경로**를 쓰는 경우, 예시는 다음과 같습니다.

- `src/__init__.py`
- `src/targeted_fn_v8.py`
- (`targeted_fn_v8.py`가 내부에서 사용하는 다른 .py가 있으면 같이 포함)

---

## 3. 제출 루트에 두면 좋은 .py (선택)

- `run_agent.py` — README에서 “메인 실행”으로 소개한 스크립트
- `run_full_analysis.py` — 문서에서 “대회 제출용” 예시로 쓰인 스크립트  
둘 중 어느 것을 **실제 제출 output 생성용**으로 쓸지 정한 뒤, 그 파일은 꼭 넣는 것이 좋습니다.

---

## 4. 요약: “꼭 넣어야 하는” py 파일만 정리

- **실행 1개**  
  - 제출한 **output.csv**를 만든 스크립트  
  - 예: `run_v8.py` 또는 `run_agent.py` (사용한 쪽)
- **그 스크립트가 import하는 모듈 전부**  
  - 대부분 `src/` 아래에 있음  
  - 예: `src/targeted_fn_v8.py`, `src/config.py`, `src/utils.py` 등
- **공통**  
  - `src/__init__.py`  
  - `requirements.txt`, `README.md`는 문서에서 요구하는 대로 포함

실제 디렉터리 구조와 다르면, “어떤 run_*.py로 output.csv를 만들었는지”만 정해 두고, 그 경로에서 **직접·간접 import 되는 .py**만 골라서 패키지에 넣으면 됩니다.

---

## 5. 시나리오별 최소 제출 .py 목록

### A) run_v8.py로 제출용 output 생성한 경우 (리더보드 0.76 등)

| 위치 | 파일 |
|------|------|
| 루트 | `run_v8.py` |
| src/ | `targeted_fn_v8.py` |

`targeted_fn_v8.py`는 stdlib·requests·dotenv만 쓰므로 위 두 개만 있으면 실행 가능합니다.  
(test.csv 경로는 run_v8.py 안이 절대경로라면, 제출 시 상대경로나 공개 예시 경로로 바꿔 두는 것이 좋습니다.)

### B) run_agent.py로 제출용 output 생성한 경우 (README 기준)

| 위치 | 파일 |
|------|------|
| 루트 | `run_agent.py` |
| src/ | `__init__.py`, `config.py`, `image_processor.py`, `saltlux_client.py`, `vision_analyzer.py`, `reasoner.py`, `decision_maker.py`, `verifier.py`, `agent_core.py`, `utils.py`, `integrated_agent.py` |

위는 `integrated_agent`가 import하는 모듈 기준입니다. 실제 프로젝트에 없는 이름이 있으면 해당 파일은 제외하면 됩니다.

### C) DEVELOPMENT_PLAN 제출 폴더 구조 그대로 쓰는 경우

```
├── run_agent.py          # 또는 실제 사용한 run_*.py
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── image_processor.py
│   ├── saltlux_client.py
│   ├── agent_core.py
│   └── utils.py
├── requirements.txt
└── README.md
```

실제로는 `integrated_agent.py` 등 위 실행 경로에서 쓰는 파일을 모두 넣어야 재현됩니다.
