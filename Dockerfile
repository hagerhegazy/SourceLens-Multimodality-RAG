FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HUB_DISABLE_SYMLINKS_WARNING=1 GRADIO_SERVER_NAME=0.0.0.0 GRADIO_ANALYTICS_ENABLED=False

# system libraries needed by OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU-only PyTorch first: far smaller than the default CUDA build
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# run as a normal user; pre-create the folders that hold data and model caches
RUN useradd -m -u 1000 appuser \
    && mkdir -p /app/data /app/store /home/appuser/.cache /home/appuser/.EasyOCR \
    && chown -R appuser:appuser /app /home/appuser
USER appuser

EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:7860/')"

CMD ["python", "app.py"]
