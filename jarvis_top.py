import schedule
import time
import subprocess
import os
import sys  # 👈 1. sys 모듈 추가

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FUNCTIONS_DIR = os.path.join(BASE_DIR, "functions")


def run_task(script_name):
    script_path = os.path.join(FUNCTIONS_DIR, script_name)
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')

    print(f"[{current_time}] 🚀 {script_name} 실행 시작!")

    try:
        # 👈 2. "python3" 대신 sys.executable (현재 실행 중인 venv 파이썬) 사용!
        subprocess.run([sys.executable, script_path], check=True)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ {script_name} 실행 완료!")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ {script_name} 실행 중 오류 발생: {e}")


# ==========================================
# ⏰ 스케줄 등록 부 (여기만 유지보수 하면 됩니다!)
# ==========================================

print("🤖 Jarvis Master Scheduler가 가동되었습니다. (백그라운드 감시 중...)")

# 1. 매주 일요일 21시 정각: 주간 브리핑
schedule.every().sunday.at("21:00").do(run_task, "weekly_briefing.py")

# 2. 매일(월~일) 22시 정각: 일일 브리핑
schedule.every().day.at("22:00").do(run_task, "daily_briefing.py")

# 3. 매일 매시간 정각(00분): 시간별 임박 일정 브리핑
schedule.every().hour.at(":00").do(run_task, "hourly_briefing.py")

# (나중에 새로운 기능이 생기면 아래에 한 줄만 추가하면 됩니다!)
# 예: schedule.every().day.at("07:00").do(run_task, "weather_briefing.py")

# ==========================================
# 🔄 무한 루프 (시계 감시)
# ==========================================
if __name__ == "__main__":
    while True:
        # 등록된 스케줄 중에 지금 실행해야 할 시간이 된 게 있는지 확인
        schedule.run_pending()

        # 1초마다 확인하면 CPU 낭비가 없으므로 1초씩 재웁니다.
        time.sleep(1)