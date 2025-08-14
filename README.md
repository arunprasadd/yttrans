# YouTube Transcript Extractor

A Streamlit web application that extracts transcripts from YouTube videos with available captions/subtitles.

## Features

- 📺 Extract transcripts from any YouTube video
- ⏱️ Display transcripts with timestamps
- 📄 View plain text version without timestamps
- 🖼️ Video thumbnail preview
- 💾 Download transcripts in multiple formats
- 📊 Display transcript statistics (word count, duration)

## Setup

### Prerequisites

- Python 3.8 or higher

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

3. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Open the application in your browser (usually `http://localhost:8501`)
2. Paste a YouTube video URL in the input field
3. Click "Extract Transcript" to get the transcript
4. View the transcript with timestamps or as plain text
5. Download the transcript in your preferred format

## How it Works

1. **URL Processing**: Supports multiple YouTube URL formats
2. **Transcript Extraction**: Uses `youtube-transcript-api` to extract captions/subtitles
3. **Formatting**: Displays transcripts with timestamps and provides plain text version
4. **Download**: Allows downloading in multiple formats

## Requirements

- The YouTube video must have captions/subtitles available (auto-generated or manual)

## Limitations

- Only works with videos that have available transcripts
- Requires internet connection for transcript extraction
- Cannot extract transcripts from private or restricted videos

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the [MIT License](LICENSE).