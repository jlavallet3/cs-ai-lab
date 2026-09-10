# Architecture

## Overview

CS AI Lab is a Retrieval-Augmented Generation (RAG) project that will create a computer-science knowledge assistant. It will answer questions using selected reference books as grounded source material.

## Goals

- Ingest local computer-science reference books.
- Extract and prepare text for search.
- Store searchable chunks and metadata in Azure AI Search.
- Retrieve relevant content for a user question.
- Generate grounded answers with Azure OpenAI.
- Evaluate answer quality, relevance, and citation accuracy.

## High-level pipeline

```text
Local source books
  → document ingestion
  → text extraction
  → chunking and metadata
  → embeddings
  → Azure AI Search index
  → retrieval
  → Azure OpenAI response generation
  → CS Knowledge Assistant