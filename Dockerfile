FROM python:3.7

ENV PYTHONUNBUFFERED 1

RUN mkdir -p /dataflowapi
WORKDIR /dataflowapi

COPY . /dataflowapi

RUN pip install -r requirements.txt

RUN chmod +x /dataflowapi/entrypoint.sh

ENTRYPOINT [ "/dataflowapi/entrypoint.sh" ]
