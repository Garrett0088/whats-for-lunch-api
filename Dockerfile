FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements first so Docker can cache this layer independently
COPY requirements.txt .

# Install dependencies without caching to keep the image smaller
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Start the FastAPI app with uvicorn; --reload watches for file changes during development
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
