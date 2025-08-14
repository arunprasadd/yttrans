# YouTube Transcript Summarizer

A Streamlit web application that extracts transcripts from YouTube videos and generates AI-powered summaries using Google's Gemini Pro model.

## Features

- 📺 Extract transcripts from any YouTube video
- 🤖 AI-powered summarization using Google Gemini Pro
- 📝 Generate concise bullet-point summaries (under 250 words)
- 🖼️ Video thumbnail preview
- 📄 View full transcript alongside summary

## Setup

### Prerequisites

- Python 3.8 or higher
- Google AI API key

### Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd youtube-transcriber
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

4. Get your Google AI API key:
   - Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the key and paste it in the `.env` file

5. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Open the application in your browser (usually `http://localhost:8501`)
2. Paste a YouTube video URL in the input field
3. Click "Get Detailed Notes" to generate the summary
4. View the AI-generated summary and optionally expand to see the full transcript

## How it Works

1. **Transcript Extraction**: Uses `youtube-transcript-api` to extract captions/subtitles from YouTube videos
2. **AI Summarization**: Sends the transcript to Google's Gemini Pro model with a specialized prompt
3. **Summary Generation**: Returns a concise, bullet-pointed summary of the video content

## Requirements

- The YouTube video must have captions/subtitles available (auto-generated or manual)
- Valid Google AI API key with Gemini Pro access

## Limitations

- Only works with videos that have available transcripts
- Summary length is limited to approximately 250 words
- Requires internet connection for both transcript extraction and AI processing

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the [MIT License](LICENSE).