# FIXME: this check will break in 3.12 if I recall correctly
assert __package__, "Please, run me as a module"

import argparse
import asyncio
import logging
import os
import tomllib

from . import CONFIG_DIR, Job

logging.basicConfig(
    handlers=[logging.StreamHandler()],
    level=os.getenv("LOGLEVEL", "INFO").upper(),
    format="[%(asctime)s.%(msecs)03d] [%(name)s] [%(levelname)s]: %(message)s",
    datefmt=r"%Y-%m-%dT%H-%M-%S",
)

parser = argparse.ArgumentParser(prog="autoposter")
parser.add_argument("NAME")
args = parser.parse_args()
with open(CONFIG_DIR / f"{args.NAME}.toml", "rb") as f:
    parsed_config: dict = tomllib.load(f)
    parsed_config.setdefault("name", args.NAME)


async def main():
    job = Job(**parsed_config)
    await job.do()


asyncio.run(main())
