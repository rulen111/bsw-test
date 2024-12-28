FROM common
WORKDIR /
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY *.py .
CMD ["python", "-u", "main.py"]