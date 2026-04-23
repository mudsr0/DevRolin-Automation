FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for typical web scraping / playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser dependencies (needed for backend scraping)
RUN playwright install --with-deps chromium

COPY . .

EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
