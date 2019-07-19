FROM tensorflow/tensorflow

RUN apt-get update && apt-get -y install wget
RUN wget https://dl.min.io/client/mc/release/linux-amd64/mc && chmod +x ./mc && mv ./mc /usr/local/bin
COPY download.sh /
RUN chmod +x /download.sh

ENTRYPOINT []
