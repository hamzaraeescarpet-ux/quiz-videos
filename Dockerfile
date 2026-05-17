FROM node:20 AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.10-slim

# Install system dependencies required by MoviePy and edge-tts
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick security policy
RUN mv /etc/ImageMagick-6/policy.xml /etc/ImageMagick-6/policy.xml.bak || true

# Setup a non-root user
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    IMAGEMAGICK_BINARY=/usr/bin/convert

WORKDIR $HOME/app

# Copy requirements and install
COPY --chown=user:user requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files
COPY --chown=user:user . $HOME/app

# Copy built frontend from previous stage
COPY --from=frontend-builder --chown=user:user /frontend/dist $HOME/app/frontend/dist

# Ensure necessary directories exist
RUN mkdir -p $HOME/app/output $HOME/app/temp && \
    chmod -R 777 $HOME/app/output $HOME/app/temp

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
