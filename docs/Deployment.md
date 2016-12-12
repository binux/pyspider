Deployment
===========

Since pyspider has various components, you can just run `pyspider` to start a standalone and third service free instance. Or using MySQL or MongoDB and RabbitMQ to deploy a distributed crawl cluster.

To deploy pyspider in product environment, running component in each process and store data in database service is more reliable and flexible.

Installation
------------

To deploy pyspider components in each single processes, you need at least one database service. pyspider now supports [MySQL](http://www.mysql.com/), [MongoDB](http://www.mongodb.org/) and [PostgreSQL](http://www.postgresql.org/). You can choose one of them.

And you need a message queue service to connect the components together. You can use [RabbitMQ](http://www.rabbitmq.com/), [Beanstalk](http://kr.github.io/beanstalkd/) or [Redis](http://redis.io/) as message queue.

`pip install --allow-all-external pyspider[all]`

> Even if you had install pyspider using `pip` before. Install with `pyspider[all]` is necessary to install the requirements for MySQL/MongoDB/RabbitMQ.

if you are using Ubuntu, try:
```
apt-get install python python-dev python-distribute python-pip libcurl4-openssl-dev libxml2-dev libxslt1-dev python-lxml
```
to install binary packages.

Deployment
----------

**This document is based on MySQL + RabbitMQ**

### config.json

Although you can use command-line to specify the parameters. A config file is a better choice.

```
{
  "taskdb": "mysql+taskdb://username:password@host:port/taskdb",
  "projectdb": "mysql+projectdb://username:password@host:port/projectdb",
  "resultdb": "mysql+resultdb://username:password@host:port/resultdb",
  "message_queue": "amqp://username:password@host:port/%2F",
  "webui": {
    "username": "some_name",
    "password": "some_passwd",
    "need-auth": true
  }
}
```

you can get complete options by running `pyspider --help` and `pyspider webui --help` for subcommands. `"webui"` in JSON  is configs for subcommands. You can add parameters for other components similar to this one.

#### Database Connection URI
`"taskdb"`, `"projectdb”`, `"resultdb"` is using database connection URI with format below:

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
    more: http://docs.mongodb.org/manual/reference/connection-string/
sqlalchemy:
    sqlalchemy+postgresql+type://user:passwd@host:port/database
    sqlalchemy+mysql+mysqlconnector+type://user:passwd@host:port/database
    more: http://docs.sqlalchemy.org/en/rel_0_9/core/engines.html
local:
    local+projectdb://filepath,filepath
    
type:
    should be one of `taskdb`, `projectdb`, `resultdb`.
```

#### Message Queue URL
You can use connection URL to specify the message queue:

```
rabbitmq:
    amqp://username:password@host:5672/%2F
    Refer: https://www.rabbitmq.com/uri-spec.html
beanstalk:
    beanstalk://host:11300/
redis:
    redis://host:6379/db
builtin:
    None
```

> Hint for postgresql: you need to create database with encoding utf8 by your own. pyspider will not create database for you.

running
-------

You should run components alone with subcommands. You may add `&` after command to make it running in background and use [screen](http://linux.die.net/man/1/screen) or [nohup](http://linux.die.net/man/1/nohup) to prevent exit after your ssh session ends. **It's recommended to manage components with [Supervisor](http://supervisord.org/).**

```
# start **only one** scheduler instance
pyspider -c config.json scheduler

# phantomjs
pyspider -c config.json phantomjs

# start fetcher / processor / result_worker instances as many as your needs
pyspider -c config.json --phantomjs-proxy="localhost:25555" fetcher
pyspider -c config.json processor
pyspider -c config.json result_worker

# start webui, set `--scheduler-rpc` if scheduler is not running on the same host as webui
pyspider -c config.json webui
```

Running with Docker
-------------------
[Running pyspider with Docker](Running-pyspider-with-Docker)


Deployment of demo.pyspider.org
-------------------------------
[Deployment of demo.pyspider.org](Deployment-demo.pyspider.org)

