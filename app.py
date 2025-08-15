import streamlit as st
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable, NoTranscriptFound

# --- Proxy configuration ---
PROXY_USERNAME = "labvizce-staticresidential"  # Replace
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

# --- Extract video ID from various YouTube URL formats ---
def extract_video_id(url_or_id: str) -> str:
    """
    Extract video ID from various YouTube URL formats or return the ID if already provided.
    
    Supported formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://youtube.com/watch?v=VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    - VIDEO_ID (direct video ID)
    """
    if not url_or_id:
        return None
    
    # Clean the input
    url_or_id = url_or_id.strip()
    
    # If it's already a video ID (11 characters, alphanumeric with - and _)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    
    # YouTube URL patterns
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:m\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    return None

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

# --- Format transcript for display ---
def format_transcript(transcript, include_timestamps=True):
    """Format transcript for display"""
    if include_timestamps:
        return "\n".join([f"[{int(t['start']//60):02d}:{int(t['start']%60):02d}] {t['text']}" for t in transcript])
    else:
        return " ".join([t['text'] for t in transcript])

# --- Get video info ---
def get_video_info(video_id: str):
    """Get basic video information"""
    try:
        # YouTube thumbnail URL
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        return {
            'thumbnail': thumbnail_url,
            'url': video_url,
            'id': video_id
        }
    except:
        return None

# --- Streamlit UI ---
st.set_page_config(
    page_title="YouTube Transcript Extractor",
    page_icon="📺",
    layout="wide"
)

st.title("📺 YouTube Transcript Extractor")
st.markdown("Extract transcripts from YouTube videos with captions/subtitles")

# Proxy status
col1, col2 = st.columns([3, 1])
with col2:
    if "✅" in proxy_status:
        st.success(proxy_status)
    else:
        st.error(proxy_status)

# Input section
st.markdown("### Enter YouTube URL or Video ID")
url_input = st.text_input(
    "YouTube URL or Video ID:",
    placeholder="e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ or dQw4w9WgXcQ",
    help="Supports various YouTube URL formats or direct video ID"
)

# Examples
with st.expander("📋 Supported URL formats"):
    st.markdown("""
    **Supported formats:**
    - `https://www.youtube.com/watch?v=VIDEO_ID`
    - `https://youtu.be/VIDEO_ID`
    - `https://youtube.com/watch?v=VIDEO_ID`
    - `https://m.youtube.com/watch?v=VIDEO_ID`
    - `https://www.youtube.com/embed/VIDEO_ID`
    - `https://www.youtube.com/v/VIDEO_ID`
    - `VIDEO_ID` (direct video ID)
    
    **Example URLs:**
    - `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
    - `https://youtu.be/dQw4w9WgXcQ`
    - `dQw4w9WgXcQ`
    """)

if st.button("🎬 Extract Transcript", type="primary"):
    if not ytt_api:
        st.error("❌ API not initialized. Check proxy settings.")
    elif not url_input.strip():
        st.warning("⚠️ Please enter a YouTube URL or video ID")
    else:
        # Extract video ID
        video_id = extract_video_id(url_input)
        
        if not video_id:
            st.error("❌ Invalid YouTube URL or video ID format")
            st.info("Please check the supported formats in the expandable section above.")
        else:
            # Show video info
            video_info = get_video_info(video_id)
            if video_info:
                col1, col2 = st.columns([1, 2])
                with col1:
                    try:
                        st.image(video_info['thumbnail'], width=300)
                    except:
                        st.info("📷 Thumbnail not available")
                
                with col2:
                    st.markdown(f"**Video ID:** `{video_info['id']}`")
                    st.markdown(f"**Video URL:** [Open in YouTube]({video_info['url']})")
            
            # Extract transcript
            with st.spinner("🔄 Extracting transcript..."):
                transcript, error = get_transcript(video_id)
            
            if error:
                st.error(f"❌ {error}")
                st.info("💡 Make sure the video has captions/subtitles available.")
            else:
                st.success("✅ Transcript extracted successfully!")
                
                # Display options
                col1, col2 = st.columns(2)
                with col1:
                    show_timestamps = st.checkbox("Show timestamps", value=True)
                with col2:
                    word_count = sum(len(t['text'].split()) for t in transcript)
                    duration = max(t['start'] + t.get('duration', 0) for t in transcript)
                    st.info(f"📊 {word_count} words • {int(duration//60)}:{int(duration%60):02d} duration")
                
                # Format and display transcript
                formatted_transcript = format_transcript(transcript, show_timestamps)
                
                st.markdown("### 📄 Transcript")
                st.text_area(
                    "Transcript content:",
                    formatted_transcript,
                    height=400,
                    label_visibility="collapsed"
                )
                
                # Download options
                st.markdown("### 💾 Download Options")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.download_button(
                        "📝 Download as TXT (with timestamps)",
                        data=format_transcript(transcript, True),
                        file_name=f"transcript_{video_id}_timestamps.txt",
                        mime="text/plain"
                    )
                
                with col2:
                    st.download_button(
                        "📄 Download as TXT (plain text)",
                        data=format_transcript(transcript, False),
                        file_name=f"transcript_{video_id}_plain.txt",
                        mime="text/plain"
                    )
                
                with col3:
                    # JSON format for developers
                    import json
                    json_data = json.dumps(transcript, indent=2)
                    st.download_button(
                        "🔧 Download as JSON",
                        data=json_data,
                        file_name=f"transcript_{video_id}.json",
                        mime="application/json"
                    )

# Footer
st.markdown("---")
st.markdown(
    "💡 **Note:** This tool only works with videos that have captions/subtitles available (auto-generated or manual)."
)