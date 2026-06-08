import json
from pathlib import Path
import requests
import streamlit as st

st.set_page_config(page_title="WebNovel 추천", layout="wide")

BACKEND = "http://localhost:8000"

# Load and cache webnovel data: prefer backend, fallback to local file
DATA_PATH = Path("web_novels.json")
NOVELS = []
try:
    resp = requests.get(f"{BACKEND}/novels", timeout=2)
    if resp.ok:
        NOVELS = resp.json()
except Exception:
    # fallback to local file
    if DATA_PATH.exists():
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            NOVELS = json.load(f)

# Prefer fetching options (genres/keywords) from backend; fallback to computing from NOVELS
GENRE_OPTIONS = []
KEYWORD_OPTIONS = []
try:
    resp = requests.get(f"{BACKEND}/options", timeout=2)
    if resp.ok:
        opts = resp.json()
        GENRE_OPTIONS = opts.get("genres", [])
        KEYWORD_OPTIONS = opts.get("keywords", [])
except Exception:
    # fallback to local extraction
    GENRE_OPTIONS = sorted({g for n in NOVELS for g in n.get("genre", [])})
    KEYWORD_OPTIONS = sorted({k for n in NOVELS for k in n.get("keywords", [])})

st.title("webnovel 추천 시스템")
st.write("학번: 2022204048  이름: 임재영")

# session defaults
if "user" not in st.session_state:
    st.session_state.user = None
if "read_ids" not in st.session_state:
    st.session_state.read_ids = []
if "show_signup" not in st.session_state:
    st.session_state.show_signup = False

# Create two tabs: Account first, then Recommendation
tabs = st.tabs(["계정", "추천"])


# --- Account tab (0) ---
with tabs[0]:
    st.subheader("로그인 / 회원가입")

    if st.session_state.user:
        st.success(f"로그인됨: {st.session_state.user}")
        if st.button("로그아웃"):
            st.session_state.user = None
            st.session_state.read_ids = []
            st.success("로그아웃 완료")

    st.markdown("### 로그인")
    col1, col2 = st.columns([2, 2])
    with col1:
        username = st.text_input("아이디", key="login_id")
    with col2:
        password = st.text_input("비밀번호", type="password", key="login_pw")

    if st.button("로그인", key="login_btn"):
        try:
            resp = requests.post(f"{BACKEND}/login", json={"username": username, "password": password}, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            st.session_state.user = data.get("username")
            st.session_state.read_ids = data.get("reads", []) or []
            st.success("로그인 성공")
        except Exception as e:
            st.error(f"로그인 실패: {e}")

    st.markdown("### 회원가입")
    if st.button("회원가입 창 열기", key="open_signup"):
        st.session_state.show_signup = True

    if st.session_state.show_signup:
        new_username = st.text_input("새 아이디", key="signup_id")
        new_password = st.text_input("새 비밀번호", type="password", key="signup_pw")
        confirm_password = st.text_input("비밀번호 확인", type="password", key="signup_pw_check")

        if st.button("회원가입 완료", key="signup_done"):
            if not new_username or not new_password:
                st.error("아이디와 비밀번호를 입력하세요.")
            elif new_password != confirm_password:
                st.error("비밀번호가 일치하지 않습니다.")
            else:
                try:
                    resp = requests.post(f"{BACKEND}/signup", json={"username": new_username, "password": new_password}, timeout=5)
                    resp.raise_for_status()
                    st.success("회원가입 완료. 로그인해주세요.")
                    st.session_state.show_signup = False
                except Exception as e:
                    st.error(f"회원가입 실패: {e}")

    st.markdown("---")
    st.write("현재 읽음 목록:")
    st.write(st.session_state.read_ids)


# --- Recommendation tab (1) ---
with tabs[1]:
    st.subheader("장르/키워드 기반 추천")

    if st.session_state.user is None:
        st.warning("추천을 사용하려면 먼저 계정으로 로그인하세요.")
        st.stop()

    if not NOVELS:
        st.warning("추천 데이터가 준비되지 않았습니다. 잠시 후 다시 시도하거나 백엔드를 확인하세요.")
    else:
        selected_genres = st.multiselect("장르 선택", GENRE_OPTIONS, key="ui_selected_genres")
        selected_keywords = st.multiselect("키워드 선택", KEYWORD_OPTIONS, key="ui_selected_keywords")

        if st.button("추천 받기", key="get_recommendations"):
            payload = {"genres": selected_genres, "keywords": selected_keywords, "exclude_ids": st.session_state.read_ids}
            try:
                resp = requests.post(f"{BACKEND}/recommendations", json=payload, timeout=5)
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

                        # 읽음 표시 버튼 (로그인한 경우)
                        if st.session_state.user:
                            novel_id = r.get('id')
                            if novel_id in st.session_state.read_ids:
                                st.info("읽음 처리됨")
                            else:
                                if st.button("읽음 표시", key=f"mark_read_{novel_id}"):
                                    try:
                                        resp2 = requests.post(f"{BACKEND}/user/{st.session_state.user}/reads", json={"novel_id": novel_id}, timeout=5)
                                        resp2.raise_for_status()
                                        reads = resp2.json().get('reads', [])
                                        st.session_state.read_ids = reads
                                        st.success("읽음으로 저장되었습니다.")
                                    except Exception as e:
                                        st.error(f"읽음 저장 실패: {e}")

                        st.markdown("---")
            except Exception as e:
                st.error(f"추천 요청 실패: {e}")
