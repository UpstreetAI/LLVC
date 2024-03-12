FROM nvidia/cuda:11.8.0-base-ubuntu20.04
WORKDIR /src
RUN rm -rf /src/*
ADD ./requirements.txt .
RUN pip install -r requirements.txt
ADD ./download_models.py .
RUN python download_models.py
RUN pip install opuslib
RUN apt-get update && apt-get -y install libsox-dev
ADD . .
EXPOSE 8000
CMD python server.py 
