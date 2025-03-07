FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install PostgreSQL client libraries, curl, and other necessary packages
RUN apt-get update && \
    apt-get install -y libpq-dev gcc curl && \
    rm -rf /var/lib/apt/lists/*

# Download the wait-for-it script from GitHub and make it executable
RUN curl -o /wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh \
    && chmod +x /wait-for-it.sh

# Copy the requirements file first (this optimizes caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy mytodo source code
COPY . .

# Set environment variables to avoid __pycache__ and use unbuffered logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Expose port 8000
EXPOSE 8000

# Command to run your Django application
CMD /wait-for-it.sh db:5432 -- python manage.py migrate && python manage.py runserver 0.0.0.0:8000