FROM python:3.11-slim

WORKDIR /app

# Install curl for healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install guardrails hub validators (non-fatal if hub unreachable)
RUN guardrails hub install hub://guardrails/valid_length --quiet || true
RUN guardrails hub install hub://guardrails/detect_jailbreak --quiet || true

COPY . .

EXPOSE 8000
CMD ["python", "main.py"]
