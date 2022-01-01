# todo: Telegram stuff
import telegram

_workers = {}


def get_worker(worker_id: int) -> telegram.Bot:
    result = _workers.get(worker_id)
    if result is None:
        pass  # todo: get from database and init
    return result


def stop_all() -> None:
    pass  # todo
