import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable, NoTranscriptFound

# --- Proxy configuration ---
PROXY_USERNAME = "labvizce"  # Replace
PROXY_PASSWORD = "x2za3x15c9ah"  # Replace

try:
    ytt_api = YouTubeTranscriptApi(
        proxy_config=WebshareProxyConfig(
            proxy_username=PROXY_USERNAME,
            proxy_password=PROXY_PASSWORD,
            filter_ip_locations=["de", "us"],
        )
    )
    proxy_status = "✅ Proxy configured"
except Exception as e:
    ytt_api = None
    proxy_status = f"❌ Proxy failed: {e}"

# --- Get transcript ---
def get_transcript(video_id: str):
    try:
        transcript_list = ytt_api.list(video_id)
        if not transcript_list:
            return None, "No transcripts available"

        # Try English first
        for t in transcript_list:
            if t.language_code.startswith("en"):
                return t.fetch(), None

        # Otherwise first available transcript
        return transcript_list[0].fetch(), None

    except TranscriptsDisabled:
        return None, "Transcripts disabled for this video"
    except VideoUnavailable:
        return None, "Video unavailable"
    except NoTranscriptFound:
        return None, "No transcript found"
    except Exception as e:
        return None, f"Error: {e}"

# --- Streamlit UI ---
st.title("📺 YouTube Transcript Extractor (Video ID)")
st.info(proxy_status)

video_id = st.text_input("Enter YouTube Video ID (e.g., dQw4w9WgXcQ):")

if st.button("Get Transcript"):
    if not ytt_api:
        st.error("API not initialized. Check proxy settings.")
    elif not video_id.strip():
        st.warning("Please enter a video ID")
    else:
        transcript, err = get_transcript(video_id)
        if err:
            st.error(err)
        else:
            text = "\n".join([f"[{round(t['start'],1)}s] {t['text']}" for t in transcript])
            st.text_area("Transcript", text, height=400)
