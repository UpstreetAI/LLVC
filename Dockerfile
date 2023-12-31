FROM cog-temp:v1
WORKDIR /src
RUN rm -rf /src/*
ADD ./requirements.txt .
RUN pip install -r requirements.txt
ADD ./download_models.py .
RUN python download_models.py
RUN pip install opuslib
ADD . .
EXPOSE 8000
CMD python server.py 