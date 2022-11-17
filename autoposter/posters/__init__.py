import abc
import logging
import typing

from ..types import Post, SubclassedModel


class Poster(SubclassedModel, abc.ABC):
    @classmethod
    def _get_subclass(cls, name: str) -> typing.Type["Poster"] | None:
        match name.lower():
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
