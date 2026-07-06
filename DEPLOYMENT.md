# 🌐 College Assistant — Deployment Guide

This guide provides step-by-step instructions for deploying the **College Assistant** chatbot in development, production, and containerized environments.

---

## 📋 Prerequisites

Before deploying, ensure you have the following requirements:
* **Python**: Version 3.8 to 3.11.
* **Dependencies**: Listed in [requirements.txt](file:///d:/assistant/zipped/requirements.txt).
* **Disk Space**: At least 2GB of free disk space for downloading sentence-transformer models and hosting FAISS index files.
* **API Keys (Optional)**:
  * `GEMINI_API_KEY`: Used for Gemini/Google AI Studio responses (preferred if available).
  * `OPENAI_API_KEY`: Fallback for GPT responses if Gemini is not set.
  * *Note: If no API keys are provided, the system will use local RAG responses.*

---

## 🔑 Environment Configuration

Create a `.env` file inside the `Scripts/` directory or project root with the following variables:

```ini
# Port to run the application on (default: 5000)
PORT=5000

# Google Gemini API Key for response generation (Preferred)
GEMINI_API_KEY=your_gemini_api_key_here

# OpenAI API Key (Fallback if Gemini is not set)
OPENAI_API_KEY=your_openai_api_key_here
```

---

## 🛠️ Deployment Options

Choose the deployment method that fits your environment:

### Option 1: Local / Development Deployment
To run the server in a local environment:

1. **Navigate to the scripts folder**:
   ```bash
   cd Scripts
   ```
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Validate the environment**:
   ```bash
   python setup.py
   ```
4. **Start the application**:
   ```bash
   python app.py
   ```
5. Open your browser and navigate to `http://localhost:5000`.

---

### Option 2: Production Deployment on Linux (Nginx + Gunicorn)
For production environments, using a WSGI server like `Gunicorn` combined with `Nginx` as a reverse proxy is the recommended setup.

#### 1. Install Gunicorn and dependencies
Activate your virtual environment and install `gunicorn`:
```bash
pip install gunicorn
```

#### 2. Configure Systemd Service
Create a systemd unit file to manage the Flask application process.
Create `/etc/systemd/system/college-assistant.service`:

```ini
[Unit]
Description=Gunicorn instance to serve College Assistant
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/college-assistant/Scripts
Environment="PATH=/var/www/college-assistant/venv/bin"
EnvironmentFile=/var/www/college-assistant/Scripts/.env
ExecStart=/var/www/college-assistant/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

Start and enable the service:
```bash
sudo systemctl daemon-reload
sudo systemctl start college-assistant
sudo systemctl enable college-assistant
```

#### 3. Configure Nginx Reverse Proxy
Create an Nginx configuration block `/etc/nginx/sites-available/college-assistant`:

```nginx
server {
    listen 80;
    server_name your_domain.com; # Replace with your domain or IP

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the configuration and reload Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/college-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### Option 3: Containerized Deployment (Docker)
Docker isolates your application code, dependencies, and environments.

#### 1. Create a `Dockerfile` in the root (`/zipped/Dockerfile`):
```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Set work directory
WORKDIR /app

# Install system dependencies needed for compiling certain packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python packages
COPY Scripts/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy source code and directories
COPY Scripts/ /app/Scripts/
COPY output/ /app/output/
COPY vector_db/ /app/vector_db/

# Expose server port
EXPOSE 5000

# Run Flask server
WORKDIR /app/Scripts
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
```

#### 2. Build and Run the Docker Container:
```bash
# Build the image
docker build -t college-assistant .

# Run the container
docker run -p 5000:5000 --env-file Scripts/.env college-assistant
```

---

### Option 4: Cloud Platform Deployment (Render / Heroku)
To deploy on PaaS environments such as **Render** or **Heroku**:

#### 1. Pre-deployment check:
* Ensure `.env` is omitted from Git (handled by our `.gitignore`).
* Define all environment secrets (`GEMINI_API_KEY` or `OPENAI_API_KEY`) as environment variables in the Cloud Provider's dashboard.

#### 2. Render Settings:
* **Service Type**: Web Service
* **Language**: Python
* **Build Command**: `pip install -r requirements.txt`
* **Start Command**: `cd Scripts && gunicorn app:app`

#### 3. Heroku Settings:
Create a `Procfile` in your repository root with:
```web
web: cd Scripts && gunicorn app:app
```
Then commit and push your code to Heroku.

---

## 🔍 Post-Deployment Verification

After deploying, run the following verification steps:

1. **Verify Health Endpoint**:
   Check if the API status is normal:
   ```bash
   curl http://localhost:5000/api/status
   ```
2. **Verify System Logs**:
   Look for the following initialization sequences in your service or container logs:
   * `Loaded sentence transformer model`
   * `Loaded FAISS index successfully`
   * `College assistant ready!`
3. **Verify API Q&A**:
   Test a simple query using curl:
   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"message":"hello"}' http://localhost:5000/api/chat
   ```
