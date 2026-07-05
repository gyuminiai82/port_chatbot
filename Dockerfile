# Stage 1: Build Next.js frontend
FROM node:20-alpine AS builder

WORKDIR /app/frontend
COPY frontend/package.json ./
# In a real scenario with package-lock.json, use npm ci. Here we just use npm install.
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Setup Python backend and serve
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built static files from Stage 1
COPY --from=builder /app/frontend/out ./frontend/out

# Expose port
EXPOSE 8000

# Start FastAPI server using Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
