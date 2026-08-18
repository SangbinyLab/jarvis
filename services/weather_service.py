import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# --- 설정 ---
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
CITY = "Suwon"  # 기본 지역 설정 (수원)


def get_tomorrow_weather():
    """OpenWeather API를 호출해 내일의 최고/최저 기온과 날씨 상태를 요약해주는 함수"""
    if WEATHER_API_KEY == "":
       return "⚠️ 날씨 API 키가 아직 설정되지 않았습니다."

    print("🌤️ 기상청(OpenWeather)에서 내일 날씨를 확인 중입니다...")

    # 5일간의 3시간 단위 일기예보 API 호출 (섭씨 온도 사용: units=metric, 한국어: lang=kr)
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={WEATHER_API_KEY}&units=metric&lang=kr"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # 내일 날짜 문자열 구하기 (예: '2026-08-19')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        # 가져온 전체 데이터 중 '내일'에 해당하는 시간대 데이터만 쏙 뽑아내기
        tomorrow_data = [item for item in data['list'] if item['dt_txt'].startswith(tomorrow)]

        if not tomorrow_data:
            return "내일 날씨 정보를 불러올 수 없습니다."

        # 내일 하루 중 가장 낮은 온도와 가장 높은 온도 계산
        temps = [item['main']['temp'] for item in tomorrow_data]
        min_temp = min(temps)
        max_temp = max(temps)

        # 낮 12시 무렵의 대표 날씨 상태 가져오기 (없으면 내일 첫 번째 데이터 사용)
        midday_weather = next((item for item in tomorrow_data if '12:00:00' in item['dt_txt']), tomorrow_data[0])
        description = midday_weather['weather'][0]['description']

        # AI에게 넘겨줄 예쁜 날씨 요약 텍스트 완성!
        weather_summary = f"{description}, 최고 {max_temp:.1f}°C / 최저 {min_temp:.1f}°C"
        return weather_summary

    except Exception as e:
        return f"⚠️ 날씨 정보를 가져오는데 실패했습니다: {e}"


# (테스트용 실행부)
if __name__ == "__main__":
    print(get_tomorrow_weather())