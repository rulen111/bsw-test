FROM python:3.10-alpine
WORKDIR /
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN rm requirements.txt
COPY *.py   /common/