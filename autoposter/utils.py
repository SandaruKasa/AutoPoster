import abc
import typing

import pydantic


class SubclassedModel(pydantic.BaseModel, abc.ABC):
    @classmethod
    def __get_validators__(cls):
        yield cls._construct_as_subclass

    @classmethod
    # IDK how to type-annotate this
    # Should be something like `-> TypeVar("X", bound=cls)`, but Python can't do that
    def _construct_as_subclass(cls, kwargs: dict):
        try:
            subcls_name = kwargs.pop("type")
        except KeyError:
            raise ValueError(f"{cls.__name__}({kwargs}) is missing a `type` field")

        subcls = cls._get_subclass(subcls_name)
        if subcls is None:
            raise ValueError(f"Unknown {cls.__name__} type: {subcls_name}")
        return subcls(**kwargs)

    @classmethod
    @abc.abstractmethod
    # TODO: replace with `-> Type[Self]` when 3.11 comes out
    def _get_subclass(cls, name: str) -> typing.Type["SubclassedModel"] | None:
        pass
