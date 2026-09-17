# 제출해야 하는 .py 파일 전체 목록

제출 시 포함할 **모든 Python 파일**을 정리한 목록입니다.

---

## 1. 제출 경로별 “전부” 목록

### A) run_v8.py 로 제출할 때 (리더보드 0.76 등, 최소)

이 경로만 쓰면 됩니다.

| 구분 | 경로 | 파일명 |
|------|------|--------|
| 루트 | 프로젝트 루트 | `run_v8.py` |
| src | src/ | `targeted_fn_v8.py` |

**총 2개**

---

### B) run_agent.py 로 제출할 때 (README 메인 실행)

아래 **전부** 넣어야 실행이 됩니다.

| 구분 | 경로 | 파일명 |
|------|------|--------|
| 루트 | 프로젝트 루트 | `run_agent.py` |
| src | src/ | `__init__.py` |
| src | src/ | `config.py` |
| src | src/ | `image_processor.py` |
| src | src/ | `saltlux_client.py` |
| src | src/ | `vision_analyzer.py` |
| src | src/ | `reasoner.py` |
| src | src/ | `decision_maker.py` |
| src | src/ | `verifier.py` |
| src | src/ | `agent_core.py` |
| src | src/ | `utils.py` |
| src | src/ | `integrated_agent.py` |

**총 12개** (루트 1 + src 11)

---

### C) “제출용 .py 전부” 한 번에 넣을 때

실행 경로( run_agent / run_v8 )와 관계없이, **제출 패키지에 들어갈 수 있는 .py를 전부** 넣을 때 사용하는 목록입니다.

#### 루트 (실행 스크립트)

```
run_agent.py
run_v8.py
run_full_analysis.py
baseline.py
validate_system.py
```

#### src/

```
src/__init__.py
src/config.py
src/image_processor.py
src/saltlux_client.py
src/vision_analyzer.py
src/reasoner.py
src/decision_maker.py
src/verifier.py
src/agent_core.py
src/utils.py
src/integrated_agent.py
src/targeted_fn_v8.py
src/targeted_fn_v7.py
src/roi_cropper.py
```

※ `run_full_analysis`가 `final_omni_agent` 등을 부르면, 그 체인에 있는  
`src/final_omni_agent.py`, `src/jtav_triple_vision.py`, `src/roi_cropper.py` 등도 해당 경로로 제출할 때는 같이 넣어야 합니다.

---

## 2. 복사해서 쓸 수 있는 전체 목록 (경로 없이 파일명만)

**run_v8 기준 최소 제출:**

```
run_v8.py
src/targeted_fn_v8.py
```

**run_agent 기준 제출 (전부):**

```
run_agent.py
src/__init__.py
src/config.py
src/image_processor.py
src/saltlux_client.py
src/vision_analyzer.py
src/reasoner.py
src/decision_maker.py
src/verifier.py
src/agent_core.py
src/utils.py
src/integrated_agent.py
```

**“제출용 py 전부” 로 넣을 때 (실행 스크립트 + 공통 src):**

```
run_agent.py
run_v8.py
run_full_analysis.py
baseline.py
validate_system.py
src/__init__.py
src/config.py
src/image_processor.py
src/saltlux_client.py
src/vision_analyzer.py
src/reasoner.py
src/decision_maker.py
src/verifier.py
src/agent_core.py
src/utils.py
src/integrated_agent.py
src/targeted_fn_v8.py
src/targeted_fn_v7.py
src/roi_cropper.py
```

---

## 3. 제출 시 넣어야 할 .py 파일 “전부” (한 줄에 하나씩)

아래를 그대로 복사해서 체크리스트로 쓸 수 있습니다.

**① run_v8 만 쓸 때 (최소 2개)**  
`run_v8.py`  
`src/targeted_fn_v8.py`

**② run_agent 쓸 때 (12개)**  
`run_agent.py`  
`src/__init__.py`  
`src/config.py`  
`src/image_processor.py`  
`src/saltlux_client.py`  
`src/vision_analyzer.py`  
`src/reasoner.py`  
`src/decision_maker.py`  
`src/verifier.py`  
`src/agent_core.py`  
`src/utils.py`  
`src/integrated_agent.py`

**③ run_full_analysis 쓸 때**  
`run_full_analysis.py`  
`src/__init__.py`  
`src/config.py`  
`src/utils.py`  
`src/final_omni_agent.py`  
`src/jtav_triple_vision.py`  
`src/luxia_enhanced_agent.py`  
`src/roi_cropper.py`  
(+ 위 모듈들이 import 하는 .py 전부)

**④ “제출용이라고 부를 수 있는 .py 전부” 넣을 때**  
루트: `run_agent.py`, `run_v8.py`, `run_full_analysis.py`, `baseline.py`, `validate_system.py`  
src: `__init__.py`, `config.py`, `image_processor.py`, `saltlux_client.py`, `vision_analyzer.py`, `reasoner.py`, `decision_maker.py`, `verifier.py`, `agent_core.py`, `utils.py`, `integrated_agent.py`, `final_omni_agent.py`, `jtav_triple_vision.py`, `luxia_enhanced_agent.py`, `roi_cropper.py`, `targeted_fn_v8.py`, `targeted_fn_v7.py`

---

## 4. 한 줄 요약

- **run_v8만 쓸 때:** `run_v8.py` + `src/targeted_fn_v8.py` (2개).
- **run_agent 쓸 때:** `run_agent.py` + `src/` 아래 11개 (위 B표 참고).
- **가능한 제출용 py 전부 넣을 때:** 루트 5개 + `src/` 11개 + `targeted_fn_v8.py`, `targeted_fn_v7.py`, `roi_cropper.py` (위 C 참고).

제출한 **output.csv**를 만든 실행 스크립트와, 그 스크립트가 **import 하는 .py**는 반드시 모두 포함해야 합니다.
