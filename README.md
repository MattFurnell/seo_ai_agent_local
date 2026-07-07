# SEO AI Agent

Azure-hosted browser chat app for an AI SEO agent.

## Local run

pip install -r requirements.txt
uvicorn app:app --reload

## Azure startup command

uvicorn app:app --host 0.0.0.0 --port 8000

## Required environment variables

See .env.example

Deployment test
