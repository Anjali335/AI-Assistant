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

## Live Link
https://ai-assistant-8e72.onrender.com
