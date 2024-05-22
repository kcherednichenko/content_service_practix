FROM python:3.10

WORKDIR /home/app/tests/functional

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /home/app

COPY ./requirements.txt .

RUN  pip install --no-cache-dir --upgrade pip && \
     pip install --no-cache-dir -r requirements.txt

COPY .. .

RUN chmod +x  /home/app/tests/functional/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/home/app/tests/functional/entrypoint.sh"]
