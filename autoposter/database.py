import datetime

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


def init(sql_connector, sql_credentials) -> None:
    global connection
    connection = SelfMaintainedConnection(
        connector=sql_connector,
        credentials=sql_credentials,
    )
    with connection as cursor:
        # todo: jobs table
        cursor.executescript("""
CREATE TABLE IF NOT EXISTS BotInfo
(
    `telegram_id` INTEGER NOT NULL PRIMARY KEY,
    `token`       TEXT    NOT NULL
);
""")


def get_all_jobs() -> list[autoposter.jobs.Job]:
    # todo: fetch from database
    return [
        autoposter.jobs.PicturePostingJob(
            target_chat="@TestChannel",
            target_time=datetime.time(hour=19, minute=20),
            source="test-source",
            worker_id=1337,
        ),
    ]
