FROM python:3.7
MAINTAINER lizc <owner@lizc.in>

RUN mkdir -p /opt/phantomjs
COPY libs/phantomjs /opt/phantomjs/bin/phantomjs
RUN ln -s /opt/phantomjs/bin/phantomjs /usr/local/bin/phantomjs
# install requirements
COPY requirements.txt /opt/pyspider/requirements.txt
RUN pip install -r /opt/pyspider/requirements.txt -i http://pypi.douban.com/simple --trusted-host=pypi.douban.com

# add all repo
ADD ./ /opt/pyspider

# run test
WORKDIR /opt/pyspider
RUN pip install -e .[all]

VOLUME ["/opt/pyspider"]
ENTRYPOINT ["pyspider"]

EXPOSE 5000 23333 24444 25555
