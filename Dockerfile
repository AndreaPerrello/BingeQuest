FROM python:3.9

# Copy files
COPY ./ /app

# Create db folder, file and add permissions
RUN mkdir /app/.mycache
RUN touch /app/.mycache/cache.db
RUN chmod 777 /app

# Set working directory
WORKDIR /app

# Install requirements
RUN  pip install --no-cache-dir -r requirements.txt

# Run the code
CMD ["python", "main.py"]