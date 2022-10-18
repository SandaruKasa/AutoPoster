import asyncio
import json
from dataclasses import dataclass

import apscheduler.triggers.cron

from . import *

assert __package__, "Please run this with `python -m`"


@dataclass
class SchedulerEntry:
    job: jobs.Job
    trigger: apscheduler.triggers.cron.CronTrigger


SCHEDULER_ENTRIES: list[SchedulerEntry] = []


with open(CREDENTIALS_FILE) as f:
    CREDENTIALS: dict[str, dict] = json.load(f)

with open(JOBS_FILE) as f:
    JOBS_DATA: list[dict] = json.load(f)


def get_crontabs(job_data: dict) -> list[str]:
    match job_data.get("crontab"), job_data.get("crontabs"):
        case None, [*crontabs]:
            return crontabs
        case crontab, None:
            if crontab is None:  # pleasing mypy
                raise KeyError(
                    'Neither "crontab" nor "crontabs" is specified for job'
                    + json.dumps(job_data)
                )
            else:
                return [crontab]
        case _:
            raise KeyError(
                'Both "crontab" and "crontabs" are specified for job'
                + json.dumps(job_data)
            )


for job_data in JOBS_DATA:
    cls = JOB_TYPES[job_data["type"]]
    params: dict = job_data["params"]

    credentials_name: str | None = job_data["credentials"]
    if credentials_name is not None:
        credentials = CREDENTIALS[credentials_name]
    else:
        credentials = {}

    job = cls(credentials=credentials, **job_data.get("params", {}))

    for crontab in get_crontabs(job_data):
        SCHEDULER_ENTRIES.append(
            SchedulerEntry(
                job=job,
                trigger=apscheduler.triggers.cron.CronTrigger.from_crontab(crontab),
            )
        )


async def fill_and_run_scheduler():
    async with scheduler:
        for entry in SCHEDULER_ENTRIES:
            if DEBUG:
                await scheduler.add_job(entry.job.do)
            else:
                await scheduler.add_schedule(entry.job.do, entry.trigger)

        await scheduler.run_until_stopped()


asyncio.run(fill_and_run_scheduler())
