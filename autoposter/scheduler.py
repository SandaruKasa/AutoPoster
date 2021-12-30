import logging

from apscheduler.schedulers.background import BackgroundScheduler

import autoposter.jobs

# Yep, a singleton
_scheduler = BackgroundScheduler()


def _execute_job(job: autoposter.jobs.Job) -> None:
    try:
        job.execute()
    except BaseException as e:
        logging.getLogger("JOB_EXECUTION").error("Job: %s, error: %s", job, e)


def add(job: autoposter.jobs.Job) -> None:
    params = job.get_scheduler_arguments()
    if params is None:
        params = {}
    params.update({
        "func": _execute_job,
        "args": (job,),
        "kwargs": dict(),
    })
    _scheduler.add_job(**params)


def start() -> None:
    _scheduler.start()


def stop() -> None:
    _scheduler.shutdown()
