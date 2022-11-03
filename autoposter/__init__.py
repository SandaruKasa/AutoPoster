import logging
import os
import random
import shutil
from pathlib import Path

import pydantic

from .posters import Poster
from .types import Media, MediaType, Post, SortBy

CONFIG_DIR: Path = Path(os.getenv("CONFIG_DIR", "conf.d")).absolute()
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

random.seed()


class Selector(pydantic.BaseModel):
    source: Path
    sort_by: SortBy
    delete_posted: bool = False
    _POSTED_PREFIX: str = "posted_"  # static (in a Java sense) field

    def choose(self, n: int) -> list[Post]:
        assert n > 0
        self.source.mkdir(parents=True, exist_ok=True)
        assert self.source.is_dir()
        candidates = [
            path
            for path in self.source.iterdir()
            if not path.name.startswith(Selector._POSTED_PREFIX)
        ]
        return [
            self._construct_post(candidate)
            for candidate in (
                self._sort(candidates)[:n]
            )  # can be done more efficiently with sort_n
        ]

    # TODO: make classmethod, pass SortBy as argument,
    #       use different sorting for choosing a post
    #       and ordering media inside a post
    def _sort(self, files: list[Path]) -> list[Path]:
        match self.sort_by:
            case SortBy.FILENAME:
                return sorted(files)
            case SortBy.CTIME:
                return sorted(files, key=os.path.getctime)
            case SortBy.MTIME:
                return sorted(files, key=os.path.getmtime)
            case SortBy.RANDOM:
                random.shuffle(files)
                return files

    def _construct_post(self, source: Path) -> Post:
        if source.is_dir():
            files = list(source.iterdir())
        else:
            files = [source]
        assert all(p.is_file() for p in files)
        caption = ""
        media = []
        for file in self._sort(files):
            x = self._fetch_from_file(file)
            if isinstance(x, str):
                if caption:
                    caption += "\n\n"
                caption += x
            else:
                media.append(x)
        return Post(source, media, caption)

    def _fetch_from_file(self, file: Path) -> Media | str:
        assert file.is_file()
        match file.suffix.lower():
            case ".txt":
                with open(file) as f:
                    return f.read()
            case ".png" | ".jpeg" | ".jpg":
                return Media(file, MediaType.IMAGE)
            case ".mp4":
                return Media(file, MediaType.VIDEO)
            case ".gif":
                return Media(file, MediaType.VIDEO)
            case _:
                return Media(file, MediaType.DOCUMENT)

    def dispose(self, contents: Post):
        p = contents._source
        if self.delete_posted:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
        else:
            # TODO: prevent collisions or something
            p.rename(p.with_name(Selector._POSTED_PREFIX + p.name))


class Job(pydantic.BaseModel):
    name: str
    count: int = 1
    selector: Selector
    poster: Poster

    @pydantic.validator("poster", pre=True)
    def _propagate_name(cls, field_kwargs: dict, values: dict):
        return {"name": values["name"], **field_kwargs}

    async def do(self):
        logging.getLogger(self.name).debug(f"Job parsed: {self.dict()}")
        try:
            posts = self.selector.choose(self.count)
            async with self.poster:
                for post in posts:
                    await self.poster.post(post)
                    self.selector.dispose(post)
            if len(posts) < self.count:
                await self.poster.on_no_candidates()
        except Exception as e:
            self.poster.logger.error("Error posting: %s", str(e), exc_info=True)
            raise
