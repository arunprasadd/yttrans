import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable, NoTranscriptFound
import re

def extract_transcript_details(youtube_video_url):
    """Extract transcript from YouTube video URL"""
    try:
        # Extract video ID from different YouTube URL formats
        video_id = None
        
        # Handle different YouTube URL formats
        if "youtube.com/watch?v=" in youtube_video_url:
            video_id = youtube_video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in youtube_video_url:
            video_id = youtube_video_url.split("youtu.be/")[1].split("?")[0]
        elif "youtube.com/embed/" in youtube_video_url:
            video_id = youtube_video_url.split("embed/")[1].split("?")[0]
        
        if not video_id:
            raise ValueError("Could not extract video ID from URL")
        
        # Get list of available transcripts first
        try:
            transcript_list_info = YouTubeTranscriptApi.list_transcripts(video_id)
            available_transcripts = []
            
            for transcript in transcript_list_info:
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
                'transcript_data': None
            }

        except TranscriptsDisabled:
            raise Exception("Transcripts are disabled for this video")
        except VideoUnavailable:
            raise Exception("Video is unavailable (may be private, deleted, or region-blocked)")
        except NoTranscriptFound:
            raise Exception("No transcripts found for this video")
        except Exception as e:
            raise Exception(f"Error accessing video: {str(e)}")

def get_transcript_by_language(video_id, language_code):
    """Get transcript for specific language"""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[language_code])
        
        # Format transcript with timestamps
        formatted_transcript = ""
        full_text = ""
        
        for entry in transcript_list:
            timestamp = format_timestamp(entry['start'])
            text = entry['text']
            formatted_transcript += f"[{timestamp}] {text}\n"
            full_text += f" {text}"
        
        return {
            'video_id': video_id,
            'formatted_transcript': formatted_transcript,
            'full_text': full_text.strip(),
            'duration': transcript_list[-1]['start'] + transcript_list[-1]['duration'] if transcript_list else 0,
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
        # This is a simple way to get video title from the thumbnail API
        # In a more complete implementation, you might use YouTube Data API
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
    
    # Sidebar with instructions
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
        
        **Note:** Only works with videos that have captions/subtitles available.
        """)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Input for YouTube URL
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
            # Quick validation and thumbnail display
            if any(domain in youtube_link for domain in ['youtube.com', 'youtu.be']):
                # Extract video ID for thumbnail
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
    
    # Extract transcript when button is clicked
    if extract_button:
        if not youtube_link:
            st.error("⚠️ Please enter a YouTube video link")
            return
        
        try:
            with st.spinner("🔍 Checking available transcripts..."):
                # Check available transcripts first
                transcript_data = extract_transcript_details(youtube_link)
                
                if transcript_data and transcript_data.get('available_transcripts'):
                    available_transcripts = transcript_data['available_transcripts']
                    
                    # Display available transcripts
                    st.success(f"✅ Found {len(available_transcripts)} available transcript(s)!")
                    
                    # Show transcript options
                    st.subheader("📋 Available Transcripts")
                    
                    transcript_options = []
                    for i, transcript in enumerate(available_transcripts):
                        generated_text = " (Auto-generated)" if transcript['is_generated'] else " (Manual)"
                        translatable_text = " - Can be translated" if transcript['is_translatable'] else ""
                        option_text = f"{transcript['language']} ({transcript['language_code']}){generated_text}{translatable_text}"
                        transcript_options.append(option_text)
                    
                    # Create columns for transcript info
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        selected_transcript = st.selectbox(
                            "Select a transcript to extract:",
                            options=range(len(transcript_options)),
                            format_func=lambda x: transcript_options[x],
                            help="Choose which transcript language/type to extract"
                        )
                    
                    with col2:
                        extract_selected = st.button("📥 Extract Selected", type="primary")
                    
                    # Show transcript details in expandable sections
                    with st.expander("📊 Transcript Details", expanded=True):
                        for i, transcript in enumerate(available_transcripts):
                            icon = "🤖" if transcript['is_generated'] else "👤"
                            translate_icon = "🌐" if transcript['is_translatable'] else "🚫"
                            
                            st.write(f"{icon} **{transcript['language']}** ({transcript['language_code']})")
                            st.write(f"   • Type: {'Auto-generated' if transcript['is_generated'] else 'Manual/Human-created'}")
                            st.write(f"   • Translatable: {translate_icon} {'Yes' if transcript['is_translatable'] else 'No'}")
                            if i < len(available_transcripts) - 1:
                                st.divider()
                    
                    # Extract selected transcript
                    if extract_selected:
                        selected_lang_code = available_transcripts[selected_transcript]['language_code']
                        selected_lang_name = available_transcripts[selected_transcript]['language']
                        
                        with st.spinner(f"🔄 Extracting {selected_lang_name} transcript..."):
                            try:
                                final_transcript = get_transcript_by_language(
                                    transcript_data['video_id'], 
                                    selected_lang_code
                                )
                                
                                if final_transcript:
                                    # Success message
                                    st.success(f"✅ {selected_lang_name} transcript extracted successfully!")
                                    
                                    # Display statistics
                                    word_count = len(final_transcript['full_text'].split())
                                    duration_formatted = format_timestamp(final_transcript['duration'])
                                    
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        st.metric("📝 Word Count", f"{word_count:,}")
                                    with col2:
                                        st.metric("⏱️ Duration", duration_formatted)
                                    with col3:
                                        st.metric("📄 Lines", len(final_transcript['formatted_transcript'].split('\n')))
                                    with col4:
                                        st.metric("🌍 Language", selected_lang_name)
                                    
                                    st.divider()
                                    
                                    # Tabs for different views
                                    tab1, tab2, tab3 = st.tabs(["📋 Formatted Transcript", "📄 Plain Text", "💾 Download"])
                                    
                                    with tab1:
                                        st.subheader(f"Transcript with Timestamps ({selected_lang_name})")
                                        st.text_area(
                                            "Formatted Transcript:",
                                            final_transcript['formatted_transcript'],
                                            height=400,
                                            help="Transcript with timestamps in [MM:SS] format"
                                        )
                                    
                                    with tab2:
                                        st.subheader(f"Plain Text Version ({selected_lang_name})")
                                        st.text_area(
                                            "Plain Text:",
                                            final_transcript['full_text'],
                                            height=400,
                                            help="Transcript without timestamps"
                                        )
                                    
                                    with tab3:
                                        st.subheader("Download Options")
                                        
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            # Download formatted transcript
                                            st.download_button(
                                                label="📥 Download with Timestamps",
                                                data=final_transcript['formatted_transcript'],
                                                file_name=f"transcript_{final_transcript['video_id']}_{selected_lang_code}_formatted.txt",
                                                mime="text/plain",
                                                help="Download transcript with timestamps"
                                            )
                                        
                                        with col2:
                                            # Download plain text
                                            st.download_button(
                                                label="📥 Download Plain Text",
                                                data=final_transcript['full_text'],
                                                file_name=f"transcript_{final_transcript['video_id']}_{selected_lang_code}_plain.txt",
                                                mime="text/plain",
                                                help="Download transcript without timestamps"
                                            )
                                else:
                                    st.error("❌ Could not extract the selected transcript")
                            except Exception as e:
                                st.error(f"❌ Error extracting transcript: {str(e)}")
                else:
                    st.error("❌ No transcripts available for this video")
                    
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            
            # Provide more detailed error information
            error_msg = str(e).lower()
            
            if "transcripts are disabled" in error_msg:
                st.info("💡 **This video has transcripts disabled by the owner**\n"
                       "- The video creator has chosen to disable captions/subtitles\n"
                       "- This is a setting controlled by the video owner\n"
                       "- Try a different video that has captions enabled")
            elif "video is unavailable" in error_msg:
                st.info("💡 **Video access issues:**\n"
                       "- Video might be private, unlisted, or deleted\n"
                       "- Could be region-blocked (IP blocking)\n"
                       "- Video might be age-restricted\n"
                       "- Check if you can access the video directly in YouTube")
            elif "no transcripts found" in error_msg:
                st.info("💡 **No transcripts available:**\n"
                       "- Video doesn't have any captions or subtitles\n"
                       "- Auto-generated captions might not be available\n"
                       "- Try videos from educational channels or news outlets")
            elif "transcript" in error_msg or "caption" in error_msg:
                st.info("💡 **Possible reasons:**\n"
                       "- Video doesn't have captions/subtitles\n"
                       "- Captions are disabled by the video owner\n"
                       "- Video is private or restricted")
            elif "video" in error_msg:
                st.info("💡 **Please check:**\n"
                       "- URL is correct and accessible\n"
                       "- Video exists and is not deleted\n"
                       "- Video is not private or region-blocked")
            else:
                st.info("💡 **General troubleshooting:**\n"
                       "- Try a different video with known captions\n"
                       "- Check your internet connection\n"
                       "- Verify the YouTube URL is correct")
                
            # Add debugging info
            with st.expander("🔧 Technical Details", expanded=False):
                st.code(f"Error: {str(e)}")
                st.write("**Suggested test videos with transcripts:**")
                st.write("- TED Talks: https://www.youtube.com/watch?v=UF8uR6Z6KLc")
                st.write("- Educational content from Khan Academy, Coursera, etc.")
                st.write("- News videos from BBC, CNN, etc.")
    
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