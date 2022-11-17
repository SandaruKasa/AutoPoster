import abc
import logging
import asyncio
import typing

from ..types import Post, SubclassedModel


class Poster(SubclassedModel, abc.ABC):
    @classmethod
    def _get_subclass(cls, name: str) -> typing.Type["Poster"] | None:
        match name.lower():
            case "multi":
                return MultiPoster

            case "telegram":
                from .telegram import TelegramPoster

                return TelegramPoster

            case "telegram_highres" | "telegram-highres" | "highres":
                from .telegram_highres import TelegramHighresPoster

                return TelegramHighresPoster

        return None

    name: str

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.name)

    @abc.abstractmethod
    async def post(self, selected: Post):
        pass

    @abc.abstractmethod
    async def __aenter__(self):
        pass

    @abc.abstractmethod
    async def __aexit__(self, *args):
        pass

    async def on_no_candidates(self):
        self.logger.warn("No more posts!")


class MultiPoster(Poster):
    posters: list[Poster]

    async def post(self, selected: Post):
        return await asyncio.gather(*(poster.post(selected) for poster in self.posters))

    async def __aenter__(self):
        return await asyncio.gather(*(poster.__aenter__() for poster in self.posters))

    async def __aexit__(self, *args):
        return await asyncio.gather(
            *(poster.__aexit__(*args) for poster in self.posters)
        )

    async def on_no_candidates(self):
        return await asyncio.gather(
            *(poster.on_no_candidates() for poster in self.posters)
        )
