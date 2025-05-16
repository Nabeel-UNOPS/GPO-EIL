# Use the official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY . .

# Make sure PORT is set (Cloud Run will override this)
ENV PORT 8080

# Expose the port
EXPOSE 8080

# Start the app with Gunicorn on the correct port
CMD exec gunicorn --bind 0.0.0.0:$PORT app:app
