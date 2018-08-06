FROM python:2.7
MAINTAINER twy

# install phantomjs
RUN mkdir -p /opt/phantomjs \
        && cd /opt/phantomjs \
        && wget -O phantomjs.tar.bz2 https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2 \
        && tar xavf phantomjs.tar.bz2 --strip-components 1 \
        && ln -s /opt/phantomjs/bin/phantomjs /usr/local/bin/phantomjs \
        && rm phantomjs.tar.bz2 

# install requirements
# RUN pip install --egg 'https://dev.mysql.com/get/Downloads/Connector-Python/mysql-connector-python-2.1.5.zip#md5=ce4a24cb1746c1c8f6189a97087f21c1'
COPY requirements.txt /opt/pyspider/requirements.txt

# When use pip in China download is too slow so recommend use https://pypi.tuna.tsinghua.edu.cn/simple
# RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r /opt/pyspider/requirements.txt
RUN pip install -r /opt/pyspider/requirements.txt

# if you are in China recommend run cnpm in China
RUN mkdir -p /opt/nodejs \
        && cd /opt/nodejs \
        && wget -O node-v8.11.3-linux-x64.tar.xz https://nodejs.org/dist/v8.11.3/node-v8.11.3-linux-x64.tar.xz \
        && tar xvf node-v8.11.3-linux-x64.tar.xz --strip-components 1 \
        && ln -s /opt/nodejs/bin/node /usr/local/bin/node \
        && ln -s /opt/nodejs/bin/npm /usr/local/bin/npm \
        && rm node-v8.11.3-linux-x64.tar.xz 
        # && npm install -g cnpm --registry=https://registry.npm.taobao.org \
        # && ln -s /opt/nodejs/bin/cnpm /usr/local/bin/cnpm

# add all repo
ADD ./ /opt/pyspider

# run test
WORKDIR /opt/pyspider

# When use pip in China download is too slow so recommed use https://pypi.tuna.tsinghua.edu.cn/simple
# RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -e .[all]
RUN pip install -e .[all]

# install puppeteer、koa、koa-bodyparser、request

# if you are in China recommend run cnpm in China
# RUN cd /opt/pyspider/pyspider/fetcher \
#         && cnpm install puppeteer@1.6.2 \
#         && cnpm install koa \
#         && cnpm install koa-bodyparser \
#         && cnpm install request

RUN cd /opt/pyspider/pyspider/fetcher \
        && npm install puppeteer@1.6.2 \
        && npm install koa \
        && npm install koa-bodyparser \
        && npm install request

RUN apt-get update \
        && apt-get install -y gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils wget 


VOLUME ["/opt/pyspider"]
ENTRYPOINT ["pyspider"]

EXPOSE 5000 23333 24444 25555 22222
