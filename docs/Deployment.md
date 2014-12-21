Deployment
===========

Since pyspider supplies various databases and components can be replaced, you can just `./run.py` to start a standalone and no serive dependent instance. Or you can deploy a distributed crawl cluster with mongodb and rabbitmq. Make your choice according to your needs.

Installation
------------
* python 2.6,2.7,3.3,3.4
* `pip install --allow-all-external -r requirements.txt`

if you are using ubuntu, try:
```
apt-get install python python-dev python-distribute python-pip libcurl4-openssl-dev libxml2-dev libxslt1-dev python-lxml
```
to install binary packages.

Deployment
----------

pyspider has 4-5 components(base on your needs), scheduler / fetcher / processor / result_worker / webui, work together and connected by message queue. When you are using `./run.py` it's running in standalone mode which will start each compnents in different subprocesses and connected by python built-in queue.

When you are deploying a production environment. It's better to start each components in their own process, and manage and monitor by things like [Supervisor](http://supervisord.org/). And mysql or mongodb should been used as database backend for better performance, then connect them with rabbitmq.

**This document is base on mysql + rabbitmq**

### config.json
Although you can use command-line to specify the parameters, but a config file is a better choice.

```
{
  "taskdb": "mysql+taskdb://username:password@host:port/taskdb",
  "projectdb": "mysql+projectdb://username:password@host:port/projectdb",
  "resultdb": "mysql+resultdb://username:password@host:port/resultdb",
  "amqp_url": "amqp://username:password@host:port/%2F",
  "fetcher": {
    "xmlrpc": false
  }
}
```

you can find complete options by `./run.py --help` and `./run.py fetcher --help` for subcommand. `"fetcher"` in JSON  is configs for subcommands. You can add parameters for other components similar to this one.

#### Database Connection URI
`"taskdb"`, `"projectdb", `"resultdb"` is using database connection URI with format below:

```
    mysql:
        mysql+type://user:passwd@host:port/database
    sqlite:
        # relative path
        sqlite+type:///path/to/database.db
        # absolute path
        sqlite+type:////path/to/database.db
        # memory database
        sqlite+type://
    mongodb:
        mongodb+type://[username:password@]host1[:port1][,host2[:port2],...[,hostN[:portN]]][/[database][?options]]
```

type may be `taskdb`, `projectdb` and `resultdb`

#### AMPQ URL
refer to: [https://www.rabbitmq.com/uri-spec.html](https://www.rabbitmq.com/uri-spec.html)

### running

```
# phantomjs
phantomjs pyspider/fetcher/phantomjs_fetcher.js 25555
# start **only one** scheduler instance
./run.py -c config.json scheduler
# start fetcher / processor / result_worker instances as many as your needs
./run.py -c config.json --phantomjs-proxy="localhost:25555" fetcher
./run.py -c config.json processor
./run.py -c config.json result_worker
# start webui
./run.py -c config.json webui
```

Running with Docker
-------------------
[Running pyspider with Docker](Running-pyspider-with-Docker)
