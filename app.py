import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable, NoTranscriptFound
import re

# Proxy configuration
def initialize_api():
    """Initialize API with proxy configuration"""
    try:
        # Try to initialize with Webshare proxy
        proxy_api = YouTubeTranscriptApi(
            proxy_config=WebshareProxyConfig(
            proxy_username="labvizce",  # Replace with your actual proxy username
            proxy_password="x2za3x15c9ah",
            filter_ip_locations=["de", "us"],
            )
        )
        return proxy_api, True, "✅ Proxy configured successfully"
    except Exception as e:
        # Fallback to direct connection (will likely fail due to rate limiting)
        try:
            direct_api = YouTubeTranscriptApi()
            return direct_api, False, f"⚠️ Proxy failed: {str(e)}. Using direct connection (may get rate limited)"
        except Exception as e2:
            return None, False, f"❌ API initialization failed: {str(e2)}"

# Initialize API
ytt_api, proxy_enabled, api_status = initialize_api()

def extract_video_id(youtube_video_url):
    """Extract video ID from different YouTube URL formats"""
    video_id = None
    
    if "youtube.com/watch?v=" in youtube_video_url:
        video_id = youtube_video_url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in youtube_video_url:
        video_id = youtube_video_url.split("youtu.be/")[1].split("?")[0]
    elif "youtube.com/embed/" in youtube_video_url:
        video_id = youtube_video_url.split("embed/")[1].split("?")[0]
    
    if not video_id:
        raise ValueError("Could not extract video ID from URL")
    
    return video_id

def get_any_available_transcript(video_id):
    """Get any available transcript - tries English first, then any other language"""
    try:
        # First, try to get list of available transcripts
        transcript_list = ytt_api.list(video_id)
        
        if not transcript_list:
            return {
                'success': False,
                'error': "No transcripts available for this video"
            }
        
        # Priority order: English variants first, then any other language
        english_codes = ['en', 'en-US', 'en-GB', 'en-CA', 'en-AU']
        
        # Try English first
        for lang_code in english_codes:
            for transcript in transcript_list:
                if transcript.language_code == lang_code:
                    try:
                        transcript_data = transcript.fetch()
                        return process_transcript_data(transcript_data, transcript.language, lang_code, is_preferred=True)
                    except Exception:
                        continue
        
        # If no English found, try any available transcript
        for transcript in transcript_list:
            try:
                transcript_data = transcript.fetch()
                return process_transcript_data(
                    transcript_data, 
                    transcript.language, 
                    transcript.language_code,
                    is_preferred=False,
                    is_generated=transcript.is_generated
                )
            except Exception:
                continue
        
        # If still no transcript found
        return {
            'success': False,
            'error': "Could not fetch any available transcript"
        }
        
    except TranscriptsDisabled:
        return {'success': False, 'error': "Transcripts are disabled for this video"}
    except VideoUnavailable:
        return {'success': False, 'error': "Video is unavailable or private"}
    except NoTranscriptFound:
        return {'success': False, 'error': "No transcripts found for this video"}
    except Exception as e:
        return {'success': False, 'error': f"Error accessing video: {str(e)}"}

def process_transcript_data(transcript_data, language_name, language_code, is_preferred=False, is_generated=False):
    """Process transcript data into formatted output"""
    formatted_transcript = ""
    full_text = ""
    
    for entry in transcript_data:
        timestamp = format_timestamp(entry['start'])
        text = entry['text']
        formatted_transcript += f"[{timestamp}] {text}\n"
        full_text += f" {text}"
    
    duration = transcript_data[-1]['start'] + transcript_data[-1]['duration'] if transcript_data else 0
    
    return {
        'success': True,
        'language_name': language_name,
        'language_code': language_code,
        'is_english': language_code.startswith('en'),
        'is_generated': is_generated,
        'is_preferred': is_preferred,
        'formatted_transcript': formatted_transcript,
        'full_text': full_text.strip(),
        'duration': duration,
        'word_count': len(full_text.strip().split()),
        'line_count': len(formatted_transcript.split('\n')) - 1
    }
def format_timestamp(seconds):
    """Convert seconds to MM:SS or HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def main():
    st.set_page_config(
        page_title="YouTube English Transcript Extractor",
        page_icon="📺",
        layout="wide"
    )
    
    st.title("📺 YouTube Transcript Extractor")
    st.markdown("**Extract transcripts from YouTube videos - tries English first, then any available language**")
    
    with st.sidebar:
        st.header("📋 Instructions")
        st.markdown("""
        1. **Configure proxy credentials** in the code first
        2. **Paste YouTube URL** in the input field
        3. **Click Extract** to get English transcript
        4. **View transcript** with timestamps
        5. **Download** transcript as text file
        
        **Proxy Configuration Required:**
        - Update proxy credentials in the code
        - Without proxy: YouTube will block requests
        - Replace `<proxy-username>` and `<proxy-password>`
        
        **Language Priority:**
        - **1st Priority:** English (en, en-US, en-GB, en-CA, en-AU)
        - **2nd Priority:** Any other available language
        - **Automatic fallback** if English not available
        - Shows language info in results
        
        **Supported URL formats:**
        - `youtube.com/watch?v=VIDEO_ID`
        - `youtu.be/VIDEO_ID`
        - `youtube.com/embed/VIDEO_ID`
        """)
        
        # Proxy status
        st.markdown("### 🔧 Proxy Status")
        if proxy_enabled:
            st.success("✅ Proxy is configured and active")
        else:
            st.error("❌ Proxy not working - you'll likely get rate limited")
            st.markdown("""
            **To fix:**
            1. Get Webshare proxy credentials from https://webshare.io/
            2. Replace `<proxy-username>` and `<proxy-password>` in the code
            3. Restart the application
            """)
        
        st.info(f"**Status:** {api_status}")
    
    # Main input
    col1, col2 = st.columns([4, 1])
    
    with col1:
        youtube_link = st.text_input(
            "Enter YouTube Video Link:",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste any YouTube video URL here"
        )
    
    with col2:
        extract_button = st.button("🔍 Extract Transcript", type="primary", use_container_width=True)
    
    # Show video thumbnail if valid URL
    if youtube_link:
        try:
            video_id = extract_video_id(youtube_link)
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(
                    f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                    caption="Video Thumbnail",
                    use_column_width=True
                )
        except:
            pass
    
    # Extract transcript
    if extract_button:
        if not youtube_link:
            st.error("⚠️ Please enter a YouTube video link")
            return
        
        if not ytt_api:
            st.error("❌ API not initialized properly")
            return
        
        try:
            # Extract video ID
            video_id = extract_video_id(youtube_link)
            
            with st.spinner("🔍 Extracting transcript (trying English first, then any available language)..."):
                # Get any available transcript
                result = get_any_available_transcript(video_id)
                
                if result['success']:
                    # Show success message with language info
                    language_info = f"{result['language_name']} ({result['language_code']})"
                    transcript_type = "Auto-generated" if result.get('is_generated') else "Manual"
                    
                    if result['is_english']:
                        st.success(f"✅ English transcript found! Language: {language_info} | Type: {transcript_type}")
                    else:
                        st.success(f"✅ Transcript extracted! Language: {language_info} | Type: {transcript_type}")
                        st.info(f"ℹ️ English not available, showing {result['language_name']} transcript instead")
                    
                    # Show statistics
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("📝 Word Count", f"{result['word_count']:,}")
                    col2.metric("⏱️ Duration", format_timestamp(result['duration']))
                    col3.metric("📄 Lines", result['line_count'])
                    col4.metric("🌍 Language", f"{result['language_code'].upper()}")
                    
                    st.divider()
                    
                    # Show transcript in tabs
                    tab1, tab2, tab3 = st.tabs(["📋 Formatted Transcript", "📄 Plain Text", "💾 Download"])
                    
                    with tab1:
                        st.text_area(
                            f"Formatted Transcript ({result['language_name']}) with Timestamps:",
                            result['formatted_transcript'],
                            height=400,
                            help="Copy this text or use the download button below"
                        )
                    
                    with tab2:
                        st.text_area(
                            f"Plain Text ({result['language_name']}) - No Timestamps:",
                            result['full_text'],
                            height=400,
                            help="Clean text without timestamps - good for analysis"
                        )
                    
                    with tab3:
                        # Create safe filename
                        safe_lang = result['language_code'].replace('-', '_')
                        
                        col1, col2 = st.columns(2)
                        col1.download_button(
                            label="📥 Download with Timestamps",
                            data=result['formatted_transcript'],
                            file_name=f"transcript_{video_id}_{safe_lang}_formatted.txt",
                            mime="text/plain",
                            help="Download transcript with timestamps"
                        )
                        col2.download_button(
                            label="📥 Download Plain Text",
                            data=result['full_text'],
                            file_name=f"transcript_{video_id}_{safe_lang}_plain.txt",
                            mime="text/plain",
                            help="Download clean text without timestamps"
                        )
                        
                        # Additional info
                        if result['is_english']:
                            st.success(f"💡 **Perfect!** Found English transcript ({result['language_code']})")
                        else:
                            st.info(f"💡 **Note:** This is a {result['language_name']} transcript. English was not available.")
                            st.markdown("**You can use translation tools like Google Translate to convert this to English.**")
                
                else:
                    st.error(f"❌ {result['error']}")
                    
                    # Show helpful suggestions
                    st.markdown("""
                    **Possible solutions:**
                    - Check if the video has any captions/subtitles enabled
                    - Try a different YouTube video
                    - Make sure the video is publicly accessible
                    - Wait a few minutes and try again if rate limited
                    - Verify your proxy credentials are correct
                    """)
        
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        <p>📺 YouTube Transcript Extractor | Built with Streamlit</p>
        <p>⚠️ Works with any video that has captions/subtitles enabled</p>
        <p>🔄 Priority: English first, then any available language</p>
        <p>🌍 Supports all languages available on YouTube</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
