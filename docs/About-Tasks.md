About Tasks
===========

tasks are the basic unit to been scheduled.

Basis
-----

* A task is differentiated by `taskid`. (Default: `md5(url)`, can be changed by override the `def get_taskid(self, task)` method)
* Tasks are isolated between different projects.
* Task has 4 status:
    - active
    - failed
    - success
    - bad - not used
* Only tasks in active status will be scheduled.
* Tasks are served in order of `priority`.

Schedule
--------

When a new task(have not seen before) comes:

* If `exetime` is set but not arrived. It will be putted into a time-based queue to wait.
* Otherwise it will be accepted.

When the task is already in the queue:

* Ignored unless `force_update`

When a completed task comes:

* If `age` is set, `last_crawl_time + age < now` it will be accepted. Otherwise discarded.
* If `itag` is set and not equal to it's previous value, it will be accepted. Otherwise discarded.