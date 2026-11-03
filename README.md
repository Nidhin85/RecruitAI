# RecruitAI – AI-Powered Resume Screening and Job Matching System

RecruitAI is a web-based recruitment platform designed to simplify the resume screening and candidate shortlisting process. It helps recruiters extract candidate information from PDF resumes, identify relevant skills, compare candidates against job requirements, and organize recruitment decisions.

## 🚀 Key Features

- **PDF Resume Parsing:** Extract candidate information from PDF resumes.
- **Candidate Information Extraction:** Identify names, email addresses, phone numbers, education, skills, and experience.
- **AI-Based Resume Matching:** Compare candidate skills with job description requirements using semantic matching.
- **Candidate Match Scoring:** Calculate candidate matching scores.
- **Candidate Ranking:** Organize candidates according to their matching results.
- **Recruiter Dashboard:** View and manage candidate information.
- **Candidate Search:** Search, filter, sort, and paginate candidate records.
- **Recruitment Management:** Track candidate decisions, including shortlisted, rejected, and under-review statuses.
- **Interview Management:** Schedule and manage candidate interviews.
- **Duplicate Detection:** Identify duplicate candidate records.
- **Reports and Export:** Generate recruitment reports and export candidate information.
- **Audit Logging:** Maintain records of recruitment-related activities.

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Frontend | React.js, Vite |
| Backend | Python, Flask |
| Database | MongoDB |
| PDF Extraction | PyMuPDF |
| AI / Semantic Matching | Python-based semantic matching |
| API Communication | REST API |

## 📁 Project Structure

```text
RecruitAI/
│
├── backend/
│   ├── app.py
│   ├── resume_parser.py
│   ├── candidate_extractor.py
│   ├── candidate_matcher.py
│   ├── semantic_candidate_matcher.py
│   ├── recruiter_decision.py
│   └── ...
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── api.js
│   │   └── ...
│   ├── package.json
│   └── vite.config.js
│
├── sample_resumes/
│
├── .env.example
├── .gitignore
└── README.md
```

## ⚙️ Installation and Setup

### Prerequisites

- Python
- Node.js and npm
- MongoDB
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Nidhin85/RecruitAI.git
cd RecruitAI
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install the Python dependencies required by the backend, then configure your environment variables using the root `.env.example` as a reference.

Start MongoDB before running the application.

Run the Flask application:

```bash
python app.py
```

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL displayed by Vite in your browser.

## 🔐 Environment Configuration

RecruitAI uses environment variables for database and email configuration.

- Keep actual passwords, API keys, and database credentials in your local `.env` file.
- Never upload `.env` to GitHub.
- Use `.env.example` as a reference for required environment variables.
- Keep email functionality in test mode when testing without actual email delivery.

## 🎯 Project Objective

The objective of RecruitAI is to reduce manual resume screening effort, improve candidate organization, and help recruiters identify suitable applicants more efficiently through automated resume extraction and job matching.

## 👨‍💻 Developer

**Nidhin Biju**

GitHub: https://github.com/Nidhin85

---

*RecruitAI – Making recruitment screening more organized and efficient.*