FROM python:3.12

WORKDIR /home/app/async_api

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt .

RUN  pip install --no-cache-dir --upgrade pip \
     && pip install --no-cache-dir -r requirements.txt

COPY .. .

RUN chmod +x  /home/app/async_api/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/home/app/async_api/entrypoint.sh"]
