# ─────────────────────────────────────────────────────────────────────────────
# The Soccer Pitch — Headless Docker Image
#
# Two-stage build:
#   Stage 1 (builder) — install Python deps into a clean prefix
#   Stage 2 (runtime) — copy only the installed packages + app source
#
# No pygame, no display, no audio required.
# Match control via web dashboard at  http://<host>:8000/
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1 : builder ────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /install

# Copy only the requirements file first so Docker layer-caches the pip step
# independently of source-code changes.
COPY pitch/requirements_headless.txt ./requirements.txt

RUN pip install --no-cache-dir --prefix=/install/deps -r requirements.txt


# ── Stage 2 : runtime ────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# ── Security: non-root user ───────────────────────────────────────────────────
RUN groupadd -r pitch && useradd -r -g pitch -u 1001 pitch

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /install/deps /usr/local

# Copy application source — pitch package only (tests, venvs excluded via .dockerignore)
COPY pitch/ ./pitch/

# Fix ownership
RUN chown -R pitch:pitch /app

USER pitch

# ── Runtime environment ───────────────────────────────────────────────────────
# Cloud Run injects PORT at runtime; we default to 8000 for local docker run.
ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# ── Health check ──────────────────────────────────────────────────────────────
# Shell form so $PORT expands correctly at runtime.
# Polls /api/state every 20s; allows 15s boot time before first check.
HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request, os; urllib.request.urlopen('http://localhost:' + os.getenv('PORT','8000') + '/api/state', timeout=4)"

# ── Entry point ───────────────────────────────────────────────────────────────
CMD ["python", "-m", "pitch.main_headless"]
