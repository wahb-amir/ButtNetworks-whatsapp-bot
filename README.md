# WhatsApp RAG Bot

A WhatsApp chatbot built with **FastAPI**, **Twilio**, **Supabase pgvector**, **Groq**, and **local embeddings**. The bot stores conversation history, retrieves relevant knowledge chunks with vector search, and generates grounded replies with an LLM.

## Features

* WhatsApp webhook integration
* FastAPI backend
* Groq LLM response generation
* Supabase-backed chat memory
* pgvector retrieval for knowledge chunks
* Local embeddings for chunking and query search
* Retrieval test scripts for debugging and validation
* Docker-ready project structure

## Project Structure

```text
app
├── api
│   └── v1
│       ├── routes.py
│       └── webhook.py
├── core
│   └── config.py
├── db
│   ├── schema.sql
│   └── supabase_client.py
├── main.py
├── repositories
│   ├── chat_repository.py
│   └── knowledge_repository.py
└── services
    ├── embeddings
    │   └── local_embeddings.py
    ├── llm
    │   └── groq_client.py
    └── rag
        ├── pipeline.py
        └── retriever.py

scripts
├── deep-research-report.md
├── ingest_docs.py
├── retival_test.py
└── test.py
```

## How It Works

1. A WhatsApp message is received through the webhook.
2. The message is saved in chat memory.
3. The user query is embedded with the local embedding model.
4. Supabase pgvector retrieves the most relevant knowledge chunks.
5. The retrieved chunks and recent chat history are passed to Groq.
6. The model generates a grounded reply.
7. The reply is returned to WhatsApp.

## Main Components

### `app/api/v1/webhook.py`

Handles incoming WhatsApp requests, stores user messages, loads recent conversation history, runs the RAG pipeline, and returns the response.

### `app/repositories/chat_repository.py`

Reads and writes conversation messages and conversation records.

### `app/repositories/knowledge_repository.py`

Inserts knowledge chunks and performs vector search operations.

### `app/services/rag/retriever.py`

Embeds the query and fetches the most relevant chunks from Supabase.

### `app/services/rag/pipeline.py`

Builds the prompt context and coordinates retrieval + generation.

### `app/services/llm/groq_client.py`

Wraps the Groq API call used for answer generation.

### `app/services/embeddings/local_embeddings.py`

Creates local embeddings using the configured embedding model.

### `scripts/ingest_docs.py`

Chunks and ingests markdown content into Supabase.

### `scripts/retival_test.py`

Tests retrieval quality without sending a WhatsApp message.

### `scripts/test.py`

Simulates a webhook request locally.

## Setup

### 1. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root and add:

```env
APP_ENV=dev

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_DIM=384
```

## Database Setup

Run the schema file in Supabase SQL editor:

```sql
-- app/db/schema.sql
```

The database should include tables for:

* `conversations`
* `chat_messages`
* `knowledge_chunks`

## Ingest Knowledge Docs

To ingest the markdown knowledge file into Supabase:

```bash
python3 scripts/ingest_docs.py
```

## Test Retrieval

To test the retrieval layer without Twilio:

```bash
python3 -m scripts.retival_test
```

## Simulate a Webhook Locally

```bash
python3 scripts/test.py
```

## Run the App

```bash
uvicorn app.main:app --reload
```

## Twilio Webhook

Point your Twilio WhatsApp webhook to your exposed endpoint, for example:

```text
POST /api/v1/webhook/whatsapp
```

For local testing, use a tunnel such as ngrok.

## Current Status

The project currently supports:

* WhatsApp webhook handling
* chat persistence in Supabase
* semantic retrieval with pgvector
* Groq-powered responses
* local testing scripts

## Notes

* The bot uses short-term chat memory from recent messages.
* Retrieval quality depends on chunking and embedding quality.
* The current architecture is built to be extended with long-term memory, reranking, and hybrid search.

## Next Improvements

* Add long-term memory summaries
* Add reranking for better retrieval quality
* Add hybrid search (vector + keyword)
* Add retries and queueing for webhook reliability
* Add observability and query logging

## License

No license has been added yet.
