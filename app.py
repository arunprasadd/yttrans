import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable, NoTranscriptFound
import re


def get_youtube_api_instance():
    """Get YouTube API instance with optional proxy configuration"""
    # Hardcoded proxy credentials - replace with your actual credentials
    proxy_username = "labvizce"  # Replace with your actual username
    proxy_password = "x2za3x15c9ah"  # Replace with your actual password
    
    try:
        # Try to import proxy support
        from youtube_transcript_api._api import YouTubeTranscriptApi
        
        if proxy_username and proxy_password:
            try:
                # For version 1.2.2, use proxies parameter in get_transcript
                return YouTubeTranscriptApi
            except Exception as e:
                st.warning(f"⚠️ Proxy configuration failed: {str(e)}. Using direct connection.")
                # Fallback to direct connection
                return YouTubeTranscriptApi
    except ImportError:
        st.info("ℹ️ Proxy support not available in this version. Using direct connection.")
    
    # Fallback to direct connection


def extract_transcript_details(youtube_video_url):
    """Extract transcript from YouTube video URL"""
    try:
        # Extract video ID from different YouTube URL formats
        video_id = None

        if "youtube.com/watch?v=" in youtube_video_url:
            video_id = youtube_video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in youtube_video_url:
            video_id = youtube_video_url.split("youtu.be/")[1].split("?")[0]
        elif "youtube.com/embed/" in youtube_video_url:
            video_id = youtube_video_url.split("embed/")[1].split("?")[0]

        if not video_id:
            raise ValueError("Could not extract video ID from URL")

        # Use list_transcripts method to get available transcripts
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            available_transcripts = []

            # Extract available transcripts from transcript list
            for transcript in transcript_list:
                transcript_info = {
                    'language': transcript.language,
                    'language_code': transcript.language_code,
                    'is_generated': transcript.is_generated,
                    'is_translatable': transcript.is_translatable
                }
                available_transcripts.append(transcript_info)

            return {
                'video_id': video_id,
                'available_transcripts': available_transcripts,
                'transcript_list': transcript_list
            }

        except TranscriptsDisabled:
            raise Exception("❌ Transcripts appear to be disabled for this video, even though captions may be visible on YouTube. This can happen due to:\n\n• Regional restrictions on transcript access\n• API limitations for certain video types\n• Temporary YouTube API issues\n• Video creator has disabled API access to transcripts\n\nTry:\n• A different video with confirmed captions\n• Refreshing and trying again later\n• Using a VPN if you're in a restricted region\n• Testing with TED Talks or educational videos which typically work")
        except VideoUnavailable:
            raise Exception("❌ Video is unavailable. This could be because the video is private, deleted, age-restricted, or region-blocked. Please check the video URL and try again.")
        except NoTranscriptFound:
            raise Exception("❌ No transcripts found for this video, even though captions may be visible on YouTube. This can happen when:\n\n• Captions are embedded/burned into the video\n• Captions are only available in languages not supported by the API\n• The video uses a caption format not accessible via API\n• Regional restrictions prevent API access\n\nTry a different video with standard YouTube captions.")
        except Exception as e:
            raise Exception(f"❌ Error accessing video: {str(e)}. Please check if the video URL is correct and the video is publicly accessible.")

    except Exception as e:
        raise e


def get_transcript_by_language(video_id, language_code):
    """Get transcript for specific language"""
    try:
        # Get transcript list first
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Find the specific transcript by language code
        selected_transcript = None
        for transcript in transcript_list:
            if transcript.language_code == language_code:
                selected_transcript = transcript
                break
        
        if not selected_transcript:
            raise Exception(f"Transcript for language '{language_code}' not found")
        
        # Get the actual transcript data
        transcript_data = selected_transcript.fetch()

        formatted_transcript = ""
        full_text = ""

        for entry in transcript_data:
            timestamp = format_timestamp(entry['start'])
            text = entry['text']
            formatted_transcript += f"[{timestamp}] {text}\n"
            full_text += f" {text}"

        return {
            'video_id': video_id,
            'formatted_transcript': formatted_transcript,
            'full_text': full_text.strip(),
            'duration': transcript_data[-1]['start'] + transcript_data[-1]['duration'] if transcript_data else 0,
            'language_code': language_code
        }

    except Exception as e:
        raise e


def format_timestamp(seconds):
    """Convert seconds to MM:SS or HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def get_video_info(video_id):
    """Get basic video information"""
    try:
        return {
            'thumbnail_url': f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            'video_url': f"https://www.youtube.com/watch?v={video_id}"
        }
    except:
        return None


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
        2. **Click Extract** to get the transcript
        3. **View transcript** with timestamps
        4. **Download** transcript as text file
        
        **Supported URL formats:**
        - `youtube.com/watch?v=VIDEO_ID`
        - `youtu.be/VIDEO_ID`
        - `youtube.com/embed/VIDEO_ID`
        
        **Requirements:**
        - Video must have captions/subtitles enabled
        - Video must be publicly accessible
        - Video cannot have transcripts disabled by creator
        
        **Try these test videos:**
        - TED Talks (usually have captions)
        - Educational channels
        - News videos
        - Popular YouTube channels
        """)
        
        # Proxy configuration section
        st.divider()
        st.header("🌐 Proxy Settings (Optional)")
        st.markdown("Use proxy if you're experiencing regional restrictions:")
        
        with st.expander("Configure Proxy"):
            proxy_username = st.text_input(
                "Proxy Username:",
                value=st.session_state.get('proxy_username', ''),
                help="Enter your Webshare or other proxy username"
            )
            proxy_password = st.text_input(
                "Proxy Password:",
                type="password",
                value=st.session_state.get('proxy_password', ''),
                help="Enter your proxy password"
            )
            
            if st.button("💾 Save Proxy Settings"):
                st.session_state['proxy_username'] = proxy_username
                st.session_state['proxy_password'] = proxy_password
                if proxy_username and proxy_password:
                    st.success("✅ Proxy settings saved!")
                else:
                    st.info("ℹ️ Proxy settings cleared - using direct connection")
            
            if st.button("🗑️ Clear Proxy Settings"):
                st.session_state['proxy_username'] = ''
                st.session_state['proxy_password'] = ''
                st.success("✅ Proxy settings cleared!")
            
            # Show current proxy status
            if st.session_state.get('proxy_username'):
                st.info(f"🌐 Using proxy: {st.session_state.get('proxy_username')}")
            else:
                st.info("🔗 Using direct connection")

    col1, col2 = st.columns([2, 1])

    with col1:
        youtube_link = st.text_input(
            "Enter YouTube Video Link:",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste any YouTube video URL here"
        )

    with col2:
        extract_button = st.button("🔍 Extract Transcript", type="primary", use_container_width=True)

    if youtube_link:
        try:
            if any(domain in youtube_link for domain in ['youtube.com', 'youtu.be']):
                video_id = None
                if "youtube.com/watch?v=" in youtube_link:
                    video_id = youtube_link.split("v=")[1].split("&")[0]
                elif "youtu.be/" in youtube_link:
                    video_id = youtube_link.split("youtu.be/")[1].split("?")[0]

                if video_id:
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.image(
                            f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                            caption="Video Thumbnail",
                            use_column_width=True
                        )
        except:
            pass

    if extract_button:
        if not youtube_link:
            st.error("⚠️ Please enter a YouTube video link")
            return

        try:
            with st.spinner("🔍 Checking available transcripts..."):
                transcript_data = extract_transcript_details(youtube_link)

                if transcript_data and transcript_data.get('available_transcripts'):
                    available_transcripts = transcript_data['available_transcripts']

                    st.success(f"✅ Found {len(available_transcripts)} available transcript(s)!")

                    st.subheader("📋 Available Transcripts")
                    transcript_options = []
                    for transcript in available_transcripts:
                        generated_text = " (Auto-generated)" if transcript['is_generated'] else " (Manual)"
                        translatable_text = " - Can be translated" if transcript['is_translatable'] else ""
                        option_text = f"{transcript['language']} ({transcript['language_code']}){generated_text}{translatable_text}"
                        transcript_options.append(option_text)

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        selected_transcript = st.selectbox(
                            "Select a transcript to extract:",
                            options=range(len(transcript_options)),
                            format_func=lambda x: transcript_options[x]
                        )
                    with col2:
                        extract_selected = st.button("📥 Extract Selected", type="primary")

                    with st.expander("📊 Transcript Details", expanded=True):
                        for transcript in available_transcripts:
                            icon = "🤖" if transcript['is_generated'] else "👤"
                            translate_icon = "🌐" if transcript['is_translatable'] else "🚫"
                            st.write(f"{icon} **{transcript['language']}** ({transcript['language_code']})")
                            st.write(f"   • Type: {'Auto-generated' if transcript['is_generated'] else 'Manual'}")
                            st.write(f"   • Translatable: {translate_icon} {'Yes' if transcript['is_translatable'] else 'No'}")
                            st.divider()

                    if extract_selected:
                        selected_lang_code = available_transcripts[selected_transcript]['language_code']
                        selected_lang_name = available_transcripts[selected_transcript]['language']

                        with st.spinner(f"🔄 Extracting {selected_lang_name} transcript..."):
                            try:
                                final_transcript = get_transcript_by_language(
                                    transcript_details['video_id'],
                                    selected_lang_code
                                )

                                if final_transcript:
                                    st.success(f"✅ {selected_lang_name} transcript extracted successfully!")

                                    word_count = len(final_transcript['full_text'].split())
                                    duration_formatted = format_timestamp(final_transcript['duration'])

                                    col1, col2, col3, col4 = st.columns(4)
                                    col1.metric("📝 Word Count", f"{word_count:,}")
                                    col2.metric("⏱️ Duration", duration_formatted)
                                    col3.metric("📄 Lines", len(final_transcript['formatted_transcript'].split('\n')))
                                    col4.metric("🌍 Language", selected_lang_name)

                                    st.divider()
                                    tab1, tab2, tab3 = st.tabs(["📋 Formatted Transcript", "📄 Plain Text", "💾 Download"])

                                    with tab1:
                                        st.text_area(
                                            "Formatted Transcript:",
                                            final_transcript['formatted_transcript'],
                                            height=400
                                        )

                                    with tab2:
                                        st.text_area(
                                            "Plain Text:",
                                            final_transcript['full_text'],
                                            height=400
                                        )

                                    with tab3:
                                        col1, col2 = st.columns(2)
                                        col1.download_button(
                                            label="📥 Download with Timestamps",
                                            data=final_transcript['formatted_transcript'],
                                            file_name=f"transcript_{final_transcript['video_id']}_{selected_lang_code}_formatted.txt",
                                            mime="text/plain"
                                        )
                                        col2.download_button(
                                            label="📥 Download Plain Text",
                                            data=final_transcript['full_text'],
                                            file_name=f"transcript_{final_transcript['video_id']}_{selected_lang_code}_plain.txt",
                                            mime="text/plain"
                                        )
                                else:
                                    st.error("❌ Could not extract the selected transcript")
                            except Exception as e:
                                st.error(f"❌ Error extracting transcript: {str(e)}")
                else:
                    st.error("❌ No transcripts available for this video")

        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        <p>YouTube Transcript Extractor | Built with Streamlit</p>
        <p>⚠️ Only works with videos that have available captions/subtitles</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()