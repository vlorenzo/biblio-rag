# Stage 1: Frontend Builder
# Use a specific Node.js version to ensure consistency
FROM node:18-alpine AS frontend-builder

# Set the working directory for the frontend
WORKDIR /app/frontend

# Copy package files and install dependencies
# This leverages Docker's layer caching. `npm install` only runs if these files change.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install

# Copy the rest of the frontend source code
COPY frontend/ ./

# Build the static assets for production
# The output will be in /app/frontend/dist
RUN npm run build

# ---

# Stage 2: Backend Builder
# Use a slim Python image for a smaller base
FROM python:3.12-slim AS backend-builder

# Install uv, the Python package manager
RUN pip install uv

# Set the working directory for the backend
WORKDIR /app

# Copy dependency definition files
COPY pyproject.toml uv.lock ./
COPY README.md ./

# Install only production dependencies into a virtual environment
# This creates a self-contained set of packages we can copy later.
RUN uv sync --no-dev

# ---

# Stage 3: Final Production Image
# Start from the same slim Python base
FROM python:3.12-slim

# Set a non-root user for better security
RUN addgroup --system app && adduser --system --group app
USER app

# Set the final working directory
WORKDIR /app

# Copy the virtual environment with dependencies from the backend-builder stage
COPY --from=backend-builder /app/.venv ./.venv

# Set the PATH to include the virtual environment's binaries
ENV PATH="/app/.venv/bin:$PATH"

# Copy the built frontend static assets from the frontend-builder stage
# These will be served by FastAPI.
COPY --from=frontend-builder /app/frontend/dist ./static

# Copy the backend source code
COPY backend/ ./backend
COPY alembic.ini .
COPY migrations/ ./migrations/


# Expose the port the application will run on
# PaaS providers will typically use this and map it automatically.
EXPOSE 8000

# The command to run the application
# Use --host 0.0.0.0 to make it accessible from outside the container.
# The PaaS will set the $PORT environment variable.
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
