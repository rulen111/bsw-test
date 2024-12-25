FROM python:3.10-alpine
WORKDIR /
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY main.py main.py
CMD ["python", "-u", "main.py"]