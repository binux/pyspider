Script Environment
==================

Variables
---------
* `self.project_name`
* `self.project` information about current project
* `self.response`
* `self.task`

About Script
------------
* The name of `Handler` is not matters, but you need at least one class inherit from `BaseHandler`
* A third parameter can be set to get task object: `def callback(self, response, task)`
* Non-200 response will not submit to callback by default. Use `@catch_status_code_error` 

About Environment
-----------------
* `logging`, `print` and exceptions will be captured.
* You can import other projects as module with `from projects import some_project`

### Web view

* view the page as a browser would render (approximately)

### HTML view

* view the HTML of the current callback (index_page, detail_page, etc.)

### Follows view

* view the callbacks that can be made from the current callback
* index_page follows view will show the detail_page callbacks that can be executed.

### Messages view

* shows the messages send by [`self.send_message`](apis/self.send_message) API.

### Enable CSS Selector Helper

* Enable a CSS Selector Helper of the Web view. It gets the CSS Selector of the element you clicked then add it to your script.
