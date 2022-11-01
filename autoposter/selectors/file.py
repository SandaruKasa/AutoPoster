import random
import shutil
from pathlib import Path

from . import Selector


class FileSelector(Selector[Path]):
    source: Path
    random: bool = True
    delete_posted: bool = False
    _POSTED_PREFIX: str = "posted_"  # static (in a Java sense) field

    def choose(self) -> None | Path:
        self.source.mkdir(parents=True, exist_ok=True)
        assert self.source.is_dir()
        candidates = tuple(
            path
            for path in self.source.iterdir()
            if not path.name.startswith(FileSelector._POSTED_PREFIX)
        )
        if not candidates:
            return None
        elif self.random:
            return random.choice(candidates)
        else:
            return sorted(candidates)[0]

    def dispose(self, contents: Path):
        if self.delete_posted:
            shutil.rmtree(contents)
        else:
            # TODO: prevent collisions or something
            contents.rename(
                contents.with_name(FileSelector._POSTED_PREFIX + contents.name)
            )
