
# Brand Compliance Check for videos

This project implements an automated Video Compliance QA Pipeline orchestrated by LangGraph, designed to audit content against regulatory standards using a RAG architecture. 

Azure Video Indexer is leveraged  for multimodal ingestion (transcripts/OCR) and Azure AI Search to retrieve relevant compliance rules via Azure OpenAI Embeddings. The core reasoning engine is Azure OpenAI (GPT-4o). LangSmith provides granular tracing for LLM workflow optimization. Additionally, Azure Application Insights is integrated for production-grade telemetry, logging, and real-time performance monitoring. This end-to-end system transforms unstructured video into structured, actionable JSON compliance reports with deep full-stack observability.


## Acknowledgements

 - Guided project implemented as part of courses undertaken with Krish Naik Academy


## Environment Variables

Please refer the 'env.example' file for the environment variable configuration


## Features

- Automated Video Compliance Check 
- RAG based compliance rules retrieval
- Microsoft Azure leveraged for infrastructure


