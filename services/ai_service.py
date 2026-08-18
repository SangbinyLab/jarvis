import requests
from dotenv import load_dotenv

# --- 👤 전역 설정: 비서가 부를 나의 이름 ---
USER_NAME = "상빈"  # (본명이나 원하시는 호칭으로 수정해 주세요!)

def ask_ai(task_prompt):
    """공통 프롬프트(페르소나/이름)와 개별 기능 프롬프트를 합쳐서 AI에게 전달하는 엔진"""
    print("🤖 AI 비서(Qwen 7B)가 생각 중입니다...")

    # ✨ 공통 프롬프트 (자비스의 기본 성격과 규칙 설정)
    common_prompt = f"""
당신은 '{USER_NAME}'님을 1:1로 보좌하는 유능하고 친절한 수석 AI 비서 '자비스'입니다.
[필수 규칙]
1. 답변을 시작할 때 반드시 '{USER_NAME}'님의 이름을 부르며 친근하게 인사하세요. (절대 '사용자님'이라고 부르지 마세요)
2. 프롬프트에서 요구한 번호 목록(1., 2., 3.)과 날씨/일정 데이터는 절대로 누락하지 말고 모두 출력하세요.
"""

    # 공통 규칙과 개별 명령(task_prompt)을 하나로 합침
    final_prompt = common_prompt + "\n\n[이번 지시 사항]\n" + task_prompt

    url = "http://localhost:11434/api/generate"
    payload = {
        #"model": "qwen2.5-coder:7b",
        "model": "llama3.1",
        "prompt": final_prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        return result["response"]
    except requests.exceptions.RequestException as e:
        return f"⚠️ AI 서버 통신 중 오류가 발생했습니다: {e}"