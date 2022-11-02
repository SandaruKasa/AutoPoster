from pathlib import Path

import pydantic
import pyrogram

from ..types import Media, MediaType, Post
from . import Poster


class TelegramPoster(Poster):
    class Config:
        arbitrary_types_allowed = True

    client: pyrogram.client.Client = pydantic.Field(alias="credentials")

    # TODO: use a subdir?
    _SESSIONS_DIR: Path = Path.cwd()

    @pydantic.validator("client", pre=True)
    def _make_client(cls, credentials: dict, values: dict) -> pyrogram.client.Client:
        return pyrogram.client.Client(
            name=values["name"],
            workdir=str(TelegramPoster._SESSIONS_DIR),
            **credentials,
            no_updates=True,
        )

    async def post(self, contents: Post):
        # TODO: implement me
        raise NotImplementedError(contents)

    async def __aenter__(self):
        return await self.client.__aenter__()

    async def __aexit__(self, *args):
        return await self.client.__aexit__(*args)
