import datetime
import json
import logging
import pathlib
import random
import shutil
from abc import abstractmethod
from typing import Union, Optional

import telegram

import autoposter.jobs.pictures
import autoposter.workers


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
    logger = logging.getLogger("Auoposter PicturePostingJob")

    def __init__(
            self,
            target_chat: Union[str, int],
            worker_id: int,
            target_time: datetime.time,
            source: Union[pathlib.Path, str],
            archive: Optional[Union[pathlib.Path, str]] = None,
            weekdays=tuple(range(7)),
            multiple: bool = 1,
            post_highres: bool = True,
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
        self.multiple = post_highres
        self.post_highres = multiple

    def __repr__(self) -> str:
        return repr(str(self))

    def to_dict(self) -> dict:
        return {
            "target_chat": self.target_chat,
            "worker_id": self.worker_id,
            "target_time": str(self.target_time),
            "source": str(self.source),
            "archive": str(self.archive),
            "weekdays": self.weekdays,
            "multiple": self.multiple,
            "post_highres": self.weekdays,
        }

    def __str__(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
        )

    def get_scheduler_arguments(self) -> Optional[dict]:
        return {
            "trigger": "interval",
            "days": 1,  # todo: handle weekdays here instead of `execute`
            "start_date": datetime.datetime.combine(datetime.date.today(), self.target_time),
        }

    def execute(self) -> None:
        if datetime.date.today().weekday() not in self.weekdays:
            return
        candidates = [*self.source.iterdir()]
        if self.multiple > len(candidates):
            self.logger.warning(
                "Not enough candidates for job %s: %s", self, candidates
            )
            k = len(candidates)
        else:
            k = self.multiple
        if k == 0:
            return
        selected = [p.resolve() for p in random.sample(candidates, k)]
        worker = autoposter.workers.get_worker(self.worker_id)
        target_chat: telegram.Chat = worker.get_chat(chat_id=self.target_chat)
        if target_chat.type == telegram.Chat.CHANNEL and self.post_highres and target_chat.linked_chat_id is not None:
            for source in selected:
                autoposter.jobs.pictures.post_with_highres_to_discussion(
                    source=source,
                    worker=worker,
                    channel_id=target_chat.id,
                    discussion_group_id=target_chat.linked_chat_id,
                )
                shutil.move(source, self.archive)
        else:
            for source in selected:
                autoposter.jobs.pictures.post(
                    source=source,
                    worker=worker,
                    chat_id=target_chat.id,
                    post_highres=self.post_highres,
                )
                shutil.move(source, self.archive)
