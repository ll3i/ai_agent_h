import requests

API_KEY = "YOUR_API_KEY" # 팀별 API Key
# BRIDGE_URL은 문서에 나온 기본 도메인 (예: https://bridge.luxiacloud.com 등)
BASE_URL = "https://bridge.luxiacloud.com" 

headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

try:
    # 1. 모델 리스트 조회 엔드포인트 호출 (OpenAI 호환 방식일 경우)
    response = requests.get(f"{BASE_URL}/v1/models", headers=headers)
    
    if response.status_code == 200:
        models = response.json()['data']
        print("=== [사용 가능한 모델 리스트] ===")
        for m in models:
            print(f"- {m['id']}")
    else:
        print(f"Error: {response.status_code}, {response.text}")
        
except Exception as e:
    print(f"확인 실패: {e}")