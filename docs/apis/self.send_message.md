self.send_message
=================

self.send_message(project, msg, [url])
--------------------------------------
send messages to other project. can been received by `def on_message(self, project, message)` callback.

- `project` - other project name
- `msg` - any json-able object
- `url` - result will been overwrite if have same `taskid`. `send_message` share a same `taskid` by default. Change this to return multiple result by one response.

```python
def detail_page(self, response):
    for i, each in enumerate(response.json['products']):
        self.send_message(self.project_name, {
                "name": each['name'],
                'price': each['prices'],
             }, url="%s#%s" % (response.url, i))

def on_message(self, project, msg):
    return msg
``` 

pyspider send_message [OPTIONS] PROJECT MESSAGE
-----------------------------------------------

You can also send message from command line.

```
Usage: pyspider send_message [OPTIONS] PROJECT MESSAGE

  Send Message to project from command line

Options:
  --scheduler-rpc TEXT  xmlrpc path of scheduler
  --help                Show this message and exit.
```

def on_message(self, project, message)
--------------------------------------
receive message from other project
