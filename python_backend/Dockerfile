# Use an official Python runtime as a base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run the application
CMD ["python", "app.py"]

# Copy app source
COPY . .

# Expose the Cloud Run default port
EXPOSE 8080

# Use Gunicorn to serve the Flask app
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
