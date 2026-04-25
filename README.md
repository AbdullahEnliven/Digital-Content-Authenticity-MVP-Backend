# TrustVerify Backend

This is the main TrustVerify API backend. It handles authentication, uploads, verification history, certificates, credit usage, and communication with the ML service.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file from `.env.example`, then run database migrations if your environment requires them.

## Run

```bash
uvicorn app.main:app --reload
```

## ML Service

The ML service lives at the repository root in `ml-service`. It is kept separate from the main API so model inference dependencies and routes can evolve independently.
