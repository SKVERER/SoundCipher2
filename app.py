import streamlit as st
from scipy.io import wavfile
import numpy as np
from datetime import datetime
import uuid
from pydub import AudioSegment
import os
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av

st.set_page_config(page_title="🔐 Sound Cipher", layout="centered")
st.markdown("""
    <style>
        .stButton>button {
            text-align: left !important;
        }
    </style>
""", unsafe_allow_html=True)

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
        seconds = int(time_array[index]) % 60
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
        seconds = int(time_array[index]) % 60
        amplitude = data[int(index)]
        ascii_val = round(amplitude + seconds)
        if 32 <= ascii_val <= 126:
            message += chr(ascii_val)
        else:
            break
    return message

# --- קלט קובץ או הקלטה ---
st.subheader("⬆️ העלאת קובץ קול להצפנה")
uploaded_file = st.file_uploader("בחר קובץ קול (נתמך: wav, mp3, ogg, m4a)", type=["wav", "mp3", "ogg", "m4a"])
input_wav_path = None

if uploaded_file:
    temp_filename = f"uploaded_{uuid.uuid4().hex}"
    uploaded_file_path = temp_filename + uploaded_file.name[-4:]
    with open(uploaded_file_path, "wb") as f:
        f.write(uploaded_file.read())
    if not uploaded_file_path.endswith(".wav"):
        input_wav_path = temp_filename + ".wav"
        sound = AudioSegment.from_file(uploaded_file_path)
        sound.export(input_wav_path, format="wav")
        os.remove(uploaded_file_path)
    else:
        input_wav_path = uploaded_file_path

# --- הקלטה מהדפדפן ---
class AudioRecorder(AudioProcessorBase):
    def __init__(self):
        self.audio_frames = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        self.audio_frames.append(frame)
        return frame

st.subheader("🎙️ או הקלט ישירות מהאתר")
record = st.checkbox("סמן כאן כדי להקליט דרך הדפדפן")
recorded_audio_path = None

if record:
    ctx = webrtc_streamer(
        key="send_audio",
        mode="sendonly",
        in_audio=True,
        audio_processor_factory=AudioRecorder,
        media_stream_constraints={"audio": True, "video": False},
    )

    if ctx.audio_processor and st.button("💾 שמור הקלטה"):
        frames = ctx.audio_processor.audio_frames
        if frames:
            audio = AudioSegment.empty()
            for f in frames:
                samples = f.to_ndarray().flatten()
                seg = AudioSegment(
                    samples.tobytes(),
                    frame_rate=f.sample_rate,
                    sample_width=2,
                    channels=f.layout.channels
                )
                audio += seg

            recorded_audio_path = f"recorded_{uuid.uuid4().hex}.wav"
            audio.export(recorded_audio_path, format="wav")
            st.success("🎉 ההקלטה נשמרה!")
            st.audio(recorded_audio_path)

# --- קלטים להצפנה ---
message = st.text_input("💬 מסר להצפנה")
key_input = st.text_input("מפתח הצפנה (אופציונלי; ברירת מחדל: 300)", max_chars=4)
key = int(key_input) if key_input.isdigit() else 300

# --- הצפנה ---
if st.button("🔐 הצפן ושלח"):
    selected_input_path = input_wav_path or recorded_audio_path
    if not selected_input_path or not message:
        st.error("יש להעלות או להקליט קובץ קול ולהזין מסר.")
    else:
        output_path = f"encrypted_{uuid.uuid4().hex}.wav"
        encrypt_message_on_audio(selected_input_path, output_path, message, key)
        st.success("✔ ההצפנה הושלמה!")
        st.audio(output_path)
        with open(output_path, "rb") as f:
            st.download_button("📥 הורד את הקובץ המוצפן", f, file_name="encrypted.wav")

# --- פענוח ---
st.subheader("🔓 פענוח קובץ קול")
decrypt_file = st.file_uploader("📂 העלה קובץ מוצפן (WAV בלבד)", type=["wav"], key="decrypt")
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
