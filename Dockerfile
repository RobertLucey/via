FROM ubuntu:20.04

WORKDIR /code

RUN apt -y update && apt -y install build-essential python-numpy python-setuptools python3-scipy libatlas-base-dev libatlas3-base python3-pip

RUN python3 -m pip install virtualenv

COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt

EXPOSE 8080
COPY . .

CMD ["make", "run_bottle"]
