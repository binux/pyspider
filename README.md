pyspider [![Build Status](https://travis-ci.org/binux/pyspider.png?branch=master)](https://travis-ci.org/binux/pyspider)
========

most powerful spider system in python!

![debug demo](http://f.binux.me/debug_demo.png)
demo code: [gist:9424801](https://gist.github.com/binux/9424801)

Installation
============

* python2.7
* `pip install -r requirements.txt`
* `./run.py` , visit [http://localhost:5000/](http://localhost:5000/)

Docker
======
build:  
`docker build -t pyspider .`
run:  
```
# mysql
docker run -it -d --name mysql dockerfile/mysql
# rabbitmq
docker run -it -d --name rabbitmq dockerfile/rabbitmq

# scheduler
docker run -it -d --name scheduler --link mysql:mysql --link rabbitmq:rabbitmq pyspider scheduler
# fetcher, run multiple instance if needed.
docker run -it -d --link mysql:mysql --link rabbitmq:rabbitmq pyspider fetcher
# processor, run multiple instance if needed.
docker run -it -d --link mysql:mysql --link rabbitmq:rabbitmq pyspider processor
# webui
docker run -it -d -P 5000:5000 --link mysql:mysql --link rabbitmq:rabbitmq --link scheduler:scheduler pyspider webui
```

Documents
=========

* [Wiki](https://github.com/binux/pyspider/wiki)
* [Quickstart](https://github.com/binux/pyspider/wiki/Quickstart)
* [脚本编写指南](https://github.com/binux/pyspider/wiki/%E8%84%9A%E6%9C%AC%E7%BC%96%E5%86%99%E6%8C%87%E5%8D%97)
* [架构设计](http://blog.binux.me/2014/02/pyspider-architecture/)

Contribute
==========

* 部署使用，提交 bug、特性 [Issue](https://github.com/binux/pyspider/issues)
* 参与 [特性讨论](https://github.com/binux/pyspider/issues?labels=discussion&state=open) 或 [完善文档](https://github.com/binux/pyspider/wiki)
* 我正在进行 [Bugfix and Basic Features](https://github.com/binux/pyspider/issues?milestone=2&state=open) 的第二个里程碑开发。欢迎发 pull request (代码、注释和提交日志请用英文）


License
=======
Licensed under the Apache License, Version 2.0
