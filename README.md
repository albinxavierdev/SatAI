# Vedika – AI Chatbot for ISRO Satellite Data
*A structured development roadmap*

---

## Overview
**Vedika** is an AI-powered chatbot designed to provide researchers, students, and professionals with accurate, context-aware answers about ISRO satellite datasets. It integrates historical archives (since 1986) and near-real-time satellite data into a single knowledge base (KB), enabling intelligent query handling such as comparisons, geospatial extents, and product details.

---

## Phase 1: Data Sourcing & Preparation
**Goal:** Collect, clean, and standardize both historical and live ISRO satellite data.  
- Register and access ISRO portals: **MOSDAC, Bhoonidhi, Bhuvan, VEDAS, ISDA**.  
- Gather **historical archives** (e.g., 1986 onward datasets from Bhoonidhi).  
- Set up feeds for **near-real-time products** (e.g., MOSDAC Live INSAT-3DS data, Bhuvan daily mosaics).  
- Collect **unstructured docs** (PDFs, brochures, manuals).  
- Clean and normalize:  
  - Standardize dates, spatial extents (GeoJSON), and satellite metadata.  
  - Tag historical vs. live data for clarity.  
- Validate against ISRO official docs.  

---

## Phase 2: Knowledge Base & Real-Time Updates
**Goal:** Build and maintain Vedika’s hybrid knowledge base (KB).  
- Structured storage: **PostgreSQL/SQLite** for satellite metadata.  
- Unstructured storage: **Vector DB (FAISS/Pinecone)** for semantic search of documents.  
- Index and embed: satellites, instruments, datasets, product manuals.  
- Automate **update pipelines**: cron jobs / schedulers to fetch new datasets daily/hourly.  
- Implement **monitoring & logging** for failures (API downtime, broken feeds).  
- Version control for scripts & timestamps to track freshness.  

---

## Phase 3: AI/NLP Integration
**Goal:** Enable Vedika to understand and respond to natural language queries.  
- **Entity recognition (spaCy/HF):** detect satellite names, instruments, geospatial terms.  
- **Intent classification (ML model):** distinguish query types (e.g., “compare satellites”, “give geospatial extent”, “download data”).  
- **RAG pipeline setup:**  
  - Retrieve snippets from KB (vector search).  
  - Generate responses via LLM (fine-tuned on ISRO terminology).  
- Fine-tune/customize: add ISRO-specific vocab (e.g., INSAT payloads, EOS missions).  
- Context handling: maintain conversation history (LangChain memory).  

---

## Phase 4: Chatbot Development, Testing & Deployment
**Goal:** Deliver Vedika as a functional, user-facing AI chatbot.  
- Build **UI** (Streamlit or Gradio) → simple, clean chat window.  
- Connect UI → NLP backend → KB.  
- Features:  
  - Query handling (“Compare INSAT-3D vs. 3DS”).  
  - Conversation memory for follow-ups.  
  - Optional: voice mode, map/visual previews of geospatial data.  
- **Testing:** simulate live update events (new satellite data availability).  
- **Deployment:** containerize with Docker, deploy on **AWS/Heroku**.  
- Add **feedback loop:** log queries, refine answers, expand KB coverage.  

---

✅ With these phases, **Vedika** becomes a **context-aware satellite data assistant** — seamlessly bridging ISRO’s archives with live updates to serve researchers, students, and the wider space-tech community.
