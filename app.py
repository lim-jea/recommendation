import json
from pathlib import Path
import random

import matplotlib.pyplot as plt
import requests
import streamlit as st
from pathlib import Path

# Load and cache webnovel data once at module import
DATA_PATH = Path("web_novels.json")
if DATA_PATH.exists():
    with open(DATA_PATH, "r", encoding="utf-8") as _f:
        NOVELS = json.load(_f)
else:
    NOVELS = []

# Precompute unique genre and keyword options for UI
GENRE_OPTIONS = sorted({g for n in NOVELS for g in n.get("genre", [])})
KEYWORD_OPTIONS = sorted({k for n in NOVELS for k in n.get("keywords", [])})

st.title("webnovel 추천 시스템")
st.write("학번: 2022204048  이름: 임재영")


tabs = st.tabs(["추천"])

with tabs[0]:
    st.subheader("webnovel 추천 퀴즈")

    # --- 장르/키워드 선택 기반 추천 UI (캐시된 옵션 사용) ---
    st.markdown("---")
    st.subheader("장르/키워드 기반 추천")

    if not NOVELS:
        st.warning("web_novels.json 파일을 찾을 수 없습니다. 추천 UI를 사용하려면 파일을 프로젝트 루트에 두세요.")
    else:
        selected_genres = st.multiselect("장르 선택", GENRE_OPTIONS, key="ui_selected_genres")
        selected_keywords = st.multiselect("키워드 선택", KEYWORD_OPTIONS, key="ui_selected_keywords")

        backend_url = "http://localhost:8000/recommendations"

        if st.button("추천 받기", key="get_recommendations"):
            payload = {"genres": selected_genres, "keywords": selected_keywords}
            try:
                resp = requests.post(backend_url, json=payload, timeout=5)
                resp.raise_for_status()
                data = resp.json()
                recs = data.get("recommendations") or data
                if not recs:
                    st.info("조건에 맞는 추천이 없습니다.")
                else:
                    for r in recs:
                        st.markdown(f"**{r.get('title')}**  —  점수: {r.get('score')}")
                        st.write(r.get('description'))
                        st.write(f"장르: {', '.join(r.get('genre') or [])} | 키워드: {', '.join(r.get('keywords') or [])}")
                        st.markdown(f"[원문 보기]({r.get('link')})")
                        st.markdown("---")
            except Exception as e:
                st.error(f"추천 요청 실패: {e}")
