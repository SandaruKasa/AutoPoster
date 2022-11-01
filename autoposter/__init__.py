import logging
import os
from pathlib import Path

import pydantic

from .posters import Poster
from .selectors import Selector

CONFIG_DIR: Path = Path(os.getenv("CONFIG_DIR", "conf.d")).absolute()
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


class Job(pydantic.BaseModel):
    name: str
    selector: Selector
    poster: Poster

    @pydantic.validator("poster", pre=True)
    def _propagate_name(cls, field_kwargs: dict, values: dict):
        return {"name": values["name"], **field_kwargs}

    async def do(self):
        logging.getLogger(self.name).critical(self.dict())
        contents = self.selector.choose()
        try:
            async with self.poster:
                if contents is None:
                    await self.poster.on_no_candidates()
                else:
                    await self.poster.post(contents)
                    self.selector.dispose(contents)
        except:
            self.poster.logger.error("Error posting", exc_info=True)
            raise
