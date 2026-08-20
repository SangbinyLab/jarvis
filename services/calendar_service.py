import os
import caldav
import urllib.parse
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

# 프로젝트 최상단의 .env 파일 절대 경로로 찾아오기
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# --- 설정 ---
APPLE_ID = os.getenv("APPLE_ID")
APP_PASSWORD = os.getenv("APP_PASSWORD")
safe_id = urllib.parse.quote(APPLE_ID)
CALDAV_URL = f"https://{safe_id}:{APP_PASSWORD}@caldav.icloud.com/"

WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]


def get_schedule(start_time, end_time):
    """지정된 시간 범위의 캘린더 일정을 (날짜/요일 + 시간 + 일정명 + 장소) 형태로 가져오는 함수"""
    print("🚀 iCloud 캘린더에 접속 중...")

    client = caldav.DAVClient(url=CALDAV_URL)
    principal = client.principal()

    calendars = principal.calendars()
    if not calendars:
        return ["캘린더를 찾을 수 없습니다."]

    my_calendar = calendars[0]

    events = my_calendar.search(start=start_time, end=end_time, event=True)

    schedule_list = []
    for event in events:
        component = event.get_icalendar_component()
        if component and component.get('summary'):
            summary = str(component.get('summary'))

            # 🚀 [수정됨] 위치(Location) 데이터 파싱 추가!
            location_prop = component.get('location')
            location_str = str(location_prop) if location_prop else ""

            dtstart_prop = component.get('dtstart')
            dtend_prop = component.get('dtend')

            time_str = ""
            if dtstart_prop:
                dt_start = dtstart_prop.dt
                # 특정 시간 일정이 있는 경우
                if isinstance(dt_start, datetime):
                    if dt_start.tzinfo is not None:
                        dt_start = dt_start.astimezone()

                    weekday = WEEKDAYS[dt_start.weekday()]
                    date_prefix = f"{dt_start.strftime('%m/%d')}({weekday})"
                    start_time_formatted = dt_start.strftime("%H:%M")

                    if dtend_prop and isinstance(dtend_prop.dt, datetime):
                        dt_end = dtend_prop.dt
                        if dt_end.tzinfo is not None:
                            dt_end = dt_end.astimezone()
                        end_time_formatted = dt_end.strftime("%H:%M")
                        time_str = f"[{date_prefix} {start_time_formatted} ~ {end_time_formatted}] "
                    else:
                        time_str = f"[{date_prefix} {start_time_formatted}] "
                # 종일 일정인 경우
                elif isinstance(dt_start, date):
                    weekday = WEEKDAYS[dt_start.weekday()]
                    time_str = f"[{dt_start.strftime('%m/%d')}({weekday}) 종일] "

            # 🚀 [수정됨] 장소 정보가 있으면 문자열 끝에 추가해서 MC 엔진이 읽을 수 있게 함
            if location_str:
                schedule_list.append(f"{time_str}{summary} (장소: {location_str})")
            else:
                schedule_list.append(f"{time_str}{summary}")

    return schedule_list