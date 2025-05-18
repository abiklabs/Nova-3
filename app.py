import streamlit as st
import yt_dlp
import nest_asyncio
from deepgram import DeepgramClient, PrerecordedOptions
import os

# Apply async patch for Streamlit
nest_asyncio.apply()

# Load API key from Streamlit secrets
DEEPGRAM_API_KEY = st.secrets["DEEPGRAM_API_KEY"]

# UI setup
st.set_page_config(page_title="Transcribe", layout="centered")
st.title("🎙️ Transcribe Audio or Video to Text")

# Tabbed layout for upload vs URL
tab_upload, tab_link = st.tabs(["Upload", "From link"])

uploaded_file = None
video_url = ""

with tab_upload:
    st.markdown("### Upload a file")
    uploaded_file = st.file_uploader("Choose a file (MP3 or MP4)", type=["mp3", "mp4"])

with tab_link:
    st.markdown("### Paste video or audio link")
    video_url = st.text_input("Enter your link here...", placeholder="e.g. https://youtube.com/...")

# Helpers
def save_uploaded_file(file):
    path = os.path.join("/tmp", file.name)
    with open(path, "wb") as f:
        f.write(file.read())
    return path

def download_audio(url):
    output_base = "/tmp/audio"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_base + '.%(ext)s',
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_base + ".mp3"

def transcribe_file(mp3_path):
    dg = DeepgramClient(DEEPGRAM_API_KEY)
    options = PrerecordedOptions(
        model="nova-3",
        language="en",
        smart_format=True,
        paragraphs=True,
        diarize=True,
    )
    response = dg.listen.prerecorded.v("1").transcribe_path(mp3_path, options)
    transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]
    return transcript

# Main logic
if uploaded_file or video_url:
    if st.button("🧠 Transcribe"):
        audio_path = None

        if uploaded_file:
            with st.spinner("📦 Saving uploaded file..."):
                audio_path = save_uploaded_file(uploaded_file)

        elif video_url.strip():
            with st.spinner("🔗 Downloading from link..."):
                try:
                    audio_path = download_audio(video_url)
                except Exception as e:
                    st.error(f"❌ Failed to fetch audio: {e}")

        if audio_path:
            st.audio(audio_path)
            with st.spinner("💬 Transcribing with Deepgram Nova-3..."):
                try:
                    transcript = transcribe_file(audio_path)
                    st.success("✅ Done!")
                    st.subheader("📄 Transcript")
                    st.text_area("Transcript", transcript, height=300)
                    st.download_button("📥 Download Transcript (.txt)", data=transcript, file_name="transcript.txt", mime="text/plain")
                except Exception as e:
                    st.error(f"❌ Transcription failed: {e}")
