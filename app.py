import streamlit as st
import os
import pandas as pd
from datetime import datetime, timedelta
import time
import random

st.set_page_config(page_title="자율주행 태도 평가 설문", layout="wide")

# 초기 상태 설정
if "step" not in st.session_state:
    st.session_state.step = "start_check"
if "index" not in st.session_state:
    st.session_state.index = 0
if "responses" not in st.session_state:
    st.session_state.responses = []
if "user_info" not in st.session_state:
    st.session_state.user_info = {}
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "paused" not in st.session_state:
    st.session_state.paused = False

# 파일 경로
PAIR_FILE = "sentence_pairs_attitude.csv"
SAVE_FILE = "responses_temp.csv"
BACKUP_FILE = "responses_backup.csv"
TIME_LIMIT_HOURS = 3

@st.cache_data
def load_data():
    return pd.read_csv(PAIR_FILE)

df_original = load_data()
total_pairs = len(df_original)
if "shuffled_ids" not in st.session_state:
    st.session_state.shuffled_ids = random.sample(range(total_pairs), total_pairs)

# 함수
def generate_participant_id(name, year, phone):
    suffix = phone[-4:] if len(phone) >= 4 else "XXXX"
    return f"{name}_{year}_{suffix}"

def get_remaining_time():
    if st.session_state.paused:
        return st.session_state.remaining_at_pause
    elapsed = time.time() - st.session_state.start_time
    remaining = max(0, TIME_LIMIT_HOURS * 3600 - elapsed)
    return timedelta(seconds=int(remaining))

# 1단계: 사용자 정보 입력
if st.session_state.step == "start_check":
    st.title("📋 자율주행 태도 평가 설문 시작")
    with st.form("user_info_form"):
        st.subheader("기본 정보 입력")
        name = st.text_input("이름")
        birth_year = st.selectbox("출생 연도", list(range(1985, 2009)))
        phone = st.text_input("휴대폰 번호 (대시 '-' 없이 입력)")
        submitted = st.form_submit_button("설문 시작하기")

    if submitted:
        participant_id = generate_participant_id(name, birth_year, phone)
        st.session_state.user_info = {
            "참가자 ID": participant_id,
            "이름": name,
            "출생 연도": birth_year,
            "휴대폰": phone,
            "응답 시작 시각": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.step = "instruction"
        st.session_state.start_time = time.time()
        st.rerun()

# 2단계: 설명 및 동의
elif st.session_state.step == "instruction":
    st.header("2️⃣ 설문 설명 및 동의")
    st.markdown("#### ✅ 이 설문은 '자율주행에 대한 태도' 문장들의 유사도를 평가하는 것입니다.")
    st.markdown("총 25개의 문장으로 이루어진 문장쌍을 평가합니다. 각 문장은 다른 문장과 짝을 이루며 평가됩니다.")

    explanations = [
        "자율주행차 운전자들의 태도를 반영한 문장들을 두 개씩 제시합니다.",
        "응답자는 두 문장이 얼마나 유사한지를 1점(완전히 다름)에서 7점(거의 동일함)까지 주관적으로 판단하여 평가합니다.",
        "총 문장쌍 수는 300개이며, 설문 시간은 약 1.5시간~2시간이 소요됩니다.",
        "가능한 한 응답을 중단하지 않고 한 번에 완료해 주세요.",
    ]

    all_checked = True
    for i, explanation in enumerate(explanations):
        st.markdown(f"- {explanation}")
        if not st.checkbox(" 이해했습니다", key=f"agree_{i}"):
            all_checked = False

    if all_checked:
        st.success("설문을 시작할 수 있습니다!")
        if st.button("👉 설문 시작하기"):
            st.session_state.step = "survey"
            st.session_state.start_time = time.time()
            st.rerun()
    else:
        st.warning("모든 항목을 체크해야 다음 단계로 진행할 수 있습니다.")

# 3단계: 설문 본문
elif st.session_state.step == "survey":
    st.title("문장 유사도 평가 설문")

    remaining = get_remaining_time()
    if remaining.total_seconds() <= 0:
        st.warning("⚠️ 응답 가능 시간이 초과되었습니다. 설문은 계속 진행할 수 있지만, 가능한 빠르게 완료해 주세요.")
    else:
        st.info(f"⏱️ 남은 시간: {remaining}")

    answered_ids = [r["ID"] for r in st.session_state.responses if r["참가자 ID"] == st.session_state.user_info["참가자 ID"]]
    current_idx = len(answered_ids)
    st.markdown(f"**응답 질문: {current_idx + 1} / {total_pairs}**")

    rating_labels = {
        "1 - 완전히 다름": 1,
        "2 - 매우 다름": 2,
        "3 - 꽤 다름": 3,
        "4 - 비슷함": 4,
        "5 - 꽤 비슷함": 5,
        "6 - 매우 비슷함": 6,
        "7 - 거의 동일함": 7
    }

    i = st.session_state.index
    while i < total_pairs:
        shuffled_i = st.session_state.shuffled_ids[i]
        row = df_original.iloc[shuffled_i]
        if not any(r["ID"] == row["ID"] and r["참가자 ID"] == st.session_state.user_info["참가자 ID"] for r in st.session_state.responses):
            break
        i += 1
        st.session_state.index = i

    if i < total_pairs:
        shuffled_i = st.session_state.shuffled_ids[i]
        row = df_original.iloc[shuffled_i]

        st.markdown("**문장 A:**")
        st.markdown(f"> {row['Sentence A']}")
        st.markdown("**문장 B:**")
        st.markdown(f"> {row['Sentence B']}")

        choice = st.radio("두 문장의 유사도는?", list(rating_labels.keys()), index=3)
        rating = rating_labels[choice]

        if st.button("다음"):
            combined = {
                "ID": int(row["ID"]),
                "Sentence A": row["Sentence A"],
                "Sentence B": row["Sentence B"],
                "Rating": rating,
                "응답 시각": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            combined.update(st.session_state.user_info)
            st.session_state.responses.append(combined)

            df_responses = pd.DataFrame(st.session_state.responses)
            df_responses.to_csv(SAVE_FILE, index=False)
            df_responses.to_csv(BACKUP_FILE, index=False)

            st.session_state.index += 1
            st.rerun()
    else:
        st.success("설문이 완료되었습니다. 감사합니다!")
        final_df = pd.DataFrame(st.session_state.responses)
        filename = "responses_attitude.csv"
        final_df.to_csv(filename, index=False)
        st.download_button("응답 데이터 다운로드", data=final_df.to_csv(index=False), file_name=filename, mime="text/csv")
