# Use a slim Python base
FROM python:3.10-slim

# Install required system libraries for Chromium (used by Playwright)
RUN apt-get update && apt-get install -y \
    curl gnupg git wget unzip \
    ca-certificates fonts-liberation libnss3 libxss1 libasound2 \
    libatk-bridge2.0-0 libgtk-3-0 libdrm2 libgbm1 libx11-xcb1 \
    libxcomposite1 libxdamage1 libxrandr2 libxshmfence1 \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy all your project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and its browsers
RUN playwright install

# Expose port
EXPOSE 8000

# Start the FastAPI app using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
