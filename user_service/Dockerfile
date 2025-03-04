# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables (optional)
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt .

# Install dependencies in a single step (reduces layer size)
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Start the Django app using Gunicorn
CMD ["gunicorn", "user_service.wsgi:application", "--bind", "0.0.0.0:8000"]