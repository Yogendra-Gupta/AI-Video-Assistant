# AI Video Assistant

> An end-to-end AI meeting intelligence platform that converts video/audio into searchable transcripts and structured insights, then uses semantic retrieval and RAG to provide context-grounded conversational answers.

## Overview

**AI Video Assistant** processes YouTube videos or local audio/video files and transforms them into useful meeting intelligence:

- Speech-to-text transcription
- Professional meeting title generation
- Meeting summarization
- Action-item extraction
- Key-decision extraction
- Unresolved-question detection
- Semantic transcript search
- Context-grounded conversational Q&A

The application combines media processing, speech recognition, LLM orchestration, embeddings, vector search, and Retrieval-Augmented Generation (RAG) in a single Python application.

## How It Works

```text
YouTube URL / Local Audio-Video
              |
              v
     Audio Acquisition
   yt-dlp / FFmpeg / pydub
              |
              v
       Audio Normalization
        Mono 16 kHz WAV
              |
              v
        Audio Chunking
       ~10-minute chunks
              |
              v
        Speech-to-Text
     Whisper / Sarvam AI
              |
              v
           Transcript
              |
       +------+------+------+
       |      |      |      |
       v      v      v      v
     Title  Summary Actions Decisions/
                              Questions
              |
              v
       Transcript Chunking
              |
              v
          Embeddings
     all-MiniLM-L6-v2
              |
              v
           ChromaDB
              |
              v
        User Question
              |
              v
     Semantic Retrieval
        Top 4 chunks
              |
              v
      Context + Question
              |
              v
          Mistral LLM
              |
              v
       Grounded Answer
```

## Key Features

### Multi-Source Video/Audio Input
Accepts YouTube URLs through `yt-dlp` and local audio/video files. Media is normalized to **mono, 16 kHz WAV** before transcription.

### Speech Recognition
- **OpenAI Whisper** for English transcription
- **Sarvam AI** for Hinglish-oriented processing
- Long audio is divided into smaller chunks for practical processing and API constraints.

### Meeting Intelligence
Uses Mistral through LangChain to generate:
- Meeting title
- Concise summary
- Action items
- Owners/deadlines where available
- Key decisions
- Unresolved questions

### Semantic Search + RAG
The transcript is converted into embeddings using `all-MiniLM-L6-v2` and persisted in **ChromaDB**. For each question, the system retrieves the top 4 relevant transcript chunks and passes the retrieved context with the question to Mistral for a grounded answer.

### Conversational UI
The Streamlit interface provides processing status, transcript, summary, action items, decisions, open questions, conversational Q&A, and session chat history. A CLI workflow is also provided.

## Technology Stack

| Area | Technology |
|---|---|
| Language | Python |
| UI | Streamlit |
| LLM | Mistral AI (`mistral-small-latest`) |
| LLM Orchestration | LangChain / LCEL |
| English STT | OpenAI Whisper |
| Hinglish STT | Sarvam AI |
| Media Download | yt-dlp |
| Media Processing | FFmpeg, pydub |
| Embeddings | Hugging Face `all-MiniLM-L6-v2` |
| Vector Database | ChromaDB |
| Configuration | python-dotenv / Environment Variables |

## Project Structure

```text
AI-Video-Assistant/
│
├── app.py                    # Streamlit application
├── main.py                   # CLI workflow
├── test.py                   # Pipeline/demo test
├── Requirements.txt          # Python dependencies
|
│
├── core/
│   ├── extractor.py          # Action items, decisions, questions
│   ├── rag_engine.py         # Semantic retrieval + RAG Q&A
│   ├── summarizer.py         # Title and transcript summarization
│   ├── transcriber.py        # Whisper / Sarvam transcription
│   └── vector_store.py       # Embeddings + ChromaDB
│
└── utils/
    └── audio_processor.py    # Download, conversion and chunking
```

## Getting Started

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd AI-Video-Assistant
```

### 2. Create a Virtual Environment

**Windows**

```bash
python -m venv .venv
.venv\\Scripts\\activate
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r Requirements.txt
```

### 4. Install FFmpeg

FFmpeg is required for audio/video conversion and processing.

```bash
ffmpeg -version
```

### 5. Configure API Keys

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
MISTRAL_API_KEY=your_mistral_api_key
SARVAM_API_KEY=your_sarvam_api_key
```

Use only the keys required by the selected processing path. **Never commit `.env` or API keys to GitHub.**

### 6. Run the Streamlit Application

```bash
streamlit run app.py
```

Then provide a YouTube URL or local media input and select the desired language processing path.

### CLI

```bash
python main.py
```

## Why RAG?

Long transcripts can be too large and inefficient to send to an LLM for every question. Instead:

```text
User Question
      ↓
Embedding / Similarity Search
      ↓
Top 4 Transcript Chunks
      ↓
Relevant Context + Question
      ↓
Mistral LLM
      ↓
Grounded Answer
```

This reduces unnecessary context, improves retrieval relevance, and provides a foundation for transcript-grounded conversational QA.

## Engineering Decisions

- **Mono 16 kHz audio** provides a consistent transcription input format.
- **Audio chunking** makes long recordings easier to process.
- **Short Sarvam segments** accommodate synchronous API duration constraints.
- **Map-and-combine summarization** handles transcripts too large for one LLM call.
- **Smaller RAG chunks** improve retrieval granularity.
- **Top-k retrieval** limits the evidence sent to the LLM.
- **Environment variables** keep credentials outside source code.
- **ChromaDB persistence** provides a practical local vector-store implementation.

## Current Limitations

This implementation is a **portfolio/prototype project**, not a production-grade multi-user platform.

- No robust speaker diarization.
- Transcript chunks do not maintain a complete speaker/timestamp model for precise video navigation.
- ChromaDB setup would need meeting-level isolation for multi-user deployments.
- No authentication or authorization layer.
- `test.py` is primarily a pipeline/demo test rather than a comprehensive automated test suite.
- Processing is largely synchronous/local.
- Temporary downloaded and chunked media would benefit from explicit lifecycle cleanup.

## Future Improvements

- Speaker diarization and timestamp-aware transcripts
- Meeting-level metadata and user isolation
- FastAPI backend
- Background workers and job queues
- Object storage for uploaded media
- PostgreSQL for metadata
- Scalable/managed vector database
- Hybrid keyword + vector retrieval
- Retrieval reranking
- Citation-aware answers
- Retrieval and factuality evaluation
- Authentication and authorization
- Retry handling, rate limiting, and monitoring
- Docker-based deployment
- Comprehensive automated testing

## Example Use Cases

- Meeting summarization
- Interview/video analysis
- Lecture and webinar analysis
- Long-form video Q&A
- Knowledge extraction from recorded discussions
- Searchable meeting archives
- Action-item and decision tracking

## Project Highlights

This project demonstrates an end-to-end GenAI pipeline rather than a simple LLM wrapper:

**Media Processing → Speech Recognition → NLP → LLM Orchestration → Embeddings → Vector Search → RAG → Conversational UI**

The main technical focus is the integration of speech processing and RAG to turn unstructured video/audio content into searchable and conversational knowledge.
