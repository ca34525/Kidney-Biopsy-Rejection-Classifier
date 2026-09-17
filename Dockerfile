# Build from the repository root after scripts/prepare_container.py.
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

# Install the same locked packages as development, without test/lint tools.
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
RUN uv sync --locked --no-dev --no-editable && rm -rf .uv-cache

# Only the explicitly prepared serving files enter the image.
ARG BUNDLE_DIR=build/container
COPY ${BUNDLE_DIR}/ ./runtime/
COPY scripts/serve_container.py ./serve_container.py

# The service reads its model and returns scores; it needs no privileged user.
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]
CMD ["python", "serve_container.py"]
