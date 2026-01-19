# Use an official Python slim image for a lightweight container
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies needed for some Python packages (like fpdf2 or if needed for others)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the Flask app runs on
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=server.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV UIDAI_API_KEY="579b464db66ec23bdd000001623c2de44ffb40755360bbc473134c16"

# Run the application
CMD ["python", "server.py"]
