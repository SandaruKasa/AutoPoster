import threading

shutdown_event = threading.Event()


# https://en.wikipedia.org/wiki/Dining_philosophers_problem#Arbitrator_solution
class Arbitrator:
    _lock = threading.Lock()

    def __init__(self, *locks: threading.Lock):
        self.locks = locks

    def __enter__(self) -> None:
        with self._lock:
            for lock in self.locks:
                lock.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        for lock in self.locks:
            lock.release()


# todo: maybe TTL
_chat_pool = dict()


def get_chat_lock(chat_id: int) -> threading.Lock:
    return _chat_pool.setdefault(chat_id, threading.Lock())
