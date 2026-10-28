FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DB_PATH=/app/data/app.db

WORKDIR /app

# Dependências primeiro, para aproveitar o cache de camadas
# Instala só wheels (sem executar setup.py) com versões e hashes travados no requirements.txt.
# O pip não é usado em runtime e traz bibliotecas embutidas com CVEs (pip/_vendor),
# por isso é removido depois de instalar as dependências.
COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary :all: --require-hashes -r requirements.txt \
    && pip uninstall -y pip

COPY app/ ./app/

# Executa sem root; o diretório do banco SQLite pertence ao usuário da aplicação
RUN useradd --create-home appuser \
    && mkdir -p /app/data \
    && chown appuser:appuser /app/data
USER appuser

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
