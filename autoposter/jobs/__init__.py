import datetime
import json
import pathlib
from abc import abstractmethod
from typing import Union, Optional


class Job:
    def __init__(self):
        pass

    @abstractmethod
    def get_scheduler_arguments(self) -> Optional[dict]:
        pass

    @abstractmethod
    def execute(self) -> None:
        pass


class PicturePostingJob(Job):
    def __init__(
            self,
            target_chat: Union[str, int],
            worker_id: int,
            target_time: datetime.time,
            source: Union[pathlib.Path, str],
            archive: Optional[Union[pathlib.Path, str]] = None,
            weekdays=tuple(range(7)),
    ):
        super().__init__()
        self.target_chat = target_chat
        self.worker_id = worker_id
        self.target_time = target_time
        if isinstance(source, str):
            source = pathlib.Path(source)
        self.source = source.resolve()
        self.source.mkdir(exist_ok=True)
        if archive is None:
            # isn't a completely bullshit-proof way to deal with symlinks and stuff, but good enough for this bot
            if source.name in (".", ".."):
                source = source.resolve()
            archive = source.with_name(f"{self.source.name}-posted")
        elif isinstance(archive, str):
            archive = pathlib.Path(archive)
        self.archive = archive.resolve()
        self.archive.mkdir(exist_ok=True)
        self.weekdays = weekdays

    def __repr__(self) -> str:
        return repr(str(self))

    def __str__(self) -> str:
        return json.dumps(
            {
                "target_chat": self.target_chat,
                "worker_id": self.worker_id,
                "target_time": str(self.target_time),
                "source": str(self.source),
                "archive": str(self.archive),
                "weekdays": self.weekdays,
            },
            ensure_ascii=False,
        )

    def get_scheduler_arguments(self) -> Optional[dict]:
        pass  # todo

    def execute(self) -> None:
        pass  # todo
