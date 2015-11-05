import platform

if platform.system() == 'Darwin':
    from pyspider.libs import base_queue as Queue
else:
    from six.moves import queue as Queue
