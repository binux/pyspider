About Projects
==============

In most cases, a project is one script you write for one website.

* Projects are independent, but you can import another project as a module with `from projects import other_project`
* A project has 5 status: `TODO`, `STOP`, `CHECKING`, `DEBUG` and `RUNNING`
    - `TODO` - a script is just created to be written
    - `STOP` - you can mark a project as `STOP` if you want it to STOP (= =).
    - `CHECKING` - when a running project is modified, to prevent incomplete modification, project status will be set as `CHECKING` automatically.
    - `DEBUG`/`RUNNING` - these two status have no difference to spider. But it's good to mark it as `DEBUG` when it's running the first time then change it to `RUNNING` after being checked.
* The crawl rate is controlled by `rate` and `burst` with [token-bucket](http://en.wikipedia.org/wiki/Token_bucket) algorithm.
    - `rate` - how many requests in one second
    - `burst` - consider this situation, `rate/burst = 0.1/3`, it means that the spider scrawls 1 page every 10 seconds. All tasks are finished, project is checking last updated items every minute. Assume that 3 new items are found, pyspider will "burst" and crawl 3 tasks without waiting 3*10 seconds. However, the fourth task needs wait 10 seconds.
* To delete a project, set `group` to `delete` and status to `STOP`, wait 24 hours.


`on_finished` callback
--------------------
You can override `on_finished` method in the project, the method would be triggered when the task_queue goes to 0.

Example 1: When you start a project to crawl a website with 100 pages, the `on_finished` callback will be fired when 100 pages are successfully crawled or failed after retries.

Example 2: A project with `auto_recrawl` tasks will **NEVER** trigger the `on_finished` callback, because time queue will never become 0 when there are auto_recrawl tasks in it.

Example 3: A project with `@every` decorated method will trigger the `on_finished` callback every time when the newly submitted tasks are finished.
