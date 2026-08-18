import requests
import json
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE_PATH = os.path.join(BASE_DIR, "kakao_code.json")


def _refresh_kakao_token():
    """(내부용) 카카오 토큰을 자동 갱신하는 함수"""
    try:
        # 📌 수정: 고정된 텍스트가 아닌 '절대 경로(TOKEN_FILE_PATH)'를 사용해서 서랍 열기
        with open(TOKEN_FILE_PATH, "r") as fp:
            tokens = json.load(fp)
    except FileNotFoundError:
        print(f"❌ {TOKEN_FILE_PATH} 파일이 없습니다.")
        return None

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        return None

    url = "https://kauth.kakao.com/oauth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}
    data = {
        "grant_type": "refresh_token",
        "client_id": REST_API_KEY,
        "refresh_token": refresh_token
    }

    response = requests.post(url, headers=headers, data=data)
    new_tokens = response.json()

    if "access_token" in new_tokens:
        tokens["access_token"] = new_tokens["access_token"]
        if "refresh_token" in new_tokens:
            tokens["refresh_token"] = new_tokens["refresh_token"]

        # 📌 수정: 저장할 때도 '절대 경로'에 덮어쓰기
        with open(TOKEN_FILE_PATH, "w") as fp:
            json.dump(tokens, fp)
        return tokens["access_token"]

    return None



def send_kakao_message(text_message):
    """토큰 갱신부터 메시지 전송까지 한 번에 처리하는 함수"""
    # 1. 쏘기 전에 알아서 토큰 갱신부터 해오기
    access_token = _refresh_kakao_token()

    if not access_token:
        print("❌ 토큰 발급에 실패하여 메시지를 보낼 수 없습니다.")
        return

    # 2. 메시지 전송
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": text_message,
            "link": {
                "web_url": "https://localhost:3000",
                "mobile_web_url": "https://localhost:3000"
            },
            "button_title": "자비스 미니 브리핑"
        })
    }

    response = requests.post(url, headers=headers, data=payload)
    res_data = response.json()

    if res_data.get("result_code") == 0:
        print("🚀 [성공] 카카오톡 메시지가 전송되었습니다!")
    else:
        print("❌ [실패] 메시지 전송 오류:", res_data)