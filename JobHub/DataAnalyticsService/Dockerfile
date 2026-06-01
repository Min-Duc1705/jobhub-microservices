FROM python:3.10-slim

WORKDIR /app

# ── System deps ────────────────────────────────────────────────────────────────
# libgomp1: cần cho xgboost (OpenMP runtime), nhẹ hơn nhiều so với build-essential
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# ── Cài thư viện ──────────────────────────────────────────────────────────────
# --prefer-binary: BẮT BUỘC dùng wheel đã biên dịch sẵn từ PyPI
#   → xgboost, prophet, scikit-learn đều có binary wheel → không cần compile
COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# ── Copy source code ───────────────────────────────────────────────────────────
COPY . .

EXPOSE 5007

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5007"]
