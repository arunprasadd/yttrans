import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable, NoTranscriptFound, NoTranscriptAvailable
import re

# Initialize YouTube Transcript API with proxy configuration
try:
    ytt_api = YouTubeTranscriptApi(
        proxy_config=WebshareProxyConfig(
            proxy_username="<proxy-username>",  # Replace with your actual proxy username
            proxy_password="<proxy-password>",  # Replace with your actual proxy password
        )
    )
    st.sidebar.success("✅ Proxy configured")
except Exception as e:
    # Fallback to default API without proxy
    ytt_api = YouTubeTranscriptApi()
    st.sidebar.warning("⚠️ Using direct connection (no proxy)")


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


def get_available_transcripts(video_id):
    """Get list of available transcripts for a video"""
    try:
        transcript_list = ytt_api.list_transcripts(video_id)
        available_transcripts = []
        
        for transcript in transcript_list:
            transcript_info = {
                'language': transcript.language,
                'language_code': transcript.language_code,
                'is_generated': transcript.is_generated,
                'is_translatable': transcript.is_translatable if hasattr(transcript, 'is_translatable') else False,
                'transcript_obj': transcript
            }
            available_transcripts.append(transcript_info)
        
        return available_transcripts
        
    except TranscriptsDisabled:
        raise Exception("❌ Transcripts are disabled for this video")
    except VideoUnavailable:
        raise Exception("❌ Video is unavailable or private")
    except (NoTranscriptFound, NoTranscriptAvailable):
        raise Exception("❌ No transcripts found for this video")
    except Exception as e:
        raise Exception(f"❌ Error accessing video: {str(e)}")


def get_transcript_data(transcript_obj):
    """Get transcript data from transcript object"""
    try:
        # Use the proxied API instance to fetch transcript data
        # transcript_obj contains the video_id and language info we need
        transcript_data = transcript_obj.fetch()
        
        formatted_transcript = ""
        full_text = ""
        
        for entry in transcript_data:
            timestamp = format_timestamp(entry['start'])
            text = entry['text']
            formatted_transcript += f"[{timestamp}] {text}\n"
            full_text += f" {text}"
        
        duration = transcript_data[-1]['start'] + transcript_data[-1]['duration'] if transcript_data else 0
        
        return {
            'formatted_transcript': formatted_transcript,
            'full_text': full_text.strip(),
            'duration': duration,
            'word_count': len(full_text.strip().split()),
            'line_count': len(formatted_transcript.split('\n'))
        }
        
    except Exception as e:
        raise Exception(f"❌ Error fetching transcript: {str(e)}")


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
        page_title="YouTube Transcript Extractor",
        page_icon="📺",
        layout="wide"
    )
    
    st.title("📺 YouTube Transcript Extractor")
    st.markdown("Extract transcripts from any YouTube video with available captions")
    
    with st.sidebar:
        st.header("📋 Instructions")
        st.markdown("""
        1. **Paste YouTube URL** in the input field
        2. **Click Extract** to get available transcripts
        3. **Select language** from available options
        4. **View transcript** with timestamps
        5. **Download** transcript as text file
        
        **Proxy Status:**
        - Using proxy to prevent IP bans
        - Replace proxy credentials in code
        
        **Supported URL formats:**
        - `youtube.com/watch?v=VIDEO_ID`
        - `youtu.be/VIDEO_ID`
        - `youtube.com/embed/VIDEO_ID`
        
        **Requirements:**
        - Video must have captions/subtitles enabled
        - Video must be publicly accessible
        """)
    
    # Main input
    col1, col2 = st.columns([3, 1])
    
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
        
        try:
            # Extract video ID
            video_id = extract_video_id(youtube_link)
            
            with st.spinner("🔍 Checking available transcripts..."):
                # Get available transcripts
                available_transcripts = get_available_transcripts(video_id)
                
                if available_transcripts:
                    st.success(f"✅ Found {len(available_transcripts)} available transcript(s)!")
                    
                    # Show available transcripts
                    st.subheader("📋 Available Transcripts")
                    
                    transcript_options = []
                    for i, transcript in enumerate(available_transcripts):
                        generated_text = " (Auto-generated)" if transcript['is_generated'] else " (Manual)"
                        translatable_text = " - Translatable" if transcript.get('is_translatable', False) else ""
                        option_text = f"{transcript['language']} ({transcript['language_code']}){generated_text}{translatable_text}"
                        transcript_options.append(option_text)
                    
                    # Language selection
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        selected_index = st.selectbox(
                            "Select a transcript to extract:",
                            options=range(len(transcript_options)),
                            format_func=lambda x: transcript_options[x]
                        )
                    with col2:
                        extract_selected = st.button("📥 Extract Selected", type="primary")
                    
                    # Show transcript details
                    with st.expander("📊 Transcript Details", expanded=True):
                        for transcript in available_transcripts:
                            icon = "🤖" if transcript['is_generated'] else "👤"
                            translate_icon = "🌐" if transcript.get('is_translatable', False) else "🚫"
                            st.write(f"{icon} **{transcript['language']}** ({transcript['language_code']})")
                            st.write(f"   • Type: {'Auto-generated' if transcript['is_generated'] else 'Manual'}")
                            st.write(f"   • Translatable: {translate_icon} {'Yes' if transcript.get('is_translatable', False) else 'No'}")
                            st.divider()
                    
                    # Extract selected transcript
                    if extract_selected:
                        selected_transcript = available_transcripts[selected_index]
                        
                        with st.spinner(f"🔄 Extracting {selected_transcript['language']} transcript..."):
                            try:
                                transcript_data = get_transcript_data(selected_transcript['transcript_obj'], video_id)
                                
                                st.success(f"✅ {selected_transcript['language']} transcript extracted successfully!")
                                
                                # Show statistics
                                col1, col2, col3, col4 = st.columns(4)
                                col1.metric("📝 Word Count", f"{transcript_data['word_count']:,}")
                                col2.metric("⏱️ Duration", format_timestamp(transcript_data['duration']))
                                col3.metric("📄 Lines", transcript_data['line_count'])
                                col4.metric("🌍 Language", selected_transcript['language'])
                                
                                st.divider()
                                
                                # Show transcript in tabs
                                tab1, tab2, tab3 = st.tabs(["📋 Formatted Transcript", "📄 Plain Text", "💾 Download"])
                                
                                with tab1:
                                    st.text_area(
                                        "Formatted Transcript:",
                                        transcript_data['formatted_transcript'],
                                        height=400
                                    )
                                
                                with tab2:
                                    st.text_area(
                                        "Plain Text:",
                                        transcript_data['full_text'],
                                        height=400
                                    )
                                
                                with tab3:
                                    col1, col2 = st.columns(2)
                                    col1.download_button(
                                        label="📥 Download with Timestamps",
                                        data=transcript_data['formatted_transcript'],
                                        file_name=f"transcript_{video_id}_{selected_transcript['language_code']}_formatted.txt",
                                        mime="text/plain"
                                    )
                                    col2.download_button(
                                        label="📥 Download Plain Text",
                                        data=transcript_data['full_text'],
                                        file_name=f"transcript_{video_id}_{selected_transcript['language_code']}_plain.txt",
                                        mime="text/plain"
                                    )
                                
                            except Exception as e:
                                st.error(f"❌ Error extracting transcript: {str(e)}")
                else:
                    st.error("❌ No transcripts available for this video")
        
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        <p>YouTube Transcript Extractor | Built with Streamlit</p>
        <p>⚠️ Only works with videos that have available captions/subtitles</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()