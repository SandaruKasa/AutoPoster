import abc
import logging
import typing

from ..utils import SubclassedModel

T = typing.TypeVar("T")


class Poster(typing.Generic[T], SubclassedModel, abc.ABC):
    @classmethod
    def _get_subclass(cls, name: str) -> typing.Type["Poster"] | None:
        match name.lower():
            case "telegram":
                from .telegram import TelegramPoster

                return TelegramPoster

        return None

    name: str

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.name)

    @abc.abstractmethod
    async def post(self, selected: T):
        pass

    @abc.abstractmethod
    async def __aenter__(self):
        pass

    @abc.abstractmethod
    async def __aexit__(self, *args):
        pass

    async def on_no_candidates(self):
        self.logger.warn("No more posts!")


# lazy imports, kinda
def get_cls(name: str) -> typing.Type[Poster]:
    match name.lower():
        case "telegram":
            from .telegram import TelegramPoster

            return TelegramPoster
        case unknown:
            raise ValueError(f"Unknown job type: {unknown!r}")
