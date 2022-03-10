FROM python:3.10

RUN apt update && apt install git -y

WORKDIR /tg

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY *.py .
COPY *.session* .

ENTRYPOINT ["inv"]
