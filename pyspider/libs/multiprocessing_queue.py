import six
import platform
import multiprocessing
from multiprocessing.queues import Queue as BaseQueue


# The SharedCounter and Queue classes come from:
# https://github.com/vterron/lemon/commit/9ca6b4b

class SharedCounter(object):
    """ A synchronized shared counter.
    The locking done by multiprocessing.Value ensures that only a single
    process or thread may read or write the in-memory ctypes object. However,
    in order to do n += 1, Python performs a read followed by a write, so a
    second process may read the old value before the new one is written by the
    first process. The solution is to use a multiprocessing.Lock to guarantee
    the atomicity of the modifications to Value.
    This class comes almost entirely from Eli Bendersky's blog:
    http://eli.thegreenplace.net/2012/01/04/shared-counter-with-pythons-multiprocessing/
    """

    def __init__(self, n=0):
        self.count = multiprocessing.Value('i', n)

    def increment(self, n=1):
        """ Increment the counter by n (default = 1) """
        with self.count.get_lock():
            self.count.value += n

    @property
    def value(self):
        """ Return the value of the counter """
        return self.count.value


class MultiProcessingQueue(BaseQueue):
    """ A portable implementation of multiprocessing.Queue.
    Because of multithreading / multiprocessing semantics, Queue.qsize() may
    raise the NotImplementedError exception on Unix platforms like Mac OS X
    where sem_getvalue() is not implemented. This subclass addresses this
    problem by using a synchronized shared counter (initialized to zero) and
    increasing / decreasing its value every time the put() and get() methods
    are called, respectively. This not only prevents NotImplementedError from
    being raised, but also allows us to implement a reliable version of both
    qsize() and empty().
    """
    def __init__(self, *args, **kwargs):
        super(MultiProcessingQueue, self).__init__(*args, **kwargs)
        self.size = SharedCounter(0)

    def put(self, *args, **kwargs):
        self.size.increment(1)
        super(MultiProcessingQueue, self).put(*args, **kwargs)

    def get(self, *args, **kwargs):
        v = super(MultiProcessingQueue, self).get(*args, **kwargs)
        self.size.increment(-1)
        return v

    def qsize(self):
        """ Reliable implementation of multiprocessing.Queue.qsize() """
        return self.size.value


if platform.system() == 'Darwin':
    if hasattr(multiprocessing, 'get_context'):  # for py34
        def Queue(maxsize=0):
            return MultiProcessingQueue(maxsize, ctx=multiprocessing.get_context())
    else:
        def Queue(maxsize=0):
            return MultiProcessingQueue(maxsize)
else:
    from multiprocessing import Queue  # flake8: noqa
