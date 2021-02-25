FROM python:3.8.7
MAINTAINER Justin Flannery "juftin@juftin.com"

RUN python -m pip install --upgrade pip
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt && rm /tmp/requirements.txt

ENV PYTHONPATH="${PYTHONPATH}:/home/adjuftments_v2/"