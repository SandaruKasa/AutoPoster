import datetime
import pathlib
import sqlite3

import autoposter.jobs


class SelfMaintainedConnection:
    def __init__(self, connector, credentials):
        self._connector = connector
        self._credentials = credentials
        self._connection = None
        self._cursor = None

    def __enter__(self):
        self._connection = self._connector(**self._credentials)
        self._cursor = self._connection.cursor()
        return self._cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                self._connection.commit()
            else:
                try:
                    self._connection.rollback()
                except:
                    pass
        finally:
            self._cursor.close()
            self._connection.close()


# Yep, a singleton
connection = None


def init(sql_credentials) -> None:
    global connection
    connection = SelfMaintainedConnection(
        connector=sqlite3.connect,
        credentials=sql_credentials,
    )
    with connection as cursor:
        cursor.executescript("""
CREATE TABLE IF NOT EXISTS BotInfo
(
    `telegram_id` INTEGER NOT NULL PRIMARY KEY,
    `token`       TEXT    NOT NULL,
    `alias`       TEXT    NULL
);
CREATE TABLE IF NOT EXISTS Jobs_Pictures
(
    `local_id`        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    `target`          TEXT    NOT NULL,
    `worker`          INTEGER NOT NULL,
    `source`          TEXT    NOT NULL,
    `archive`         TEXT    NULL,
    `target_time`     TIME    NOT NULL,
    `weekday_bitmask` INTEGER NOT NULL DEFAULT 127,
    `multiple`        INTEGER NOT NULL DEFAULT 1,
    `post_highres`    BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (`worker`) REFERENCES BotInfo (`telegram_id`)
);
""")


def get_all_jobs() -> list[autoposter.jobs.Job]:
    jobs = []
    with connection as cursor:
        cursor.execute("""
SELECT `target`, `worker`, `source`, `archive`, `target_time`, `weekday_bitmask`, `multiple`, `post_highres`
FROM `Jobs_Pictures`
""")
        for (
                target, worker, source, archive, target_time, weekday_bitmask, multiple, post_highres
        ) in cursor.fetchall():
            try:
                target = int(target)
            except ValueError:
                pass
            jobs.append(autoposter.jobs.PicturePostingJob(
                target_chat=target,
                worker_id=worker,
                source=pathlib.Path(source),
                archive=None if archive is None else pathlib.Path(archive),
                target_time=datetime.time.fromisoformat(target_time),
                weekdays=tuple(i for i in range(7) if weekday_bitmask & (1 << i)),
                multiple=multiple,
                post_highres=bool(post_highres)
            ))
    return jobs
