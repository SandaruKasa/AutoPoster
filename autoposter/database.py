import datetime

import autoposter.jobs


# todo: database

def get_all_jobs() -> list[autoposter.jobs.Job]:
    return [
        autoposter.jobs.PicturePostingJob(
            target_chat="@TestChannel",
            target_time=datetime.time(hour=19, minute=20),
            source="test-source",
            worker_id=1337,
        ),
    ]
