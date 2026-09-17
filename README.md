# CS AI Lab

A hands-on AI-103 learning project for a computer-science knowledge assistant using Retrieval-Augmented Generation (RAG). It ingests selected computer-science reference books, extracts and chunks their text, indexes them in Azure AI Search, and answers questions with Azure OpenAI.

## Architecture

```text
Source books
  → document ingestion (ingestion/)
  → text extraction and chunking
  → embeddings + upload (search/upload_chunks.py)
  → Azure AI Search index (search/create_index.py)
  → retrieval + answer generation (rag/ask.py)
  → Streamlit UI (apps/chat.py) / evaluation (evaluation/)
```

See [docs/architecture.md](docs/architecture.md) for more detail.

## Prerequisites

- Python 3.11+ and a virtual environment (`.venv`)
- An Azure subscription with:
  - Azure AI Search
  - Azure OpenAI, with `gpt-4.1-mini` and `text-embedding-3-small` deployed
- Azure CLI, signed in with `az login`
- Your account granted these roles on the resources:
  - `Cognitive Services OpenAI User` on the Azure OpenAI resource
  - `Search Index Data Reader`, `Search Index Data Contributor`, and `Search Service Contributor` on the Azure AI Search service

Authentication uses `DefaultAzureCredential` (Entra ID); no API keys are stored in `.env`.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Fill in `.env` with your Azure AI Search and Azure OpenAI endpoint and deployment names.

## Ingest the book corpus

```powershell
python ingestion/inventory.py <path-to-books>
python ingestion/extract_pdf_text.py <path-to-books>
python ingestion/chunk_text.py
python search/create_index.py
python search/upload_chunks.py
```

Use `--limit 1` on `upload_chunks.py` for a low-cost smoke test before uploading the full corpus.

## Ask a question

```powershell
python rag/ask.py "What problem characteristics make dynamic programming appropriate?"
```

Add `--top` to change retrieved chunk count, or `--retrieval-mode hybrid` to combine keyword and vector search.

## Chat UI

```powershell
python -m streamlit run apps/chat.py
```

## Evaluation

```powershell
python evaluation/run_evaluation.py
python evaluation/compare_retrieval.py
```

`run_evaluation.py` scores answers against `evaluation/questions.json` for expected-source retrieval, required-concept coverage, and citation validity. `compare_retrieval.py` compares vector vs. hybrid retrieval across multiple `--top` values without generating answers.

## Deployment

Azure App Service infrastructure is defined in [infrastructure/main.bicep](infrastructure/main.bicep) and deployed with [infrastructure/deploy_app.ps1](infrastructure/deploy_app.ps1). The web app uses a system-assigned managed identity; grant it `Cognitive Services OpenAI User` and `Search Index Data Reader` after provisioning.