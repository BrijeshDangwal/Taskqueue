# Start from a slim Python base — small, official, includes Python 3.12.
FROM python:3.12-slim

# Don't buffer stdout/stderr — logs appear immediately (important in containers).
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the image.
WORKDIR /app

# Copy requirements FIRST (before the rest of the code).
# This is a caching optimization: Docker caches this layer, so deps only
# reinstall when requirements.txt changes — not on every code edit.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the application code.
COPY . .

# Default command — runs the API. The worker service overrides this in compose.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]