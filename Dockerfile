FROM python:3.10-alpine

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements.txt --pre && \
    rm requirements.txt

WORKDIR /usr/src
COPY autoposter autoposter

CMD ["python", "-m", "autoposter"]
STOPSIGNAL SIGINT
