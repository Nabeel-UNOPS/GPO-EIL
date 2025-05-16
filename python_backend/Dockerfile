# Use the official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY . .

# Set PORT for Cloud Run and expose it
ENV PORT 8080
EXPOSE 8080

# Start the app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
