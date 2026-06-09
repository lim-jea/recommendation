import json
import os
from pathlib import Path

import requests
import streamlit as st


st.set_page_config(page_title="웹소설 추천 앱", layout="wide")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DATA_PATH = Path("web_novels.json")


@st.cache_data(ttl=60)
def fetch_novels():
    """FastAPI에서 웹소설 데이터를 받아오고, 실패하면 로컬 파일을 사용한다."""
    try:
        response = requests.get(f"{BACKEND_URL}/novels", timeout=3)
        response.raise_for_status()
        return response.json()
    except Exception:
        if DATA_PATH.exists():
            with DATA_PATH.open("r", encoding="utf-8") as file:
                return json.load(file)
    return []


@st.cache_data(ttl=60)
def fetch_options():
    try:
        response = requests.get(f"{BACKEND_URL}/options", timeout=3)
        response.raise_for_status()
        data = response.json()
        return data.get("genres", []), data.get("keywords", [])
    except Exception:
        novels = fetch_novels()
        genres = sorted({genre for novel in novels for genre in novel.get("genre", [])})
        keywords = sorted({keyword for novel in novels for keyword in novel.get("keywords", [])})
        return genres, keywords


def request_recommendations(genres, keywords, exclude_ids):
    payload = {
        "genres": genres,
        "keywords": keywords,
        "exclude_ids": exclude_ids,
    }
    response = requests.post(f"{BACKEND_URL}/recommendations", json=payload, timeout=5)
    response.raise_for_status()
    return response.json().get("recommendations", [])


def login(username, password):
    response = requests.post(
        f"{BACKEND_URL}/login",
        json={"username": username, "password": password},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def signup(username, password):
    response = requests.post(
        f"{BACKEND_URL}/signup",
        json={"username": username, "password": password},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def mark_as_read(username, novel_id):
    response = requests.post(
        f"{BACKEND_URL}/user/{username}/reads",
        json={"novel_id": novel_id},
        timeout=5,
    )
    response.raise_for_status()
    return response.json().get("reads", [])


if "user" not in st.session_state:
    st.session_state.user = None
if "read_ids" not in st.session_state:
    st.session_state.read_ids = []
if "show_signup" not in st.session_state:
    st.session_state.show_signup = False


novels = fetch_novels()
genre_options, keyword_options = fetch_options()

st.title("웹소설 취향 추천 서비스")
st.caption("학번: 2022204048 / 이름: 임재영")
st.write("선호 장르와 키워드를 고르면 FastAPI 백엔드가 점수를 계산해 웹소설을 추천합니다.")

account_tab, recommend_tab = st.tabs(["계정", "추천"])

with account_tab:
    st.subheader("로그인")

    if st.session_state.user:
        st.success(f"현재 로그인: {st.session_state.user}")
        if st.button("로그아웃"):
            st.session_state.user = None
            st.session_state.read_ids = []
            st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        username = st.text_input("아이디", key="login_id")
    with col2:
        password = st.text_input("비밀번호", type="password", key="login_pw")

    if st.button("로그인", key="login_btn"):
        try:
            data = login(username, password)
            st.session_state.user = data.get("username")
            st.session_state.read_ids = data.get("reads", []) or []
            st.success("로그인에 성공했습니다.")
            st.rerun()
        except Exception as error:
            st.error(f"로그인에 실패했습니다: {error}")

    st.divider()
    st.subheader("회원가입")

    if st.button("회원가입 열기", key="open_signup"):
        st.session_state.show_signup = True

    if st.session_state.show_signup:
        new_username = st.text_input("새 아이디", key="signup_id")
        new_password = st.text_input("새 비밀번호", type="password", key="signup_pw")
        confirm_password = st.text_input("비밀번호 확인", type="password", key="signup_pw_check")

        if st.button("회원가입 완료", key="signup_done"):
            if not new_username or not new_password:
                st.error("아이디와 비밀번호를 모두 입력해주세요.")
            elif new_password != confirm_password:
                st.error("비밀번호가 일치하지 않습니다.")
            else:
                try:
                    signup(new_username, new_password)
                    st.success("회원가입이 완료되었습니다. 로그인해주세요.")
                    st.session_state.show_signup = False
                except Exception as error:
                    st.error(f"회원가입에 실패했습니다: {error}")

    st.divider()
    st.write("읽음 처리된 작품 ID")
    st.write(st.session_state.read_ids)

with recommend_tab:
    st.subheader("장르와 키워드 기반 추천")

    if st.session_state.user is None:
        st.warning("추천 기능을 사용하려면 먼저 계정 탭에서 로그인해주세요.")
        st.stop()

    if not novels:
        st.error("웹소설 데이터를 불러오지 못했습니다. FastAPI 서버 상태를 확인해주세요.")
        st.stop()

    selected_genres = st.multiselect("선호 장르", genre_options)
    selected_keywords = st.multiselect("선호 키워드", keyword_options)

    if st.button("추천 받기", type="primary"):
        if not selected_genres and not selected_keywords:
            st.warning("장르나 키워드를 하나 이상 선택해주세요.")
            st.stop()

        try:
            recommendations = request_recommendations(
                selected_genres,
                selected_keywords,
                st.session_state.read_ids,
            )
        except Exception as error:
            st.error(f"추천 요청에 실패했습니다: {error}")
            st.stop()

        if not recommendations:
            st.info("조건에 맞는 추천 결과가 없습니다. 다른 장르나 키워드를 선택해보세요.")
            st.stop()

        st.success(f"{len(recommendations)}개의 추천 결과를 찾았습니다.")

        for item in recommendations:
            with st.container(border=True):
                st.markdown(f"### {item.get('title')}")
                st.write(item.get("description"))
                st.write(f"작가: {item.get('author', '정보 없음')}")
                st.write(f"추천 점수: {item.get('score')}")
                st.write(f"장르: {', '.join(item.get('genre') or [])}")
                st.write(f"키워드: {', '.join(item.get('keywords') or [])}")

                link = item.get("link")
                if link:
                    st.link_button("작품 정보 보기", link)

                novel_id = item.get("id")
                if novel_id in st.session_state.read_ids:
                    st.info("이미 읽음 처리된 작품입니다.")
                elif st.button("읽음으로 표시", key=f"mark_read_{novel_id}"):
                    try:
                        st.session_state.read_ids = mark_as_read(st.session_state.user, novel_id)
                        st.success("읽음 목록에 저장했습니다.")
                        st.rerun()
                    except Exception as error:
                        st.error(f"읽음 저장에 실패했습니다: {error}")
