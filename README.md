# GA Toys Chatbot - RAG Implementation

Customer Service Chatbot dengan Retrieval-Augmented Generation (RAG)

## 📁 Project Structure

```
CHATBOT_SKRIPSI/
├── core/               # Core business logic
├── embeddings/         # Embedding models
├── data/              # Data management
├── retrieval/         # RAG retrieval
├── query/             # Query processing
├── metrics/           # Metrics & logging
├── utils/             # Utilities
├── api/               # API layer
├── tests/             # Testing
└── main.py            # Entry point
```

## 🚀 Quick Start

### Installation

```bash
# Create virtual environment

venv_fix\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### Run Chatbot

```bash
# Interactive mode
python main.py

# Run tests
python main.py test

# Export metrics
python main.py metrics
```

### Run API Server

```bash
python api/server.py
```

## 📊 Features

- ✅ Pure RAG Architecture
- ✅ Context Validation
- ✅ Multi-model Embedding Support
- ✅ Auto-refresh Index
- ✅ Comprehensive Metrics
- ✅ FastAPI REST API
- ✅ Thread-safe Operations

## 📖 Documentation

See individual module docstrings for detailed documentation.

## 🧪 Testing

```bash
python -m pytest tests/
```

## 📝 License

[Your License]
