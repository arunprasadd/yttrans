import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

# Load environment variables
load_dotenv()

# Configure Google Gemini AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Prompt template for summarization
SUMMARY_PROMPT = """You are a YouTube video summarizer. You will be taking the transcript text
and summarizing the entire video and providing the important summary in points
within 250 words. Please provide the summary of the text given here: """

def extract_transcript_details(youtube_video_url):
    """Extract transcript from YouTube video URL"""
    try:
        video_id = youtube_video_url.split("=")[1]
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)
        
        transcript = ""
        for i in transcript_text:
            transcript += " " + i["text"]
        
        return transcript
    except Exception as e:
        raise e

def generate_gemini_content(transcript_text, prompt):
    """Generate summary using Google Gemini Pro"""
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt + transcript_text)
    return response.text

def main():
    st.set_page_config(
        page_title="YouTube Transcript Summarizer",
        page_icon="📺",
        layout="wide"
    )
    
    st.title("📺 YouTube Transcript to Summary")
    st.markdown("Convert any YouTube video into detailed notes using AI")
    
    # Input for YouTube URL
    youtube_link = st.text_input(
        "Enter YouTube Video Link:",
        placeholder="https://www.youtube.com/watch?v=..."
    )
    
    if youtube_link:
        try:
            video_id = youtube_link.split("=")[1]
            st.image(
                f"http://img.youtube.com/vi/{video_id}/0.jpg", 
                use_column_width=True,
                caption="Video Thumbnail"
            )
        except:
            st.error("Please enter a valid YouTube URL")
    
    if st.button("🔍 Get Detailed Notes", type="primary"):
        if not youtube_link:
            st.error("Please enter a YouTube video link")
            return
            
        if not os.getenv("GOOGLE_API_KEY"):
            st.error("Please set your GOOGLE_API_KEY in the .env file")
            return
        
        try:
            with st.spinner("Extracting transcript and generating summary..."):
                # Extract transcript
                transcript_text = extract_transcript_details(youtube_link)
                
                if transcript_text:
                    # Generate summary
                    summary = generate_gemini_content(transcript_text, SUMMARY_PROMPT)
                    
                    # Display results
                    st.markdown("## 📝 Detailed Notes:")
                    st.write(summary)
                    
                    # Show transcript in expander
                    with st.expander("📄 View Full Transcript"):
                        st.text_area("Transcript", transcript_text, height=300)
                else:
                    st.error("Could not extract transcript from this video")
                    
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.info("Make sure the video has captions/subtitles available")

if __name__ == "__main__":
    main()