import platform

if platform.system() == 'Darwin':
    from pyspider.libs import base_queue as Queue
    from pyspider.libs.base_queue import get_multiprocessing_queue as get_queue
else:
    from six.moves import queue as Queue
    from multiprocessing import Queue as get_queue
