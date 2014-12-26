```shell
# mysql
docker run -d --name mysql dockerfile/mysql:latest
# rabbitmq
docker run -d --name rabbitmq dockerfile/rabbitmq:latest
# phantomjs
docker run --name phantomjs -d -v `pwd`:/mnt/test --expose 25555 cmfatih/phantomjs:latest /usr/bin/phantomjs /mnt/test/pyspider/fetcher/phantomjs_fetcher.js 25555

# scheduler
docker run -d --name scheduler --link mysql:mysql --link rabbitmq:rabbitmq binux/pyspider:latest scheduler
# fetcher, run multiple instance if needed.
docker run -d --name fetcher --link rabbitmq:rabbitmq --link phantomjs:phantomjs binux/pyspider:latest fetcher
# processor, run multiple instance if needed.
docker run -d --name processor --link mysql:mysql --link rabbitmq:rabbitmq binux/pyspider:latest processor
# webui
docker run -d --name webui -p 5000:5000 --link mysql:mysql --link rabbitmq:rabbitmq --link phantomjs:phantomjs --link scheduler:scheduler binux/pyspider:latest webui
```

or running with [fig](http://www.fig.sh/) with `fig.yml`:

```
mysql:
  image: dockerfile/mysql:latest
rabbitmq:
  image: dockerfile/rabbitmq:latest
phantomjs:
  image: cmfatih/phantomjs:latest
  expose:
    - "25555"
  volumes:
    - .:/mnt/test
  command: /usr/bin/phantomjs /mnt/test/pyspider/fetcher/phantomjs_fetcher.js 25555
scheduler:
  image: binux/pyspider:latest
  links:
    - mysql
    - rabbitmq
  command: scheduler
fetcher:
  image: binux/pyspider:latest
  links:
    - rabbitmq
    - phantomjs
  command : fetcher
processor:
  image: binux/pyspider:latest
  links:
    - mysql
    - rabbitmq
  command: processor
webui:
  image: binux/pyspider:latest
  links:
    - mysql
    - rabbitmq
    - scheduler
    - phantomjs
  volumes:
    - .:/opt/pyspider
  command: webui
  ports:
    - "5000:5000"
```

`fig up`
