FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run bot only
ENV PYTHONUNBUFFERED=1
CMD ["python", "main_fixed_final.py"]

