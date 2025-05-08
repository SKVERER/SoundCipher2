import streamlit as st
from scipy.io import wavfile
import numpy as np
from datetime import datetime
import uuid
from pydub import AudioSegment
import os

# הגדרת הפונט (Heebo מ-Google Fonts)
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.set_page_config(page_title="🔐 Sound Cipher", layout="centered")
local_css("style.css")

st.title("🔐 Sound Cipher - הצפנה קולית")

# --- פונקציית הצפנה ---
def encrypt_message_on_audio(input_wav, output_wav, message, key=300):
    sample_rate, data = wavfile.read(input_wav)
    if len(data.shape) > 1:
        data = data[:, 0]
    data = data.astype(np.float32)
    time_array = np.arange(len(data)) / sample_rate
    month = datetime.now().month
    day = datetime.now().day
    step = month * day * key

    for i, char in enumerate(message):
        index = i * step
        if index >= len(data):
            break
        ascii_val = ord(char)
        seconds = int(time_array[int(index)]) % 60
        new_amplitude = ascii_val - seconds
        data[int(index)] = new_amplitude

    data = np.clip(data, -32768, 32767).astype(np.int16)
    wavfile.write(output_wav, sample_rate, data)
    return output_wav

# --- פונקציית פענוח ---
def decrypt_message_from_audio(input_wav, key=300):
    sample_rate, data = wavfile.read(input_wav)
    if len(data.shape) > 1:
        data = data[:, 0]
    data = data.astype(np.float32)
    time_array = np.arange(len(data)) / sample_rate
    month = datetime.now().month
    day = datetime.now().day
    step = month * day * key

    message = ""
    for index in range(0, len(data), step):
        seconds = int(time_array[int(index)]) % 60
        amplitude = data[int(index)]
        ascii_val = round(amplitude + seconds)
        if 32 <= ascii_val <= 126:
            message += chr(ascii_val)
        else:
            break
    return message

# --- העלאת קובץ ---
st.subheader("⬆️ העלאת קובץ WAV")
uploaded_file = st.file_uploader("בחר קובץ קול (WAV)", type=["wav"])
input_wav_path = None

if uploaded_file:
    input_wav_path = f"uploaded_{uuid.uuid4().hex}.wav"
    with open(input_wav_path, "wb") as f:
        f.write(uploaded_file.read())

# --- קלטים ---
message = st.text_input("💬 מסר להצפנה")
key_input = st.text_input("מפתח הצפנה (אופציונלי; מומלץ להגברת האבטחה)", max_chars=4)
key = int(key_input) if key_input.isdigit() else 300

# --- כפתור הצפנה ---
if st.button("🔐 הצפן ושלח"):
    if not input_wav_path or not message:
        st.error("יש להעלות קובץ קול ולהזין מסר.")
    else:
        output_path = f"encrypted_{uuid.uuid4().hex}.wav"
        encrypt_message_on_audio(input_wav_path, output_path, message, key)
        st.success("✔ ההצפנה הושלמה!")
        st.audio(output_path)
        with open(output_path, "rb") as f:
            st.download_button("📥 הורד את הקובץ המוצפן", f, file_name="encrypted.wav")

# --- כפתור פענוח ---
st.subheader("🔓 פענוח קובץ קול")
decrypt_file = st.file_uploader("📂 העלה קובץ מוצפן", type=["wav"], key="decrypt")
key_decrypt = st.text_input("🔑 מפתח לפענוח (כמו בהצפנה)", key="key_decrypt")
key_d = int(key_decrypt) if key_decrypt.isdigit() else 300

if st.button("🔎 פענח מסר"):
    if not decrypt_file:
        st.error("יש להעלות קובץ קול מוצפן.")
    else:
        decrypt_path = f"decrypt_{uuid.uuid4().hex}.wav"
        with open(decrypt_path, "wb") as f:
            f.write(decrypt_file.read())
        result = decrypt_message_from_audio(decrypt_path, key_d)
        st.success(f"📨 המסר המפוענח: {result}")
