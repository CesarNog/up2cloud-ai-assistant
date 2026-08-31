# Hugging Face Spaces Configuration for UP2CLOUD
# This file tells Hugging Face how to run the Gradio app

FROM python:3.11-slim

WORKDIR /app

# Copy all project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gradio

# Expose port
EXPOSE 7860

# Run the app
CMD ["python", "app.py"]
