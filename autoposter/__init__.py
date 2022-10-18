import logging
import os
from distutils.debug import DEBUG
from pathlib import Path

import apscheduler.schedulers.async_

from . import jobs

logging.basicConfig(
    handlers=[logging.StreamHandler()],
    level=os.getenv("LOGLEVEL", "INFO").upper(),
    format="[%(asctime)s.%(msecs)03d] [%(name)s] [%(levelname)s]: %(message)s",
    datefmt=r"%Y-%m-%dT%H-%M-%S",
)

scheduler = apscheduler.schedulers.async_.AsyncScheduler()

CREDENTIALS_FILE = Path(os.getenv("CREDENTIALS_FILE", "credentials.json"))
JOBS_FILE = Path(os.getenv("JOBS_FILE", "jobs.json"))
DEBUG = os.getenv("DEBUG", None) is not None

JOB_TYPES = {
    "pyrogram": jobs.PyrogramJob,
}
