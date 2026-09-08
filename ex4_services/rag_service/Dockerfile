FROM python:3.11-slim

WORKDIR /app

# Install curl for healthchecks and build dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# CPU-only torch avoids pulling 2GB+ CUDA libs
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download the sentence-transformer model so it's baked into the image
# (avoids downloading at runtime which needs internet + RAM spike)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

EXPOSE 8001
CMD ["python", "main.py"]
