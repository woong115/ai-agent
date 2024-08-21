FROM --platform=linux/arm64 python:3.11-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./app ./app
COPY ./tests ./tests
COPY ./pdfs ./pdfs
COPY ./pymupdf4llm ./pymupdf4llm
COPY ./docker-entrypoint.sh .
COPY ./gunicorn.conf.py .

#COPY ./pytest.ini .
ENV PYTHONPATH=/code

EXPOSE 5000
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD [ "gunicorn" ]
