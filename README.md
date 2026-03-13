# Omni Search Engine V4 — Ultimate Upgrade

![Omni Banner](https://img.shields.io/badge/Omni%20Search-V4--Ultimate-blue?style=for-the-badge&logo=openai)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Production%20Ready-orange?style=for-the-badge)

Omni Search is a production-grade, agentic intelligence search platform designed to compete with the likes of Perplexity, SearchGPT, and ChatGPT Atlas. It combines multi-step agentic research, real-time source transparency, and a premium localized UI to deliver deep insights in seconds.

## 🚀 Key Features

### 1. Agentic Intelligence Core
- **Multi-Step Research**: Uses an autonomous agent to decompose complex queries into sub-tasks and recursively verify information.
- **Deep Extraction**: Automatically extracts "Extracted Facts" (entities, dates, and hard data) from research streams.
- **Sentinel Reasoning**: Powered by advanced reasoning models for high-fidelity synthesis.

### 2. Global Multi-Language System
- **29+ Languages**: Full support for European, Asian, Middle Eastern, and African languages.
- **Native Localization**: The entire research stream is translated in real-time, matching the user's preferred native language.
- **Flag-Aware UI**: Dynamic UI elements reflect the selected global context.

### 3. Verified Source Transparency
- **SSE Source Streaming**: Sources are streamed and categorized in real-time.
- **Inline Citations**: Academic-grade citations `[1], [2]` map directly to sources.
- **RL Relevance Scoring**: Sources are ranked based on a reinforcement learning feedback loop (`Zap` score).

### 4. Professional Export Engine
- **Triple Format Support**: Export your research sessions as **PDF**, **Microsoft Word (DOCX)**, or **Markdown**.
- **Formatted Reports**: Exports include metadata, queries, and structured research summaries.

### 5. Premium Competitive Features
- **Focus Modes**: Switch between `General`, `Academic` (arXiv/Scholar focus), `News`, and `Code` modes.
- **Related Questions**: AI-generated follow-up questions to drive deeper discovery.
- **Engagement Loop**: Interactive feedback (Thumbs Up/Down) and one-click response copying.

---

## 🛠️ Technical Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy (Async), Uvicorn.
- **Frontend**: React 18, Vite, Lucide Icons, Vanilla CSS.
- **Intelligence**: Google Gemini (via sentinel-provider), Deep-Translator.
- **Exporting**: FPDF2, Python-Docx.

---

## 📦 Setup Instructions

### Backend Setup
1. Navigate to the `backend/` directory.
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment: `.\venv\Scripts\activate`
4. Install dependencies: `pip install fastapi uvicorn sqlalchemy httpx beautifulsoup4 deep-translator g4f google-generativeai tenacity python-docx fpdf2 aiosqlite`
5. Set your API Key: `GEMINI_API_KEY=your_key_here`
6. Run the server: `python main.py`

### Frontend Setup
1. Navigate to the `frontend/` directory.
2. Install dependencies: `npm install`
3. Run the development server: `npm run dev`
4. Open `http://localhost:5173` in your browser.

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.

Developed with ❤️ by **Shivay**
