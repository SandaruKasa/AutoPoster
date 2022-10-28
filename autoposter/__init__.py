import logging
import os
from pathlib import Path

from . import jobs

logging.basicConfig(
    handlers=[logging.StreamHandler()],
    level=os.getenv("LOGLEVEL", "INFO").upper(),
    format="[%(asctime)s.%(msecs)03d] [%(name)s] [%(levelname)s]: %(message)s",
    datefmt=r"%Y-%m-%dT%H-%M-%S",
)

CONFIG_DIR: Path = Path(os.getenv("CONFIG_DIR", "conf.d")).absolute()
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
