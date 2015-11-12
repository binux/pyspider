Frequently Asked Questions
==========================

Does pyspider Work with Windows?
--------------------------------
Yes, it should, some users have made it work on Windows. But as I don't have windows development environment, I cannot test. Only some tips for users who want to use pyspider on Windows:

- Some package needs binary libs (e.g. pycurl, lxml), that maybe you cannot install it from pip, Windowns binaries packages could be found in [http://www.lfd.uci.edu/~gohlke/pythonlibs/](http://www.lfd.uci.edu/~gohlke/pythonlibs/).
- Make a clean environment with [virtualenv](https://virtualenv.readthedocs.org/en/latest/)
- Try 32bit version of Python, especially your are facing crash issue.
- Avoid using Python 3.4.1 ([#194](https://github.com/binux/pyspider/issues/194), [#217](https://github.com/binux/pyspider/issues/217))

Unreadable Code (乱码) Returned from Phantomjs
---------------------------------------------

Phantomjs doesn't support gzip, don't set `Accept-Encoding` header with `gzip`.


How to Delete a Project?
------------------------

set `group` to `delete` and `status` to `STOP` then wait 24 hours. You can change the time before a project deleted via `scheduler.DELETE_TIME`.

How to Restart a Project?
-------------------------
#### Why
It happens after you modified a script, and wants to crawl everything again with new strategy. But as the [age](/apis/self.crawl/#age) of urls are not expired. Scheduler will discard all of the new requests.

#### Solution
1. Create a new project.
2. Using a [itag](/apis/self.crawl/#itag) within `Handler.crawl_config` to specify the version of your script.

How to Use WebDAV Mode?
-----------------------
Mount `http://hostname/dav/` to your filesystem, edit or create scripts with your favourite editor.

> OSX: `mount_webdav http://hostname/dav/ /Volumes/dav`  
> Linux: Install davfs2, `mount.davfs http://hostname/dav/ /mnt/dav`  
> VIM: `vim dav://hostname/dav/script_name.py`

When you are editing script without WebUI, you need to change it to `WebDAV Mode` while debugging. After you saved script in editor, WebUI can load and use latest script to debug your code.

What does the progress bar mean on the dashboard?
-------------------------------------------------
When mouse move onto the progress bar, you can see the explaintions.

For 5m, 1h, 1d the number are the events triggered in 5m, 1h, 1d. For all progress bar, they are the number of total tasks in correspond status.

Only the tasks in DEBUG/RUNNING status will show the progress.
