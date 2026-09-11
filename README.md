# CS AI Lab

A hands-on AI-103 learning project for building a computer-science knowledge assistant using Retrieval-Augmented Generation (RAG).

## Project goal

This project will ingest selected computer-science reference books, extract and prepare their text, index the content in Azure AI Search, and provide answers through a RAG-based assistant.

## Planned architecture

```text
Source books
  → document ingestion
  → text extraction
  → chunking and metadata
  → embeddings
  → Azure AI Search
  → RAG application
  → CS Knowledge Assistant