import json

from fastapi import FastAPI
import uvicorn
from model import UserPreference, RecommendationResult

app = FastAPI()

def load_webnovel_data():
    with open("web_novels.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/recommendations")
async def get_recommendations(user_preference: UserPreference):
    webnovel_data = load_webnovel_data()
    results = []
    
    pref_genres = [g.strip().lower() for g in (user_preference.genres or [])]
    pref_keywords = [k.strip().lower() for k in (user_preference.keywords or [])]

    for novel in webnovel_data:
        novel_genres = [g.strip().lower() for g in (novel.get("genre") or [])]
        novel_keywords = [k.strip().lower() for k in (novel.get("keywords") or [])]

        genre_matches = len(set(pref_genres) & set(novel_genres))
        keyword_matches = len(set(pref_keywords) & set(novel_keywords))

        if keyword_matches > 0 or genre_matches > 0:
            score = genre_matches + 2 * keyword_matches
            results.append({
                "id": novel.get("id"),
                "title": novel.get("title"),
                "author": novel.get("author"),
                "score": score,
                "genre": novel.get("genre"),
                "keywords": novel.get("keywords"),
                "description": novel.get("description"),
                "link": novel.get("link")
            })

    results.sort(key=lambda x: (-x["score"], x.get("title", "")))
    return {"recommendations": results}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


"""
장르/키워드 분류 및 추천 규칙 안내

1) 표준 장르:
    - 판타지, 로맨스, 액션, 게임, 무협, 스릴러, 스릴러/미스터리, SF,
      아포칼립스, 슈퍼히어로, 학원, 코미디, 드라마, 스포츠, 로맨스판타지

2) 표준 키워드:
    - 시스템, 전생/재생, 이세계, 타임루프, 성장, 전투, 던전, 헌터,
      마법, 마법학, 경제, 정치, 전략, 서바이벌, 여관, 메타, 스컬프터,
      e스포츠, 프로게이머, 몬스터, 암살자, 능력치, 현실게임화

3) 추천 규칙
    - 장르 매칭: 사용자 선호 장르와 소설의 장르 배열에 공통 항목이 하나라도 있으면 후보로 포함.
    - 키워드 매칭: 사용자 선호 키워드와 소설의 키워드 배열에 공통 항목이 하나라도 있으면 반드시 추천 후보에 포함.
    - 우선순위 산정: 장르 매칭 개수 + (키워드 매칭 개수 * 가중치(예:2)) 형태의 점수를 부여하여 매칭 수가 많을수록 상위에 노출.
    - 읽음 제외: 사용자가 읽음으로 표시한 `id` 목록은 추천 후보에서 제외.

4) 데이터 표준화 권장 방식
    - `genre` 필드는 문자열 리스트로 유지하여 다중 장르를 표현.
    - `keywords` 필드는 소문자/일관된 태그 형식으로 유지 (공백 대신 하이픈 또는 붙여쓰기 권장).
    - 새로운 소설 추가 시 위 표준 리스트 중 적절한 항목으로 태깅하도록 유도.
"""
