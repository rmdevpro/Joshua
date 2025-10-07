# Dockerfile

# Use a specific, recent version of Python for reproducibility
FROM python:3.11.5-slim-bullseye

# Set environment variables to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Create a non-root user and group
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy iccm-network library for installation
COPY iccm-network /app/iccm-network

# Install dependencies
COPY horace-nas-v2/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY horace-nas-v2/horace/ /app/horace/

# Change ownership of the app directory to the non-root user
# Note: Volumes mounted later will have their own ownership
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Expose the ports the app runs on
EXPOSE 8000 9070

# Run the application
CMD ["python", "-m", "horace.main"]
