# Personal Finance Tracker

[![Development Status](https://img.shields.io/badge/status-in_development-yellow)](#)
![workflow](https://github.com/Dema-koder/SQRS-final-project/actions/workflows/main.yaml/badge.svg)

An application to track finances, including backend API, SQLite database, and Streamlit frontend.

Manage transactions, split your expenses to the different categories, and analyze it for free.

## Prerequisites

- **Python** 3.11+
- **Poetry** for environment and dependency management
- **Streamlit** library
- **Uvicorn** as ASGI server
- **Docker** for metrics

## Technical Stack

- **Python 3.11**
- **FastAPI** for RESTful backend
- **OpenAPI** for auto-generated API documentation
- **SQLite** for lightweight data persistence
- **Streamlit** for interactive frontend UI
- **Prometheus_client** for metrics
- **Uvicorn** as ASGI server
- **Poetry** for dependency management

## Getting Started

The instruction to run the application locally:

1. **Clone the repository**
   ```bash
   git clone https://github.com/Dema-koder/SQRS-final-project.git
   cd SQRS-final-project/
2. **Backend (Install Dependencies and Start the server)**
   ```bash
   cd backend
   poetry install
   poetry run uvicorn finance_tracker.main:app --reload
3. **Frontend** (Install Dependencies and Start the server)
   ```bash
   cd ../frontend
   poetry install
   poetry run streamlit run src/personal_finance_tracker_front/main.py
4. Access the application

 - Backend API docs:
    http://127.0.0.1:8000/docs

 - Frontend UI:
    http://localhost:8501

## Usage

Use the Streamlit interface to log incomes, expenses, and manage budgets. The backend API exposes endpoints for users, categories, transactions, budgets, and audit logs.

## CI workflow
A GitHub Actions pipeline is configured in .github/workflows/main.yml to lint, test, and perform security scans on both backend and frontend.

## Metrics

Prometheus metrics are available at the backend endpoint /metrics.

For prometheus, use `docker-compose.yaml` file:

1. Initialize backend and prometheus using `.yaml` file:
   ```bash
   docker-compose up
2. Open the prometheus: `localhost:9090`
