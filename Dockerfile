FROM python:3.6
ENV PYTHONUNBUFFERED 1
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y ntp
RUN mkdir /code
RUN mkdir /code/requirements && echo
COPY ./deployment/requirements/* /code/requirements/

WORKDIR /code
RUN pip install -r /code/requirements/dev.txt

ADD . /code/