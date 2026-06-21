# OmniSense AI Wizard (AKA SteelMind Ai Wizard) 🏭🤖
**Multimodal Multi-Agent AI Maintenance Decision Support System for Steel Plants**

Built for the **Tata Steel AI Hackathon 2026**.

OmniSense is an intelligent maintenance assistant designed to help engineers at steel plants diagnose machinery issues, predict failures, and generate actionable repair strategies. It uses a **multi-agent architecture** (powered by LangGraph) to seamlessly combine text, voice, image, sensor data, and technical manuals into a single, comprehensive diagnostic process.

## 🌟 Key Features

- **Multimodal Interactions:** Interact via text or voice (Whisper STT/TTS). Upload images of broken parts, CSVs of sensor data, or PDFs of equipment manuals.
- **Multi-Agent Diagnostics:** A specialized team of AI agents work together to analyze the data and provide accurate diagnoses.
- **Predictive Maintenance:** Uses machine learning (XGBoost/Scikit-learn) to detect anomalies in sensor data and predict Remaining Useful Life (RUL).
- **Automated Reporting:** Generates detailed maintenance reports (PDF/Markdown) automatically after diagnosis.
- **Real-Time Assistant:** A responsive React frontend connected via WebSockets provides a live conversational experience with the AI.
- **Continuous Learning Loop:** The Feedback Agent allows engineers to confirm or correct diagnoses, helping the system learn over time.

## 🛠️ Technology Stack

### Backend (Python/FastAPI)
- **Framework:** FastAPI, Uvicorn
- **AI/LLM orchestration:** LangChain, LangGraph
- **Models:** Groq, Google Generative AI (Gemini)
- **RAG & Vector DB:** FAISS
- **Machine Learning:** Scikit-learn, XGBoost, Pandas, Numpy
- **Voice/Audio:** OpenAI Whisper, gTTS
- **Others:** PyPDF, FPDF2 (Reporting)

### Frontend (React/Vite)
- **Framework:** React 19, Vite
- **Styling:** Tailwind CSS, Framer Motion (Animations)
- **Icons:** Lucide React
- **Others:** React Markdown, Axios, HTML2PDF

## 🧠 Multi-Agent Architecture (`src/agents/`)

OmniSense relies on a sophisticated graph of specialized agents:

1. **Orchestrator (`orchestrator.py`):** The mastermind that routes inputs to the correct specialized agents based on user query and attached files.
2. **Vision Agent (`vision_agent.py`):** Analyzes uploaded equipment photos for visible wear, tear, or faults.
3. **RAG Agent (`rag_agent.py`):** Queries technical manuals and historical logs using FAISS vector search.
4. **Diagnostic Agent (`diagnostic_agent.py`):** Consolidates findings and reasons through the primary fault.
5. **Anomaly Agent (`anomaly_agent.py`):** Evaluates tabular sensor data (CSVs) using ML models.
6. **Risk Scorer (`risk_scorer.py`):** Assigns a risk level (LOW, MEDIUM, HIGH, CRITICAL) and estimates RUL.
7. **Report Generator (`report_generator.py`):** Creates downloadable PDF/MD reports.
8. **Feedback Agent (`feedback_agent.py`):** Handles post-repair feedback to improve future accuracy.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- API Keys for Groq and Google Gemini (Set in `.env`)

### 1. Setup the Backend
```bash
# Clone the repo and enter the directory
cd steelmind-ai-wizard

# Create a virtual environment and activate it
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys

# Run the FastAPI server
uvicorn main:app --reload --port 8000
```
*The API will be available at `http://localhost:8000`*

### 2. Setup the Frontend
```bash
# Open a new terminal
cd steelmind-ai-wizard/frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```
*The app will be available at `http://localhost:5173`*

## 📁 Project Structure

```text
steelmind-ai-wizard/
├── .env.example
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── src/                    # Backend source code
│   ├── agents/             # The multi-agent LangGraph system
│   ├── graph/              # LangGraph pipeline definition
│   ├── schemas/            # Pydantic models and Enums
│   └── utils/              # Helper functions (voice, etc.)
├── frontend/               # React User Interface
│   ├── src/                # React components, pages, and hooks
│   ├── package.json        # Node dependencies
│   ├── tailwind.config.js  # Tailwind configuration
│   └── vite.config.js      # Vite configuration
├── uploads/                # Temporary storage for inputs (images, audio, csv)
└── reports/                # Generated PDF/MD maintenance reports
```
