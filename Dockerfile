FROM python:3.11-slim

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

ENV CHROMA_PERSIST_DIR=/tmp/chroma_db
ENV UPLOAD_DIR=/tmp/uploads

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]