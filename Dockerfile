FROM ubuntu
RUN apt-get update
RUN apt-get install -y tzdata
RUN ln -fs /usr/share/zoneinfo/Asia/Jerusalem /etc/localtime && dpkg-reconfigure -f noninteractive tzdata
ENV DEBIAN_FRONTEND=noninteractive
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
RUN apt-get install -y python3.8 python3-pip
RUN ln -s /usr/bin/python3 /usr/bin/python && \
    ln -s /usr/bin/pip3 /usr/bin/pip
COPY bci /bci
COPY scripts /scripts
COPY requirements.txt /requirements.txt
RUN /scripts/install-docker.sh
EXPOSE 5000
EXPOSE 8080
