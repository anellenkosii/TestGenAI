# Dockerfile for containerized deployment.
# Includes Java + Node toolchains so generated Java/JS tests can run inside
# the container too, not just Python ones.
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk-headless \
    nodejs \
    npm \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN wget -O /opt/junit-platform-console-standalone-1.10.2.jar \
    https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.10.2/junit-platform-console-standalone-1.10.2.jar
ENV JUNIT_JAR=/opt/junit-platform-console-standalone-1.10.2.jar

COPY . .
RUN mkdir -p uploads generated_tests

# Run as a non-root user — generated/AI-produced test code executes inside
# this container, so it shouldn't run as root.
RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

ENV PORT=5002
EXPOSE 5002

CMD ["python", "app.py"]