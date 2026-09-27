# INSUREAI – Evidence-Grounded Insurance Pitch Generator

INSUREAI is an AI-powered insurance advisory prototype that generates client-specific insurance recommendations from policy documents, verifies generated claims against source evidence, and produces a client-ready PowerPoint pitch and audit report.

## Key Features

- Company and workforce profiling
- Insurance policy comparison
- Retrieval-Augmented Generation (RAG)
- AI-generated policy recommendation
- Claim-level evidence verification
- Source document and page traceability
- Advisor review and approval workflow
- PowerPoint pitch generation
- PDF audit report generation
- Grounded insurance chatbot
- Out-of-scope question guardrails

## Tech Stack

### Frontend
- React
- TypeScript
- Vite
- TanStack
- Tailwind CSS

### Backend
- Python
- FastAPI
- Uvicorn
- Groq LLM API
- Document retrieval / RAG
- python-pptx
- PDF processing

---

# Project Structure

```text
INSURE_AI/
│
├── frontend/                 # React frontend
├── src/                      # FastAPI backend and AI workflow
├── data/                     # Insurance policy brochures
├── templates/                # PowerPoint template
├── sample_outputs/           # Generated sample pitch and audit report
├── writeup/                  # Project report
├── docs/                     # Supporting documentation
│
├── requirements.txt
├── render.yaml
├── .env.example
├── .gitignore
└── README.md
```

---

# Running the Project Locally

## Prerequisites

Install:

- Python 3.11+
- Node.js
- npm
- Git

---

## 1. Clone the Repository

```bash
git clone https://github.com/surbhi1us/INSURE_AI.git
cd INSURE_AI
```

---

## 2. Backend Setup

Create a Python virtual environment:

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Environment Variables

Create a `.env` file in the project root.

Use `.env.example` as reference.

Example:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
CORS_ORIGINS=http://localhost:5173
```

Do not commit the `.env` file or API keys to GitHub.

---

## 4. Start the Backend

From the project root:

```bash
uvicorn src.api:app --reload --host 127.0.0.1 --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 5. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
```

Create `frontend/.env` if required:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the frontend:

```bash
npm run dev
```

Open the URL displayed by Vite, normally:

```text
http://localhost:5173
```

---

# Application Workflow

1. Enter a company.
2. Specify client insurance priorities.
3. Select insurance policies for comparison.
4. Generate the AI-assisted pitch.
5. Review retrieved policy evidence.
6. Review the claim-level audit.
7. Approve the pitch for advisor use.
8. Download the PowerPoint client pitch.
9. Download the supporting audit report.
10. Use the grounded insurance chatbot for policy-related questions.

---

# Evidence Verification

INSUREAI verifies important generated insurance claims against retrieved policy-document evidence.

The audit layer records:

- Generated claim
- Verification status
- Source document
- Source page
- Citation match
- Retrieval similarity
- Supporting evidence
- Audit reason

This provides traceability between client-facing statements and the supplied policy documents.

---

# Sample Output

The repository includes a sample TATA insurance advisory case.

The sample output contains:

- A 5-slide client pitch
- Policy recommendation
- Policy comparison
- Claim-level evidence audit
- Source-document traceability

See the `sample_outputs/` directory.

---

# Important Note

INSUREAI is an advisory prototype.

Generated recommendations should be reviewed by an insurance advisor against official policy wording, exclusions, pricing, and insurer quotations before external client use.

---

# Authors

Developed as part of the Marsh AI insurance pitch and audit case study.