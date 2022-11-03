# FIXME: this check will break in 3.11 or 3.12 if I recall correctly
assert __package__, "Please, run me as a module"

import argparse
import asyncio
import json
import logging
import os

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
with open(CONFIG_DIR / f"{args.NAME}.json") as f:
    # TODO: switch to TOML when 3.11 comes out?
    parsed_config = json.load(f)


async def main():
    # TODO: add `count`
    await Job(name=args.NAME, **parsed_config).do()


asyncio.run(main())
