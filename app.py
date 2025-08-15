import streamlit as st
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable, NoTranscriptFound
import nltk
import textstat
from collections import Counter
import math
import os
from openai import OpenAI

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

# --- OpenAI configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        openai_status = "✅ OpenAI API configured"
    except Exception as e:
        openai_client = None
        openai_status = f"❌ OpenAI API failed: {e}"
else:
    openai_client = None
    openai_status = "⚠️ OpenAI API key not set"

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
    # Convert transcript snippets to dictionaries if needed
    transcript_data = []
    for item in transcript:
        if hasattr(item, 'text') and hasattr(item, 'start'):
            # It's a FetchedTranscriptSnippet object
            transcript_data.append({
                'text': item.text,
                'start': item.start,
                'duration': getattr(item, 'duration', 0)
            })
        else:
            # It's already a dictionary
            transcript_data.append(item)
    
    if include_timestamps:
        return "\n".join([f"[{int(t['start']//60):02d}:{int(t['start']%60):02d}] {t['text']}" for t in transcript_data])
    else:
        return " ".join([t['text'] for t in transcript_data])

# --- Convert transcript to dictionary format ---
def convert_transcript_to_dict(transcript):
    """Convert transcript snippets to dictionary format for easier handling"""
    transcript_data = []
    for item in transcript:
        if hasattr(item, 'text') and hasattr(item, 'start'):
            # It's a FetchedTranscriptSnippet object
            transcript_data.append({
                'text': item.text,
                'start': item.start,
                'duration': getattr(item, 'duration', 0)
            })
        else:
            # It's already a dictionary
            transcript_data.append(item)
    return transcript_data

# --- Summary generation functions ---
def calculate_sentence_scores(sentences, word_freq):
    """Calculate scores for sentences based on word frequency"""
    sentence_scores = {}
    
    for sentence in sentences:
        words = word_tokenize(sentence.lower())
        words = [word for word in words if word.isalnum()]
        
        score = 0
        word_count = 0
        
        for word in words:
            if word in word_freq:
                score += word_freq[word]
                word_count += 1
        
        if word_count > 0:
            sentence_scores[sentence] = score / word_count
        else:
            sentence_scores[sentence] = 0
    
    return sentence_scores

def get_word_frequency(text):
    """Get word frequency excluding stopwords"""
    try:
        stop_words = set(stopwords.words('english'))
    except:
        stop_words = set()
    
    words = word_tokenize(text.lower())
    words = [word for word in words if word.isalnum() and word not in stop_words and len(word) > 2]
    
    word_freq = Counter(words)
    
    # Normalize frequencies
# --- Summary generation functions ---
def calculate_sentence_scores(sentences, word_freq):
    """Calculate scores for sentences based on word frequency"""
    sentence_scores = {}
    
    for sentence in sentences:
        words = word_tokenize(sentence.lower())
        words = [word for word in words if word.isalnum()]
        
        score = 0
        word_count = 0
        
        for word in words:
            if word in word_freq:
                score += word_freq[word]
                word_count += 1
        
        if word_count > 0:
            sentence_scores[sentence] = score / word_count
        else:
            sentence_scores[sentence] = 0
    
    return sentence_scores

def get_word_frequency(text):
    """Get word frequency excluding stopwords"""
    try:
        stop_words = set(stopwords.words('english'))
    except:
        stop_words = set()
    
    words = word_tokenize(text.lower())
    words = [word for word in words if word.isalnum() and word not in stop_words and len(word) > 2]
    
    word_freq = Counter(words)
    
    # Normalize frequencies
# --- GPT-4 Summary generation ---
def generate_gpt4_summary(text, summary_type="comprehensive", max_length=400):
    """Generate summary using GPT-4"""
    if not openai_client:
        return None, "OpenAI API not configured"
    
    try:
        # Truncate text if too long (GPT-4 has token limits)
        if len(text) > 12000:  # Rough character limit
            text = text[:12000] + "..."
        
        prompts = {
            "comprehensive": f"""Please provide a comprehensive summary of this YouTube video transcript. 
Focus on the main topics, key insights, and important details discussed.
Keep it informative and well-structured, around {max_length} words.

Transcript:
{text}

Comprehensive Summary:""",
            
            "bullet_points": f"""Please extract the key points from this YouTube video transcript and present them as bullet points.
Focus on the most important information, insights, and takeaways.
Format as clear, concise bullet points, around {max_length} words total.

Transcript:
{text}

Key Points:
•""",
            
            "executive": f"""Please provide an executive summary of this YouTube video transcript.
Focus on the main conclusions, recommendations, and actionable insights.
Keep it concise and professional, around {max_length//2} words.

Transcript:
{text}

Executive Summary:"""
        }
        
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates clear, accurate summaries of video content."},
                {"role": "user", "content": prompts.get(summary_type, prompts["comprehensive"])}
            ],
            max_tokens=max_length * 2,  # Rough token estimate
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        return summary, None
        
    except Exception as e:
        print(f"DEBUG: OpenAI API error: {e}")
        return None, f"Error generating summary: {str(e)}"

def generate_multiple_summaries(text):
    """Generate multiple types of summaries"""
    summaries = {}
    
    # Comprehensive summary
    comp_summary, comp_error = generate_gpt4_summary(text, "comprehensive", 400)
    if comp_summary:
        summaries["comprehensive"] = comp_summary
    
    # Bullet points
    bullet_summary, bullet_error = generate_gpt4_summary(text, "bullet_points", 300)
    if bullet_summary:
        summaries["bullet_points"] = bullet_summary
    
    # Executive summary
    exec_summary, exec_error = generate_gpt4_summary(text, "executive", 200)
    if exec_summary:
        summaries["executive"] = exec_summary
    
    # Return summaries and any errors
    errors = [e for e in [comp_error, bullet_error, exec_error] if e]
    return summaries, errors[0] if errors else None

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
st.markdown("Extract transcripts from YouTube videos with captions/subtitles and generate AI summaries")

# Status indicators
col1, col2, col3 = st.columns([2, 1, 1])
with col2:
    if "✅" in proxy_status:
        st.success(proxy_status)
    else:
        st.error(proxy_status)

with col3:
    if "✅" in openai_status:
        st.success(openai_status)
    elif "⚠️" in openai_status:
        st.warning(openai_status)
    else:
        st.error(openai_status)

# Input section
st.markdown("### Enter YouTube URL or Video ID")
url_input = st.text_input(
    "YouTube URL or Video ID:",
    placeholder="e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ or dQw4w9WgXcQ",
    help="Supports various YouTube URL formats or direct video ID"
)

# Options
col1, col2 = st.columns(2)
with col1:
    generate_summary = st.checkbox("Generate AI Summary", value=False, disabled=not openai_client)
with col2:
    if not openai_client:
        st.info("💡 Set OPENAI_API_KEY environment variable to enable AI summaries")

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
                    # Convert transcript to dictionary format for processing
                    transcript_dict = convert_transcript_to_dict(transcript)
                    word_count = sum(len(t['text'].split()) for t in transcript_dict)
                    duration = max(t['start'] + t.get('duration', 0) for t in transcript_dict)
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
                
                # Generate AI Summary if requested
                if generate_summary and openai_client:
                    st.markdown("### 🤖 AI Generated Summary")
                    
                    with st.spinner("🔄 Generating AI summary..."):
                        plain_text = format_transcript(transcript, False)
                        summaries, summary_error = generate_multiple_summaries(plain_text)
                    
                    if summary_error:
                        st.error(f"❌ Summary generation failed: {summary_error}")
                    elif summaries:
                        # Create tabs for different summary types
                        if len(summaries) > 1:
                            tabs = st.tabs(["📋 Comprehensive", "🔸 Key Points", "📊 Executive"])
                            
                            if "comprehensive" in summaries:
                                with tabs[0]:
                                    st.markdown("**Comprehensive Summary:**")
                                    st.write(summaries["comprehensive"])
                            
                            if "bullet_points" in summaries:
                                with tabs[1]:
                                    st.markdown("**Key Points:**")
                                    st.write(summaries["bullet_points"])
                            
                            if "executive" in summaries:
                                with tabs[2]:
                                    st.markdown("**Executive Summary:**")
                                    st.write(summaries["executive"])
                        else:
                            # Single summary
                            summary_key = list(summaries.keys())[0]
                            st.write(summaries[summary_key])
                        
                        # Download summary options
                        st.markdown("#### 💾 Download Summaries")
                        col1, col2, col3 = st.columns(3)
                        
                        if "comprehensive" in summaries:
                            with col1:
                                st.download_button(
                                    "📋 Comprehensive Summary",
                                    data=summaries["comprehensive"],
                                    file_name=f"summary_comprehensive_{video_id}.txt",
                                    mime="text/plain"
                                )
                        
                        if "bullet_points" in summaries:
                            with col2:
                                st.download_button(
                                    "🔸 Key Points",
                                    data=summaries["bullet_points"],
                                    file_name=f"summary_keypoints_{video_id}.txt",
                                    mime="text/plain"
                                )
                        
                        if "executive" in summaries:
                            with col3:
                                st.download_button(
                                    "📊 Executive Summary",
                                    data=summaries["executive"],
                                    file_name=f"summary_executive_{video_id}.txt",
                                    mime="text/plain"
                                )
                
                # Download options for transcript
                st.markdown("### 💾 Download Transcript")
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
                    json_data = json.dumps(transcript_dict, indent=2)
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