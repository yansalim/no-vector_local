## Frontend build (Vite + React)
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (include dev deps for build)
RUN npm ci && npm cache clean --force

# Copy source code
COPY . .

# Build the application (Vite outputs to ./dist)
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

## Production stage for frontend - serve static files via Nginx
FROM nginx:alpine AS frontend
COPY --from=frontend-builder /app/dist /usr/share/nginx/html
EXPOSE 80

# Backend stage
FROM python:3.11-slim AS backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Expose port
EXPOSE 8000

# Start the backend server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
