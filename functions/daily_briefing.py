import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from services.calendar_service import get_schedule
from services.ai_service import ask_ai
from services.kakao_service import send_kakao_message
from services.weather_service import get_tomorrow_weather

if __name__ == "__main__":
    now = datetime.now()
    tomorrow = now + timedelta(days=1)

    start_time = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=1)

    date_str = tomorrow.strftime("%m월 %d일")
    print(f"🌙 [일일 브리핑] {date_str} 일정 요약 시작...")

    events = get_schedule(start_time, end_time)

    if events and events != ["캘린더를 찾을 수 없습니다."]:
        print("\n[📅 내일의 일정 목록]")
        for idx, event in enumerate(events, 1):
            print(f"{idx}. {event}")

        events_text = "\n".join(events)
        weather_info = get_tomorrow_weather()
        # 🌙 [기능 2 전용] 내일 밤 브리핑에 최적화된 프롬프트!
        prompt = f"""
당신은 나의 유능하고 친절한 AI 비서 '자비스'입니다.
아래는 나의 내일({date_str}) 전체 일정 목록입니다.
내일 일정을 저에게 간단하게 브리핑해 주세요.
각 일정은 1. 2. 처럼 인덱스를 붙여서 나열할 것.
참고로 날씨 정보는 OpenWeather APIs 를 이용해서 얻어오는 정보야.
날씨 브리핑은 최고 온도/ 최저 온도/ 비,눈,햇빛 여부 포함해서 해줘.
[내일의 날씨]
{weather_info}

[내일의 일정]
{events_text}

"""
        # AI 엔진에 맞춤 프롬프트 전달
        ai_briefing = ask_ai(prompt)
        final_message = f"🌙 [내일({date_str})의 브리핑]\n\n{ai_briefing}"
    else:
        print("\n[📅 내일의 일정 목록] 없음")
        final_message = f"🌙 [내일({date_str})의 브리핑]\n\n내일은 예정된 일정이 없습니다. 편안한 밤 보내세요!"

    print("\n📱 카카오톡으로 브리핑 전송을 시도합니다...")
    send_kakao_message(final_message)