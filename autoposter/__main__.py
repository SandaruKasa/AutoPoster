# FIXME: this check will break in 3.11 or 3.12 if I recall correctly
assert __package__, "Please, run me as a module"

import argparse
import asyncio
import json

from . import CONFIG_DIR, jobs

# TODO: logging


# TODO: move `count` downstream
async def main(**job_kwargs):
    cls = jobs.get_cls(job_kwargs.pop("type"))
    count = int(job_kwargs.pop("count", 1))
    job = cls(**job_kwargs)
    async with job:
        for _ in range(count):
            await job.do()


parser = argparse.ArgumentParser(prog="autoposter")
parser.add_argument("NAME")
args = parser.parse_args()
with open(CONFIG_DIR / f"{args.NAME}.json") as f:
    # TODO: switch to TOML when 3.11 comes out?
    parsed_config = json.load(f)


asyncio.run(main(name=args.NAME, **parsed_config))
