FROM python:3.11

WORKDIR /opt/app

COPY requirements.txt /opt/app
RUN pip3 install -r requirements.txt

COPY . /opt/app