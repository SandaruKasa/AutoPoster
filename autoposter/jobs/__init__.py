import abc
import logging
import random
import shutil
import typing
from pathlib import Path

import pydantic


class Job(abc.ABC, pydantic.BaseModel):
    name: str

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.name)

    @abc.abstractmethod
    async def do(self):
        pass

    async def __aenter__(self):
        pass

    async def __aexit__(self, exc_type, exc, tb):
        pass


# TODO: decouple selector and poster(s)
class FilePostingJob(Job):
    source: Path
    random: bool = True
    delete_posted: bool = False
    _POSTED_PREFIX: str = "posted_"  # static (in a Java sense) field

    @abc.abstractmethod
    async def post(self, contents: Path):
        pass

    async def do(self):
        contents = self.choose()
        if contents is None:
            await self.on_no_candidates()
        else:
            await self.post(contents)
            self.dispose(contents)

    def choose(self) -> None | Path:
        self.source.mkdir(parents=True, exist_ok=True)
        assert self.source.is_dir()
        candidates = tuple(
            path
            for path in self.source.iterdir()
            if not path.name.startswith(FilePostingJob._POSTED_PREFIX)
        )
        if not candidates:
            return None
        elif self.random:
            return random.choice(candidates)
        else:
            return sorted(candidates)[0]

    async def on_no_candidates(self):
        self.logger.warn("No more posts!")

    def dispose(self, contents: Path):
        if self.delete_posted:
            shutil.rmtree(contents)
        else:
            # TODO: prevent collisions or something
            contents.rename(
                contents.with_name(FilePostingJob._POSTED_PREFIX + contents.name)
            )


# lazy imports, kinda
def get_cls(name: str) -> typing.Type[Job]:
    match name.lower():
        case "telegram":
            from .telegram import TelegramJob

            return TelegramJob
        case unknown:
            raise ValueError(f"Unknown job type: {unknown!r}")
