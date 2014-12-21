About Tasks
===========

tasks are the basic unit to been scheduled.

Basis
-----

* A task is differentiate by `taskid` which is `md5(url)` by default.
* Tasks are isolated between different projects.
* Task has four status:
    - active
    - failed
    - success
    - bad - not used
* Only tasks in active status will scheduled. Tasks scheduled by `exetime` and `priority`

Schedule
--------
when a new task comes:
* it will been putted into queued and sorted with `exetime` and `priority`.

when a crawled task comes:
* if it is in `active` status(in queue), it will been ignored. Unless `force_update`.
* if it is finished(success or failed) task arrive, it will been re-crawled and rescheduled if `last_crawl_time + age < now` or `itag` now equal to the its last value.
