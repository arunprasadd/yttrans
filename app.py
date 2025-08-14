import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
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
        
        # Get transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
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
            'duration': transcript_list[-1]['start'] + transcript_list[-1]['duration'] if transcript_list else 0
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
            with st.spinner("🔄 Extracting transcript..."):
                # Extract transcript
                transcript_data = extract_transcript_details(youtube_link)
                
                if transcript_data:
                    # Success message
                    st.success("✅ Transcript extracted successfully!")
                    
                    # Display statistics
                    word_count = len(transcript_data['full_text'].split())
                    duration_formatted = format_timestamp(transcript_data['duration'])
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📝 Word Count", f"{word_count:,}")
                    with col2:
                        st.metric("⏱️ Duration", duration_formatted)
                    with col3:
                        st.metric("📄 Lines", len(transcript_data['formatted_transcript'].split('\n')))
                    
                    st.divider()
                    
                    # Tabs for different views
                    tab1, tab2, tab3 = st.tabs(["📋 Formatted Transcript", "📄 Plain Text", "💾 Download"])
                    
                    with tab1:
                        st.subheader("Transcript with Timestamps")
                        st.text_area(
                            "Formatted Transcript:",
                            transcript_data['formatted_transcript'],
                            height=400,
                            help="Transcript with timestamps in [MM:SS] format"
                        )
                    
                    with tab2:
                        st.subheader("Plain Text Version")
                        st.text_area(
                            "Plain Text:",
                            transcript_data['full_text'],
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
                                data=transcript_data['formatted_transcript'],
                                file_name=f"transcript_{transcript_data['video_id']}_formatted.txt",
                                mime="text/plain",
                                help="Download transcript with timestamps"
                            )
                        
                        with col2:
                            # Download plain text
                            st.download_button(
                                label="📥 Download Plain Text",
                                data=transcript_data['full_text'],
                                file_name=f"transcript_{transcript_data['video_id']}_plain.txt",
                                mime="text/plain",
                                help="Download transcript without timestamps"
                            )
                else:
                    st.error("❌ Could not extract transcript from this video")
                    
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            
            # Provide helpful error messages
            error_msg = str(e).lower()
            if "transcript" in error_msg or "caption" in error_msg:
                st.info("💡 **Possible reasons:**\n"
                       "- Video doesn't have captions/subtitles\n"
                       "- Captions are disabled by the video owner\n"
                       "- Video is private or restricted")
            elif "video" in error_msg:
                st.info("💡 **Please check:**\n"
                       "- URL is correct and accessible\n"
                       "- Video exists and is not deleted\n"
                       "- Video is not private")
    
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