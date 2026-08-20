import os
import sys
import requests
import random

# 상위 폴더의 services 모듈을 가져오기 위한 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from services.place_service import fetch_places

OLLAMA_MODEL = "llama3.1"


def get_search_keywords_from_llm(location):
    """[MC 역할 1] LLM을 이용해 중심 위치 주변의 세부 탐색 구역(반경 1km) 3곳을 설정합니다."""
    prompt = f"""
    사용자가 '{location}' 주변에서 친구와 약속이 있어.
    도보 10분(반경 1km) 내외로 이동 가능한 유명한 거리나 교차로 이름 3개만 뽑아줘.
    예시처럼 콤마(,)로만 구분해서 대답해.
    예시: 상수역 1번출구, 합정 카페거리, 당인리 발전소길
    """

    url = "http://localhost:11434/api/generate"
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.5}}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        text = response.json().get('response', '')
        keywords = [k.strip() for k in text.split(',') if k.strip()]
        return keywords[:3] if keywords else [location]
    except:
        return [location]


def filter_and_pool_places(keywords, category_type):
    """
    [MC 역할 2] PS(place_service)를 컨트롤하여 데이터를 모으고 파이썬으로 1차 필터링합니다.
    """
    pooled_places = []
    seen_urls = set()

    for keyword in keywords:
        search_query = f"{keyword} {category_type}"
        # PS(place_service)에 데이터 수집 명령!
        raw_places = fetch_places(search_query)

        for p in raw_places:
            # 1차 필터링: 맛집을 찾는데 '카페'나 '다방'이 카테고리에 있으면 아웃! (매머드커피 방지)
            if category_type == "맛집" and "카페" in p['full_category']:
                continue
            # 1차 필터링: 카페를 찾는데 '음식점' 메인 카테고리가 아니면 아웃!
            if category_type == "카페" and "카페" not in p['full_category']:
                continue

            if p['url'] not in seen_urls:
                seen_urls.add(p['url'])
                pooled_places.append(p)

    # 랜덤하게 섞어서 15개만 LLM에게 전달 (프롬프트 길이 조절)
    random.shuffle(pooled_places)
    return pooled_places[:15]


def curate_with_llm(location, place_type, places):
    """[MC 역할 3] 정제된 리스트를 LLM에게 넘겨 최종 3곳을 엄선합니다."""
    if not places:
        return f"[{place_type}] 적절한 장소를 찾지 못했습니다."

    places_str = ""
    for i, p in enumerate(places):
        places_str += f"{i + 1}. {p['name']} (분류: {p['short_category']}, 주소: {p['address']}) - URL: {p['url']}\n"

    prompt = f"""
    너는 센스 있는 일일 AI 비서 '자비스'야.
    사용자가 '{location}' 주변에서 친구와 만날 예정이야.
    아래는 카카오맵 실제 API 데이터로 수집하고 내가 1차로 필터링한 {place_type} 후보 목록이야.

    [후보 목록]
    {places_str}

    [임무 및 조건]
    1. 주소를 확인하고 '{location}'에서 걸어가기 너무 멀어보이는(동네 이름이 쌩뚱맞은) 곳은 제외해.
    2. 메뉴나 분위기가 겹치지 않는 가장 알짜배기 장소 3곳만 엄선해줘.
    3. 각 장소마다 다정한 말투(~해요체)로 1~2줄 추천 이유를 적어줘.
    4. 제공된 URL을 절대 변형하지 말고 그대로 출력해.

    [출력 양식]
    [{place_type} 추천]
    - 장소명 (분류)
      💬 자비스: (추천 이유 - 거리적인 장점도 포함해서 설명)
      🔗 링크: URL
    """

    url = "http://localhost:11434/api/generate"
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.8}}

    try:
        response = requests.post(url, json=payload)
        return response.json().get('response', '')
    except:
        return f"{place_type} AI 큐레이션 실패"


# ... (위쪽 import 및 프롬프트 함수 3개는 기존 그대로 유지) ...

def process_meetup_event(query_str, specific_categories=None):
    """이 함수가 애플 캘린더 일정을 돌거나 데일리플로우(멀티턴)에서 호출될 최종 파이프라인입니다."""
    print(f"\n🗺️ [MC 동작 1] '{query_str}' 주변 세부 탐색 구역(반경 1km) 설정 중...")

    # 🚀 [오류 해결 1] 이제 query_str에는 "상수역" 이라는 순수 장소만 들어옵니다.
    keywords = get_search_keywords_from_llm(query_str)
    print(f"   👉 설정 완료: {', '.join(keywords)}")

    # 🚀 [오류 해결 2] 밖에서 카테고리를 명확히 지정해줬다면(멀티턴), 억지로 텍스트를 읽지 않고 그것만 딱 씁니다!
    if specific_categories:
        target_categories = specific_categories
    else:
        # 캘린더에서 넘어온 일정 텍스트일 경우 (알아서 카테고리 추출)
        target_categories = []
        if "맛집" in query_str: target_categories.append("맛집")
        if "카페" in query_str: target_categories.append("카페")
        if "술집" in query_str: target_categories.append("술집")

        # 아무 조건이 안 적혀있으면 3종 풀코스!
        if not target_categories:
            target_categories = ["맛집", "카페", "술집"]

    print(f"\n📡 [MC 동작 2] PS(Place Service)를 구동하여 {', '.join(target_categories)} 데이터 수집 및 필터링 중...")

    reports = []
    total_places_count = 0

    for cat in target_categories:
        places = filter_and_pool_places(keywords, cat)
        total_places_count += len(places)
        report = curate_with_llm(query_str, cat, places)
        reports.append(report)

    print(f"\n🧠 [MC 동작 3] 수집된 총 {total_places_count}개의 장소 중 최종 큐레이션 완료!")

    final_report = f"📍 [자비스의 핫플 큐레이션]\n\n" + "\n\n".join(reports)
    return final_report


if __name__ == "__main__":
    from services.kakao_service import send_kakao_message

    test_location = "상수역"

    print("==================================================")
    print("🚀 [Integration Test] MC 엔진 ➔ 카카오톡 '나에게 보내기'")
    print("==================================================")

    # 파라미터 분리 테스트!
    report = process_meetup_event(test_location, specific_categories=["술집"])

    print("\n[생성된 큐레이션 리포트]")
    print(report)

    print("\n📱 카카오톡 '나와의 채팅방'으로 전송 중...")
    send_kakao_message(report)
    print("\n✅ 모든 테스트 절차 완료!")


