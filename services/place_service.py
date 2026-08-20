import os
import requests
from dotenv import load_dotenv

# 프로젝트 최상단의 .env 파일 로드
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")


def fetch_places(keyword, pages=3):
    """
    [Data Fetcher] 카카오 API를 호출하여 장소 데이터를 수집합니다.
    - 역할: 오직 주어진 키워드로 검색하고, 중복(URL 기준)을 제거하여 raw 데이터를 반환.
    - pages=3으로 설정하여 최대 45개의 데이터를 긁어옵니다.
    """
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}

    unique_places = {}

    for page in range(1, pages + 1):
        params = {"query": keyword, "size": 15, "page": page}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            documents = response.json().get('documents', [])

            if not documents:
                break

            for doc in documents:
                address = doc.get('road_address_name') or doc.get('address_name') or ""
                if not address:
                    continue

                place_url = doc.get('place_url')
                if place_url not in unique_places:
                    # 전체 카테고리 텍스트 보존 (예: "음식점 > 카페 > 커피전문점")
                    full_category = doc.get('category_name', '')
                    short_category = full_category.split('>')[-1].strip() if full_category else ""

                    unique_places[place_url] = {
                        'name': doc.get('place_name'),
                        'short_category': short_category,
                        'full_category': full_category,
                        'address': address,
                        'phone': doc.get('phone', ''),
                        'url': place_url
                    }
        except Exception as e:
            print(f"❌ 카카오 API 검색 오류 ({keyword}): {e}")
            break

    return list(unique_places.values())