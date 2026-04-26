FROM alpine:latest

RUN apk add --no-cache python3 py3-pip sqlite build-base python3-dev

RUN pip3 install --no-cache-dir --break-system-packages pandas requests

WORKDIR /app

COPY sse_pe_crawler.py /app/sse_pe_crawler.py

RUN mkdir -p /app/data /app/html

CMD ["python3", "sse_pe_crawler.py"]
