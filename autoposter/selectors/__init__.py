import abc
import typing

from ..utils import SubclassedModel

T = typing.TypeVar("T")


class Selector(typing.Generic[T], SubclassedModel, abc.ABC):
    @classmethod
    # TODO: replace with `-> Type[Self]` when 3.11 comes out
    def _get_subclass(cls, name: str) -> typing.Type["Selector"] | None:
        match name.lower():
            case "file":
                from .file import FileSelector

                return FileSelector
        return None

    @abc.abstractmethod
    def choose(self) -> T | None:
        pass

    @abc.abstractmethod
    def dispose(self, contents: T):
        pass
