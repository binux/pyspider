FROM dockerfile/ubuntu
MAINTAINER binux <roy@binux.me>

# install python
RUN apt-get update
RUN apt-get install -y python python-dev python-distribute python-pip

# install binary depends
RUN apt-get install -y libcurl4-openssl-dev libxml2-dev libxslt1-dev

# install requirements
ADD requirements.txt /opt/pyspider/requirements.txt
RUN pip install --allow-all-external -r /opt/pyspider/requirements.txt

# add all repo
ADD ./ /opt/pyspider

# run test
WORKDIR /opt/pyspider
RUN IGNORE_MYSQL=1 IGNORE_RABBITMQ=1 ./runtest.sh

VOLUME ["/opt/pyspider/data"]

ENTRYPOINT ["python", "run.py"]

EXPOSE 5000
EXPOSE 23333
EXPOSE 24444
