import re
import json
import time
import random
import requests
import pandas as pd # type: ignore
import base64
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =========================
# 설정
# =========================
# 참가자 안내:
# - 아래 API_KEY / BRIDGE_URL / MODEL은 솔트룩스 "LLM API 호출 설정" 문법을 따릅니다.
# - 이 베이스라인은 GPT-4o-mini를 Agent의 메인 LLM으로 하여,
# - (1) 이미지 관찰(LLM) -> (2) 규칙 기반 판단 -> (3) 애매하면 1회 재검토의 아주 기초적인 AI Agent 구조를 보여주는 예시입니다.
API_KEY = os.getenv("SALTLUX_API_KEY", "YOUR API KEY") # .env 파일에서 API KEY 로드
BRIDGE_URL = "https://bridge.luxiacloud.com/llm/openai/chat/completions/gpt-4o-mini/create"
MODEL = "gpt-4o-mini-2024-07-18"

# 입력(test.csv) / 출력(output.csv) 경로
TEST_CSV_PATH = "./test.csv" # 100장 테스트 데이터
OUT_PATH = "./output/output.csv"

# API 호출 헤더
HEADERS = {"apikey": API_KEY, "Content-Type": "application/json"}

# 대회 라벨 정의: 0=정상, 1=비정상
LABEL_NORMAL = 0
LABEL_ABNORMAL = 1

# =========================
# 관찰 항목
# =========================
# 참가자 안내:
# - "관찰할 결함 항목"을 정의하는 곳입니다.
# - (항목_key, 항목_설명) 형태로 되어 있어, 여기에 줄만 추가/삭제하면
#   프롬프트와 파싱 키(KEYS)가 자동으로 맞춰집니다.
# 분류 판단 기준 기반 관찰 항목 (6가지 불량 유형)
# 우선순위: lead_connectivity_fail(가장 중요) > component_missing > body_broken_severe > posture_bad > rotation_severe > surface_defect_only
OBS_ITEMS = [
    ("component_missing", "[Missing] Component completely missing - only PCB holes visible, no component"),
    ("lead_connectivity_fail", "[Connectivity-CRITICAL] Lead Cut/Miss/Short - lead is cut short, not in hole, or touching each other"),
    ("body_broken_severe", "[Broken] Body severely damaged - internal chip exposed with severe damage"),
    ("posture_bad", "[Posture] Bad posture - component lying down or flipped"),
    ("rotation_severe", "[Rotation] Severe misalignment - rotated 45 degrees or more"),
    ("surface_defect_only", "[Normal] Surface defects OK if connections are good"),
]

# OBS_ITEMS에서 key만 뽑아, 결과 JSON에서 가져올 항목 목록으로 사용합니다.
KEYS = [k for k, _ in OBS_ITEMS]

# =========================
# 시스템 프롬프트
# =========================
# 참가자 안내:
# - SYSTEM은 "모델의 역할/출력 규칙"을 고정하는 부분입니다.
# - JSON만 출력하도록 강제하여, 파싱 오류를 줄이려는 목적입니다.
SYSTEM = (
    "너는 반도체 소자 검사 이미지 분석기다.\n"
    "반드시 요청한 JSON만 출력한다. 다른 텍스트는 절대 출력하지 않는다.\n"
)

# =========================
# build_prompt(strict)
# =========================
# 역할:
# - OBS_ITEMS 기반으로 "관찰 프롬프트"를 자동 생성합니다.
# - strict=False: 일반 관찰(너무 애매하면 false)
# - strict=True : 더 보수적인 관찰(애매하면 무조건 false)
#
# 참가자 확장 포인트:
# - OBS_ITEMS를 바꾸면 프롬프트도 자동으로 바뀝니다.
# - strict 모드의 rule 문구를 바꾸면 "재검토 정책"을 쉽게 튜닝할 수 있습니다.
def build_prompt(strict: bool = False) -> str:
    header = """
You are a highly accurate IC component quality inspector for 3-lead transistors on PCB.

【CRITICAL: 6 Defect Classification System - FUNCTIONALITY OVER APPEARANCE】

CORE PRINCIPLE: A component is NORMAL if all leads are properly connected to PCB holes, even with cosmetic damage.
Only flag as ABNORMAL if there is actual functional defect.

1. component_missing (Missing Type): Component completely missing
   -> TRUE: Only PCB holes visible, no component at all (RARE - maybe 1-2 in 100)
   -> FALSE: Component is present (even partially visible)

2. lead_connectivity_fail (Connectivity Type) *** MOST CRITICAL ***
   ONLY flag TRUE if you can CLEARLY see lead connection problems.

   TRUE conditions - BE SPECIFIC (any of the following):
   - Cut: Lead is VISIBLY cut short (obvious length difference), end part missing, clearly broken
   - Miss: Lead CLEARLY not in its hole (floating above PCB, resting on surface, protruding outside)
   - Short: Leads OBVIOUSLY touching each other or inserted in same row of holes
   - Severe spread: Leads extremely spread apart, clearly missing their holes

   INSPECT EACH LEAD CAREFULLY:
   • Lead 1 (left): Does it reach AND enter its hole? Is it cut?
   • Lead 2 (middle): Does it reach AND enter its hole? Is it cut?
   • Lead 3 (right): Does it reach AND enter its hole? Is it cut?

   FALSE condition (DEFAULT - most cases):
   - All 3 leads appear to reach their holes
   - Leads may be slightly bent, scratched, or discolored - still FALSE if connected
   - Minor lifting or slight angle - still FALSE if tips enter holes
   - Surface oxidation, rough finish - still FALSE if connected

3. body_broken_severe (Broken Type): ONLY severe internal exposure
   -> TRUE: Internal chip/circuitry CLEARLY visible, half of body blown off, internal frame exposed
   -> FALSE: Surface cracks, dents, corner chips, paint damage (these are NORMAL if leads OK)
   -> IMPORTANT: Small cracks, scratches, corner damage = FALSE

4. posture_bad (Posture Type): Extreme orientation only
   -> TRUE: Component COMPLETELY lying flat on side OR fully inverted (upside down)
   -> FALSE: Standing upright (even if slightly tilted)

5. rotation_severe (Rotation Type): Extreme misalignment only
   -> TRUE: Rotated 45+ degrees (looks like diamond shape)
   -> FALSE: Normal orientation or slight tilt (<45 degrees)

6. surface_defect_only (Normal): Use this for cosmetic-only issues
   -> TRUE: Has scratches/dents/discoloration BUT all leads properly connected
   -> KEY RULE: "Ugly but functional" = NORMAL = surface_defect_only TRUE

"""

    # JSON 템플릿을 자동 생성합니다.
    json_template = "Output ONLY this JSON with NO other text:\n{\n" + ",\n".join([f'  "{k}": false' for k, _ in OBS_ITEMS]) + "\n}"

    # strict 여부에 따라 판단 기준 문구를 다르게 줍니다.
    if strict:
        rule = """
【STRICT MODE - Second Review】
If you see ANY of these, flag lead_connectivity_fail = TRUE:
- Lead CLEARLY cut short (obvious length difference)
- Lead CLEARLY not in hole (floating, outside hole)
- Leads TOUCHING each other
- Component completely lying down or inverted
Otherwise, be conservative -> FALSE
"""
    else:
        rule = """
【STANDARD MODE - Balanced Detection】

CRITICAL DECISION TREE:

Step 1: Check if component exists
- No component visible? -> component_missing = TRUE
- Component present? -> Continue to Step 2

Step 2: Check lead connectivity (MOST IMPORTANT)
For EACH of the 3 leads, ask:
  LEFT lead:   Can you see it reaching AND entering its hole? Is it cut?
  MIDDLE lead: Can you see it reaching AND entering its hole? Is it cut?
  RIGHT lead:  Can you see it reaching AND entering its hole? Is it cut?

If ANY lead is clearly CUT, MISSING, or NOT IN HOLE -> lead_connectivity_fail = TRUE
If ALL leads appear connected -> lead_connectivity_fail = FALSE (go to Step 3)

Step 3: Check severe body damage
- Can you see INTERNAL chip/circuitry? -> body_broken_severe = TRUE
- Only surface damage? -> body_broken_severe = FALSE (go to Step 4)

Step 4: Check posture
- Component lying FLAT or UPSIDE DOWN? -> posture_bad = TRUE
- Standing upright? -> posture_bad = FALSE (go to Step 5)

Step 5: Check rotation
- Rotated 45+ degrees (diamond shape)? -> rotation_severe = TRUE
- Normal angle? -> rotation_severe = FALSE (go to Step 6)

Step 6: Final classification
- Has cosmetic issues (scratches/dents) BUT leads connected? -> surface_defect_only = TRUE
- Clean appearance and leads connected? -> All FALSE (normal)

【REMEMBER】
- Bent leads are OK if they reach holes
- Scratched/dirty components are OK if leads connected
- Minor cracks are OK if no internal exposure
- When uncertain, prefer FALSE (normal) over TRUE (defect)
"""
    
    return header + "\n" + json_template + "\n" + rule

# 일반 관찰 프롬프트 / 보수적 관찰 프롬프트를 미리 만들어둡니다.
PROMPT_NORMAL = build_prompt(strict=False)
PROMPT_STRICT = build_prompt(strict=True)

# =========================
# _post_chat(messages)
# =========================
# 역할:
# - LLM API를 실제로 호출하는 함수입니다.
# - messages는 OpenAI ChatCompletions 형식과 유사한 구조를 사용합니다.
#
# 참가자 확장 포인트:
# - timeout을 늘리거나 줄일 수 있습니다.
# - MODEL을 바꾸면 성능/비용/속도 특성이 달라질 수 있습니다.
def _post_chat(messages, timeout=90):
    payload = {"model": MODEL, "messages": messages, "stream": False}
    r = requests.post(BRIDGE_URL, headers=HEADERS, json=payload, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"status={r.status_code}, body={r.text[:300]}")
    return r.json()["choices"][0]["message"]["content"].strip()

# =========================
# _safe_json_extract(s)
# =========================
# 역할:
# - LLM이 JSON만 출력하도록 요청했지만, 간혹 설명 문장이 섞일 수 있습니다.
# - 1차: json.loads로 바로 파싱 시도
# - 실패하면: 문자열에서 {...} 구간만 정규식으로 찾아 파싱 시도
#
# 참가자 확장 포인트:
# - 출력이 자주 깨진다면, 이 부분을 더 강하게 보정할 수 있습니다.
def _safe_json_extract(s: str) -> dict:
    try:
        return json.loads(s)
    except Exception:
        m = re.search(r"\{.*\}", s, flags=re.S)
        if m:
            return json.loads(m.group(0))
    raise ValueError(f"JSON parse failed: {s[:200]}")

# =========================
# _convert_to_data_uri(img_path)
# =========================
# 역할:
# - 로컬 이미지 파일을 base64로 인코딩하여 data URI로 변환합니다.
def _convert_to_data_uri(img_path: str) -> str:
    """Convert local image file to base64 data URI for API"""
    if img_path.startswith('http://') or img_path.startswith('https://'):
        return img_path

    # 로컬 파일 처리
    if not os.path.exists(img_path):
        raise FileNotFoundError(f"Image file not found: {img_path}")

    with open(img_path, 'rb') as f:
        img_data = f.read()

    base64_data = base64.b64encode(img_data).decode('utf-8')
    return f"data:image/png;base64,{base64_data}"

# =========================
# observe(img_url, strict)
# =========================
# Agent Step 1: Observe (관찰 단계)
#
# 역할:
# - 이미지 URL을 LLM에 전달하여, OBS_ITEMS에 정의된 결함 항목을 true/false로 관찰하게 합니다.
# - strict=False: 1차 관찰
# - strict=True : 애매하면 false로 보는 "재검토 관찰"
#
# 참가자 확장 포인트:
# - 관찰 항목을 더 추가하거나(예: surface_defect 등)
# - 프롬프트 문구를 더 구체화할 수 있습니다.
def observe(img_url: str, strict: bool = False) -> dict:
    prompt = PROMPT_STRICT if strict else PROMPT_NORMAL

    # 로컬 파일 경로를 data URI로 변환
    img_uri = _convert_to_data_uri(img_url)

    content = _post_chat([
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": img_uri}},
        ]},
    ])

    obs = _safe_json_extract(content)

    # 키 누락 대비:
    # - 어떤 키가 빠져도 기본값 false로 채워서 안정적으로 처리합니다.
    return {k: bool(obs.get(k, False)) for k in KEYS}

# =========================
# decide(obs)
# =========================
# Agent Step 2: Decide (판단 단계)
#
# 역할:
# - 관찰 결과(obs)에서 true 개수를 세고,
#   "하나라도 결함이면 비정상(1)"이라는 가장 단순한 규칙으로 라벨을 결정합니다.
#
# uncertain(재검토 대상) 정책:
# - 결함이 0개: 혹시 놓쳤을 수 있으니 재검토
# - 결함이 1개: 경계 케이스일 수 있으니 재검토
#
# 참가자 확장 포인트:
# - uncertain 조건을 바꾸면 호출 횟수/정확도 트레이드오프를 조정할 수 있습니다.
#   예) defect_count==0일 때만 재검토(더 빠름)
#   예) defect_count<=2일 때 재검토(더 보수적)
def decide(obs: dict):
    """
    분류 판단 기준에 따른 우선순위 기반 의사결정

    핵심 원칙: 흠집/파손이 있어도 기능(연결)에 문제없으면 정상으로 간주

    우선순위 (비정상 판정):
    1. lead_connectivity_fail (가장 중요) - 다리 절단/미삽/합선
    2. component_missing - 부품 전체 유실
    3. body_broken_severe - 내부 칩 노출 수준의 심각한 파손
    4. posture_bad - 누움/뒤집힘
    5. rotation_severe - 45도 이상 회전

    정상 판정:
    - 위 5가지 모두 False이면 정상
    """

    # 1. 연결형 결함 (가장 중요) - 다리 절단/미삽/합선
    if obs.get('lead_connectivity_fail', False):
        return LABEL_ABNORMAL, False  # 확정 비정상, 재검토 불필요

    # 2. 유령형 - 부품 전체 유실
    if obs.get('component_missing', False):
        return LABEL_ABNORMAL, False

    # 3. 파손형 - 내부 칩 노출 수준의 심각한 파손만
    if obs.get('body_broken_severe', False):
        return LABEL_ABNORMAL, False

    # 4. 곡예형 - 누움/뒤집힘
    if obs.get('posture_bad', False):
        return LABEL_ABNORMAL, False

    # 5. 회전형 - 45도 이상 회전
    if obs.get('rotation_severe', False):
        return LABEL_ABNORMAL, False

    # 6. 정상 판정
    # 모든 결함 항목이 False면 정상
    # surface_defect_only 상태와 관계없이 재검토 없이 확정
    return LABEL_NORMAL, False  # 확정 정상, 재검토 불필요

# =========================
# classify_agent(img_url)
# =========================
# Agent Step 3: Review (재검토 단계 포함)
#
# 역할:
# - 1차 관찰 -> decide
# - 애매하면(strict=True)로 1회 재검토 관찰 -> decide
# - 재검토에서 비정상으로 잡히면 비정상 확정
# - 그렇지 않으면 1차 결과를 유지합니다.
#
# max_retries:
# - 네트워크 오류, API 오류 등 일시적인 실패에 대비해 재시도합니다.
def classify_agent(img_url: str, max_retries=3) -> int:
    for attempt in range(max_retries):
        try:
            # 1) 1차 관찰
            obs1 = observe(img_url, strict=False)
            label1, uncertain = decide(obs1)

            # 2) 애매하지 않으면 바로 종료(불필요한 호출 방지)
            if not uncertain:
                return label1

            # 3) 애매하면 1회 재검토(더 보수적으로 판단)
            obs2 = observe(img_url, strict=True)
            label2, _ = decide(obs2)

            # 4) 재검토에서도 결함이 잡히면 비정상 확정
            if label2 == LABEL_ABNORMAL:
                return LABEL_ABNORMAL

            # 5) 재검토에서 결함이 없으면 1차 결과 유지
            return label1

        except Exception as e:
            # 마지막 시도까지 실패하면 예외를 그대로 올립니다.
            if attempt == max_retries - 1:
                raise

            # 간단한 backoff(재시도 간격 증가)로 서버/네트워크 불안정에 대응
            time.sleep((0.5 * (2 ** attempt)) + random.uniform(0, 0.2))

# =========================
# main()
# =========================
# 역할:
# - test.csv를 읽고(id, img_url 필요)
# - 각 이미지에 대해 classify_agent 실행
# - 최종 submission.csv를 (id, label) 컬럼으로 생성
#
# 참가자 확장 포인트:
# - time.sleep(0.2)를 조정하면 호출 속도를 바꿀 수 있습니다.
# - fallback label(기본값)을 바꿀 수도 있습니다(기본은 정상=0).
def main():
    # output 디렉토리가 없으면 생성
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    test_df = pd.read_csv(TEST_CSV_PATH)

    # test.csv에 필수 컬럼이 있는지 확인
    if "id" not in test_df.columns or "img_url" not in test_df.columns:
        raise ValueError(f"columns: {test_df.columns.tolist()}")

    preds = []
    n = len(test_df)

    print(f"\n[START] Starting automated classification for {n} images...")
    print(f"Input: {TEST_CSV_PATH}")
    print(f"Output: {OUT_PATH}\n")

    for i, row in test_df.iterrows():
        _id = row["id"]
        img_url = row["img_url"]

        try:
            label = classify_agent(img_url)
            label_str = "Normal(0)" if label == LABEL_NORMAL else "Abnormal(1)"
            print(f"[{i+1}/{n}] {_id} -> {label_str}")
        except Exception as e:
            # 오류 발생 시 정상(0) 판단으로 예외 처리
            print(f"[{i+1}/{n}] {_id} ERROR -> fallback Normal(0) | {e}")
            label = LABEL_NORMAL

        # 제출 형식: 무조건 id, label 컬럼
        preds.append({"id": _id, "label": label})

        # 너무 빠른 연속 호출로 인한 'API 호출 오류'를 피하기 위한 최소 sleep 설정
        time.sleep(0.2)

    # 최종 제출 파일 생성
    out_df = pd.DataFrame(preds, columns=["id", "label"])
    out_df.to_csv(OUT_PATH, index=False)

    # 통계 출력
    normal_count = (out_df['label'] == LABEL_NORMAL).sum()
    abnormal_count = (out_df['label'] == LABEL_ABNORMAL).sum()

    print(f"\n[COMPLETE] Classification Complete!")
    print(f"[STATS] Results:")
    print(f"   - Total: {n} images")
    print(f"   - Normal (0): {normal_count} images")
    print(f"   - Abnormal (1): {abnormal_count} images")
    print(f"\n[SAVE] Saved to: {OUT_PATH}")
    print(f"\nFirst 10 results:")
    print(out_df.head(10).to_string(index=False))

# 스크립트 실행 시 main() 수행
if __name__ == "__main__":
    main()