import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from services.calendar_service import get_schedule
from services.ai_service import ask_ai
from services.kakao_service import send_kakao_message

if __name__ == "__main__":
    now = datetime.now()
    # 오늘 00:00부터 7일 뒤 00:00까지 범위 설정
    start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=7)

    start_str = start_time.strftime("%m월 %d일")
    end_str = (end_time - timedelta(days=1)).strftime("%m월 %d일")

    print(f"📅 [주간 브리핑] {start_str} ~ {end_str} 주간 일정 요약 시작...")

    # 7일간의 일정 가져오기
    events = get_schedule(start_time, end_time)

    if events and events != ["캘린더를 찾을 수 없습니다."]:
        print(f"\n[📅 향후 7일간의 일정 목록 (총 {len(events)}개)]")
        for idx, event in enumerate(events, 1):
            print(f"{idx}. {event}")

        events_text = "\n".join(events)

        # 📅 [주간 브리핑 전용] 출력 순서와 양식을 엄격하게 지정한 프롬프트
        prompt = f"""
        아래는 이번 주({start_str} ~ {end_str})의 전체 일정 목록입니다.

        [주간 일정 목록]
        {events_text}

        위 일정을 바탕으로 반드시 아래의 [작성 순서]에 맞춰서 주간 브리핑을 작성해 주세요.

        [작성 순서]
        1. 이번 주 일정 나열: 요일별로 어떤 일정들이 있는지 보기 좋게 나열해 주세요.
        2. 핵심 일정 및 조언: 이번 주에 꼭 챙겨야 할 중요한 일정들을 짚어주고, 비서로서 한 주를 잘 보내기 위한 친절한 조언을 덧붙여 주세요. (짧게 써줘)
        """

        ai_briefing = ask_ai(prompt)
        final_message = f"📅 [주간 일정 브리핑 ({start_str} ~ {end_str})]\n\n{ai_briefing}"
    else:
        print("\n[📅 주간 일정 목록] 없음")
        final_message = f"📅 [주간 일정 브리핑 ({start_str} ~ {end_str})]\n\n향후 7일간 예정된 일정이 없습니다. 여유로운 한 주를 즐기세요!"

    print("\n📱 카카오톡으로 주간 브리핑 전송을 시도합니다...")
    send_kakao_message(final_message)