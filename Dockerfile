FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt -y update && apt -y install make build-essential python3.11 python3-pip vim

RUN python3.11 -m pip install --upgrade pip

COPY requirements.txt requirements.txt
RUN python3.11 -m pip install --upgrade -r requirements.txt

COPY Makefile .
COPY src/ .

EXPOSE 8000

# TODO: May not be needed? Just for apt deps.
RUN make production_setup

CMD ["make", "production_run"]
