import os
import sys
import threading
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

# 프로젝트 상위 경로 추가
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from services.calendar_service import get_schedule
from services.ai_service import ask_ai
from services.weather_service import get_tomorrow_weather
from functions.meetup_curator import process_meetup_event

app = Flask(__name__)

# 🚀 [핵심] 사용자의 대화 단계(State)를 기억하는 글로벌 메모리 (FSM)
USER_STATE = {}


def build_kakao_response(reply_text):
    """일반 텍스트를 카카오 규격으로 포장해 즉시 반환하는 함수"""
    return jsonify({
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": reply_text}}]
        }
    })


def custom_meetup_task(location, category, callback_url):
    """카테고리와 장소를 받아 MC 엔진을 돌리는 전용 백그라운드 스레드"""
    print(f"\n⚙️ [MeetUp 엔진] '{location}'의 '{category}' 검색을 시작합니다...")

    category_clean = category.replace(" ", "")
    # '모두'라고 하면 풀코스(맛집, 카페, 술집) 세팅
    if "모두" in category or "전부" in category or category_clean == "다" or "다 찾아" in category:
        target_cats = ["맛집", "카페", "술집"]
    else:
        # 단일 키워드 검색 시 공백만 제거해서 순수하게 전달
        target_cats = [category.strip()]

    try:
        # 🚀 [오류 완벽 해결] 장소와 카테고리를 강제로 합치지 않고 깔끔하게 분리해서 넘깁니다.
        reply_text = process_meetup_event(location, specific_categories=target_cats)

        if not reply_text or len(reply_text.strip()) == 0:
            reply_text = f"🥲 '{location}' 근처에 추천할 만한 '{category}' 장소를 찾지 못했어요. 검색어를 조금 바꿔서 다시 시도해 볼까요?"

    except Exception as e:
        reply_text = f"🚨 장소 검색 중 에러가 발생했습니다: {e}\n\n서버 로그를 확인해주세요."
        print(reply_text)

    # 🚀 1000자 초과 시 말풍선 연달아 쪼개서 보내기 (최대 3개)
    if callback_url:
        print("✅ [MeetUp 완료] 데일리플로우 채팅방으로 콜백 전송을 시도합니다.")

        outputs = []
        chunk_size = 980  # 카카오 제한(1000자)을 고려해 안전하게 980자 단위로 컷팅

        chunks = [reply_text[i:i + chunk_size] for i in range(0, len(reply_text), chunk_size)]

        for chunk in chunks[:3]:
            outputs.append({
                "simpleText": {
                    "text": chunk
                }
            })

        if len(chunks) > 3:
            outputs[-1]["simpleText"]["text"] += "\n\n(이하 내용은 카카오톡 길이 제한으로 생략되었습니다.)"

        res = requests.post(callback_url, json={
            "version": "2.0",
            "template": {"outputs": outputs}
        })

        if res.status_code == 200:
            print(f"🚀 [성공] 데일리플로우 챗봇 방에 {len(outputs)}개의 말풍선으로 브리핑을 띄웠습니다!")
        else:
            print(f"❌ [실패] 콜백 전송 실패 (에러코드 {res.status_code}): {res.text}")


# ---------------------------------------------------------------------
# 기존 일정 브리핑 처리 스레드
# ---------------------------------------------------------------------
def background_task(user_message, callback_url):
    now = datetime.now()
    reply_text = ""
    print("\n⚙️ [백그라운드 스레드] 일정 분석 시작...")

    if "내일" in user_message and "일정" in user_message:
        tomorrow = now + timedelta(days=1)
        start_time = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
        date_str = tomorrow.strftime("%m월 %d일")
        events = get_schedule(start_time, end_time)

        if events and events != ["캘린더를 찾을 수 없습니다."]:
            events_text = "\n".join(events)
            weather_info = get_tomorrow_weather()
            prompt = f"당신은 AI 비서 자비스입니다. 내일({date_str}) 일정을 브리핑해 주세요.\n날씨:{weather_info}\n[일정]\n{events_text}"
            reply_text = f"🌙 [내일({date_str}) 브리핑]\n\n{ask_ai(prompt)}"

            # 친구 약속 감지
            for ev in events:
                if "(친구)" in ev:
                    reply_text += f"\n\n──────────────────\n\n{process_meetup_event(ev)}"
        else:
            reply_text = f"🌙 [내일({date_str}) 일정]\n내일은 예정된 일정이 없습니다!"

    elif "오늘" in user_message and "일정" in user_message:
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
        date_str = now.strftime("%m월 %d일")
        events = get_schedule(start_time, end_time)

        if events and events != ["캘린더를 찾을 수 없습니다."]:
            events_text = "\n".join(events)
            prompt = f"당신은 AI 비서 자비스입니다. 오늘({date_str}) 일정을 요약해 주세요.\n[일정]\n{events_text}"
            reply_text = f"☀️ [오늘({date_str}) 일정]\n\n{ask_ai(prompt)}"
        else:
            reply_text = f"☀️ [오늘({date_str}) 일정]\n오늘 남은 일정이 없습니다!"

    elif "이번주" in user_message or "이번 주" in user_message:
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=7)
        events = get_schedule(start_time, end_time)

        if events and events != ["캘린더를 찾을 수 없습니다."]:
            events_text = "\n".join(events)
            prompt = f"당신은 AI 비서 자비스입니다. 이번 주 일정을 요약해 주세요.\n[일정]\n{events_text}"
            reply_text = f"📅 [이번 주 일정 브리핑]\n\n{ask_ai(prompt)}"
        else:
            reply_text = "📅 이번 주에는 예정된 일정이 없습니다!"

    # 일정 결과도 혹시 1000자가 넘을 수 있으니 안전하게 분할 전송 로직 적용
    if callback_url:
        print("✅ [일정 연산 완료] 콜백 전송을 시도합니다.")
        outputs = []
        chunk_size = 980
        chunks = [reply_text[i:i + chunk_size] for i in range(0, len(reply_text), chunk_size)]

        for chunk in chunks[:3]:
            outputs.append({"simpleText": {"text": chunk}})

        if len(chunks) > 3:
            outputs[-1]["simpleText"]["text"] += "\n\n(이하 생략)"

        requests.post(callback_url, json={
            "version": "2.0",
            "template": {"outputs": outputs}
        })


@app.route('/kakao', methods=['POST'])
def kakao_webhook():
    body = request.get_json() or {}

    # 유저 ID와 메시지 추출
    user_id = body.get('userRequest', {}).get('user', {}).get('id', 'default_user')
    user_message = body.get('userRequest', {}).get('utterance', '').strip()
    callback_url = body.get('userRequest', {}).get('callbackUrl')

    print(f"📩 [수신] 사용자({user_id}): {user_message}")

    # 유저 상태 초기화 (서버 켜지고 처음 말 건 경우)
    if user_id not in USER_STATE:
        USER_STATE[user_id] = {"step": "idle", "location": "", "category": ""}

    state = USER_STATE[user_id]

    # [예외 처리] 대화 도중 "오늘 일정 알려줘" 같은 다른 명령을 치면 즉시 탈출!
    if "일정" in user_message:
        state["step"] = "idle"

    # -------------------------------------------------------------
    # 🚀 멀티턴 대화 라우터 (State Machine)
    # -------------------------------------------------------------
    if user_message.lower() == "meetup!":
        state["step"] = "wait_location"
        return build_kakao_response("📍 어디서 만나실 예정인가요?\n(예: 홍대, 강남역, 광교)")

    elif state["step"] == "wait_location":
        state["location"] = user_message
        state["step"] = "wait_category"
        return build_kakao_response(f"'{user_message}' 좋네요! 🍽️\n맛집, 카페, 술집 중 무엇을 원하시나요?\n(혹은 '모두'라고 입력해주세요!)")

    elif state["step"] == "wait_category":
        location = state["location"]
        category = user_message
        state["step"] = "idle"  # 1회성 사이클이 끝났으므로 평소 상태로 초기화

        # 콜백 요청 & 백그라운드에서 검색 가동!
        thread = threading.Thread(target=custom_meetup_task, args=(location, category, callback_url))
        thread.start()

        # 카카오톡 채널에 점 3개(...) 로딩 애니메이션 띄우기
        return jsonify({"version": "2.0", "useCallback": True})

    # -------------------------------------------------------------
    # 기존 일정 모드 라우터
    # -------------------------------------------------------------
    else:
        if "일정" in user_message:
            thread = threading.Thread(target=background_task, args=(user_message, callback_url))
            thread.start()
            return jsonify({"version": "2.0", "useCallback": True})
        else:
            return build_kakao_response("🤖 자비스입니다. 하단 메뉴를 이용하시거나 'MeetUp!'이라고 입력해 주세요.")


if __name__ == '__main__':
    print("🚀 데일리플로우 Flask 서버(멀티턴 탑재 완전체) 5001번 포트 실행 중...")
    app.run(host='0.0.0.0', port=5001, debug=True)
