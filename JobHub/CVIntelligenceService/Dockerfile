FROM python:3.10-slim

WORKDIR /app

# ── Bước 1: Cài torch với CUDA support (tận dụng GPU acceleration) ──────────
# Tách thành layer riêng để Docker cache lại — chỉ re-download khi version thay đổi
RUN pip install --no-cache-dir \
    torch==2.3.0 \
    --index-url https://download.pytorch.org/whl/cu121

# ── Bước 2: Cài các thư viện còn lại ─────────────────────────────────────────
# --prefer-binary: ưu tiên dùng wheel đã build sẵn, tránh compile từ source
COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# ── Bước 3: Copy source code ──────────────────────────────────────────────────
COPY . .

EXPOSE 5006

ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5006"]
