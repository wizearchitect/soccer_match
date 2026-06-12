# ─────────────────────────────────────────────────────────────────────────────
# The Soccer Pitch — Headless Docker Image
#
# Multi-architecture: supports linux/amd64 AND linux/arm64 (SnapDeploy, AWS
# Graviton, Apple Silicon, etc.)
#
# python:3.11-slim is an official multi-arch image — Docker automatically
# pulls the correct variant for the build platform.
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1 : builder ────────────────────────────────────────────────────────
FROM --platform=$BUILDPLATFORM python:3.11-slim AS builder

WORKDIR /install

COPY pitch/requirements_headless.txt ./requirements.txt

RUN pip install --no-cache-dir --prefix=/install/deps -r requirements.txt


# ── Stage 2 : runtime ────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Non-root user for security
RUN groupadd -r pitch && useradd -r -g pitch -u 1001 pitch

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install/deps /usr/local

# Copy application source
COPY pitch/ ./pitch/

RUN chown -R pitch:pitch /app

USER pitch

ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request, os; urllib.request.urlopen('http://localhost:' + os.getenv('PORT','8000') + '/api/state', timeout=4)"

CMD ["python", "-m", "pitch.main_headless"]
