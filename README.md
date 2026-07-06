# College Assistant - LLM-Powered College Information Chatbot

A voice and text-based chatbot that answers questions about your college using AI and college data.

## Features

✨ **Smart Q&A**: Ask questions about placements, exams, admissions, notices, and more
🎤 **Voice Support**: Speak your questions and hear responses
📚 **College Data Integration**: Uses actual college notices and announcements
🤖 **Dual LLM Support**: Works with OpenAI API or local inference
🔍 **Smart Search**: Uses vector similarity to find relevant college information
⚡ **RAG Architecture**: Retrieval-Augmented Generation for accurate, context-aware answers

## System Architecture

```
Frontend (HTML/JS) 
    ↓
Flask Backend API
    ↓
RAG Pipeline
    ├─ Query Vectorization (Sentence Transformers)
    ├─ Vector Similarity Search (FAISS)
    ├─ Context Retrieval (College Data)
    └─ LLM Response Generation (OpenAI or Local)
```

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- ~2GB disk space for models and data
- (Optional) OpenAI API key for GPT-3.5 responses

## Installation

### 1. Install Dependencies

```bash
cd Scripts
python setup.py
```

Or manually:

```bash
cd Scripts
pip install -r requirements.txt
```

### 2. Set Up Environment (Optional - for OpenAI support)

```bash
# Windows
set OPENAI_API_KEY=your_key_here

# Linux/Mac
export OPENAI_API_KEY=your_key_here
```

## Usage

### Starting the Server

```bash
cd Scripts
python app.py
```

The server will start at: **http://localhost:5000**

### Using the Web Interface

1. Open http://localhost:5000 in your browser
2. Type your question or click the microphone to speak
3. Wait for the response
4. Chat responses will also be spoken aloud

### Example Queries

```
"When are the exams?"
"What placements are available?"
"Tell me about admissions"
"When is the next notice board update?"
"Show me recent college news"
```

## Data Files

The system uses the following data:

- **`../output/notice_dataset.json`** - Structured college notices and announcements
- **`../output/dbgi_structured.json`** - DBGI-specific information
- **`../vector_db/notice_index.faiss`** - Vector embeddings for fast search

## How It Works

### 1. Query Processing
When you ask a question, it's converted to a vector using Sentence Transformers.

### 2. Semantic Search
The vector is used to search the FAISS index for the top 5 most relevant college notices.

### 3. Context Building
Retrieved notices are formatted as context for the LLM.

### 4. Response Generation
- **With OpenAI API**: GPT-3.5-turbo generates a natural, conversational response
- **Without API**: Local keyword-based response with relevant notices

## Configuration

### Backend Settings

Edit `app.py` to customize:

```python
# Change number of retrieved notices
search_relevant_notices(message, top_k=5)  # Change 5 to different number

# Change response length
max_tokens=512  # Reduce for shorter responses

# Change similarity search
D, I = index.search(query_vector, top_k)  # Adjust search parameters
```
### LLM API Keys

- `GOOGLE_AI_STUDIO_API_KEY` or `AI_STUDIO_API_KEY` - Use Google AI Studio (free tier) for GPT-style responses.
- `OPENAI_API_KEY` - Use OpenAI GPT when Google AI Studio key is not configured.

If both are set, the app will prefer Google AI Studio first.
### Vector Database

To rebuild the vector index:

```bash
python build_notice_faiss.py
```

## API Endpoints

### Chat Endpoint

**POST** `/api/chat`

Request:
```json
{
  "message": "When are the exams?"
}
```

Response:
```json
{
  "reply": "Based on college records, here's what I found..."
}
```

### Transcribe Endpoint

**POST** `/api/transcribe`

Requires: Audio file (webm format)

Response:
```json
{
  "transcript": "What is the exam schedule?"
}
```

## Troubleshooting

### Issue: "No such file: notice_index.faiss"

**Solution**: The index will be created automatically on first run. Make sure `notice_dataset.json` exists.

### Issue: "OPENAI_API_KEY not found"

**Solution**: The system will fall back to local RAG responses. Set the environment variable if you want GPT responses:
```bash
set OPENAI_API_KEY=sk-...
```

### Issue: Slow response on first query

**Solution**: This is normal. The Sentence Transformer model is being loaded. Subsequent queries will be faster.

### Issue: "Speech recognition not working"

**Solution**: 
- Use Chrome or Edge browser (best support)
- Check microphone permissions
- Ensure browser allows microphone access

## Performance Tips

1. **Faster responses**: Set `top_k=3` instead of 5 for quicker search
2. **Better accuracy**: Use OpenAI API for natural language responses
3. **Offline support**: Remove OpenAI key - system uses local RAG
4. **Rebuild index**: If data changes, run `build_notice_faiss.py`

## Advanced Usage

### Using Different LLM Models

To use a different sentence transformer model:

```python
# In app.py
model = SentenceTransformer("paraphrase-MiniLM-L6-v2")  # Different model
```

Available models: https://www.sbert.net/docs/pretrained_models.html

### Custom Data Integration

Add more college data:

1. Add JSON files to `../output/`
2. Update `load_data()` to include new sources
3. Rebuild FAISS index: `python build_notice_faiss.py`

## Project Structure

```
Scripts/
├── app.py                      # Main Flask application
├── setup.py                    # Setup script
├── requirements.txt            # Python dependencies
├── build_notice_faiss.py      # FAISS index builder
├── templates/
│   └── index.html             # Web interface
├── static/
│   ├── app.js                 # Frontend JavaScript
│   └── styles.css             # Frontend styles
└── ../
    ├── output/
    │   ├── notice_dataset.json
    │   └── dbgi_structured.json
    └── vector_db/
        └── notice_index.faiss
```

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Vector Search**: FAISS (Facebook AI Similarity Search)
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **LLM**: OpenAI GPT-3.5-turbo (optional)
- **Frontend**: Vanilla JavaScript + HTML + CSS
- **Speech**: Web Speech API + OpenAI Whisper (optional)

## Performance Metrics

- **Search Time**: ~50-100ms per query
- **Response Time**: 500ms-2s with OpenAI, 100-300ms locally
- **Vector Database Size**: ~150MB (FAISS index)
- **Memory Usage**: ~500MB typical operation

## Future Improvements

- [ ] Support for other LLMs (Claude, Llama, etc.)
- [ ] Multiple college support
- [ ] Answer confidence scoring
- [ ] Chat history persistence
- [ ] Advanced filtering (date range, category)
- [ ] Document uploads for context
- [ ] Multi-language support

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review log output from `app.py`
3. Ensure all dependencies are installed: `pip list`
4. Check that data files exist in `../output/`

## License

MIT License

## Version

College Assistant v1.0
