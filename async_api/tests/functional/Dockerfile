FROM python:3.10

WORKDIR /home/app/tests

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt ./functional/requirements.txt

RUN  pip install --no-cache-dir --upgrade pip \
     && pip install --no-cache-dir -r ./functional/requirements.txt

COPY ../../. ./functional
COPY ../../testdata /home/app/testdata

RUN chmod +x  /home/app/tests/functional/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/home/app/tests/functional/entrypoint.sh"]
