# Dockerfile for containerized deployment
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    nodejs \
    npm \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download JUnit
RUN wget -O junit-platform-console-standalone-1.10.2.jar \
    https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.10.2/junit-platform-console-standalone-1.10.2.jar

# Copy application
COPY . .

# Create directories
RUN mkdir -p uploads generated_tests

EXPOSE 5000

CMD ["python", "app.py"]
