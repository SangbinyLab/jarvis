import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from services.calendar_service import get_schedule
from services.ai_service import ask_ai
from services.kakao_service import send_kakao_message

if __name__ == "__main__":
    now = datetime.now()
    # 현재 시각부터 앞으로 1시간 이내 범위 지정
    next_one_hour = now + timedelta(hours=1)

    current_time_str = now.strftime("%H:%M")
    next_time_str = next_one_hour.strftime("%H:%M")

    print(f"⏰ [시간별 알림] {current_time_str} ~ {next_time_str} 다가오는 일정 확인 중...")

    # 1시간 이내 일정 조회 (calendar_service 사용)
    events = get_schedule(now, next_one_hour)

    # 임박한 일정이 있을 때만 동작!
    if events and events != ["캘린더를 찾을 수 없습니다."]:
        print("\n[🚨 임박 일정 발견!]")
        for idx, event in enumerate(events, 1):
            print(f"{idx}. {event}")

        events_text = "\n".join(events)

        # ⏰ [임박 일정 전용] 간결하고 명확한 리마인드 프롬프트
        prompt = f"""
당신은 나의 친절하고 유능한 AI 비서 '자비스'입니다.
현재 시각은 {current_time_str}이며, 앞으로 1시간 이내에 시작되거나 진행 중인 임박 일정이 있습니다.

아래 일정 목록을 확인하고, 
1. 몇 시에 무슨 일정인지 정확한 시간을 명시해 주세요.
2. 시작 전 챙겨야 할 준비물이나 유의사항을 1~2줄로 짧고 명확하게 리마인드해 주세요.

[임박 일정 목록]
{events_text}
"""
        # AI 호출 및 전송
        ai_briefing = ask_ai(prompt)
        final_message = f"⏰ [임박 일정 알림 ({current_time_str})]\n\n{ai_briefing}"

        print("\n📱 카카오톡으로 임박 알림 전송 중...")
        send_kakao_message(final_message)
    else:
        # 일정이 없으면 조용히 종료 (스팸 방지)
        print(f"✅ 앞으로 1시간 이내({current_time_str} ~ {next_time_str})에 예정된 일정이 없습니다.")