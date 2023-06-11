FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt -y update && apt -y install make build-essential python-numpy python-setuptools python3-scipy libatlas-base-dev libatlas3-base python3-pip vim

COPY requirements.txt requirements.txt
RUN python3 -m pip install --upgrade -r requirements.txt

COPY Makefile .
COPY src/ .

# TODO: May not be needed? Just for apt deps.
RUN make production_setup

EXPOSE 8000

CMD ["make", "production_run"]
