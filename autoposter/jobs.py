import dataclasses
from abc import ABC, abstractmethod

import pyrogram


@dataclasses.dataclass
class Job(ABC):
    credentials: dict = dataclasses.field(repr=False)

    def __post_init__(self):
        self._authorize()

    @abstractmethod
    def _authorize(self):
        pass

    @abstractmethod
    async def do(self):
        pass


@dataclasses.dataclass
class PyrogramJob(Job):
    chat_id: int | str
    post_highres: bool = False
    client: pyrogram.client.Client = dataclasses.field(init=False)

    def _authorize(self):
        self.client = pyrogram.client.Client(**self.credentials, no_updates=True)

    async def do(self):
        async with self.client:
            # TODO: actual functionality, lol
            await self.client.send_message("me", "Hello, world!")
