FROM python:3.10-slim

# Install Chrome + dependencies
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg \
    libglib2.0-0 libnss3 libgconf-2-4 libxss1 libappindicator3-1 libasound2 \
    fonts-liberation xdg-utils \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable

# Download and install matching ChromeDriver (flattening nested folder path)
RUN CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+') && \
    DRIVER_URL=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json" \
      | grep -A 20 "$CHROME_VERSION" \
      | grep -oP 'https://.*chromedriver-linux64.zip' | head -1) && \
    wget -O /tmp/chromedriver.zip "$DRIVER_URL" && \
    unzip /tmp/chromedriver.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm -rf /tmp/chromedriver*

# Add chromedriver to PATH
ENV PATH="/usr/local/bin:$PATH"

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add application code
COPY . /app
WORKDIR /app

CMD ["python", "scraper.py"]
