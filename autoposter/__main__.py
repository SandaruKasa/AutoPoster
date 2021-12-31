import datetime
import logging
import sqlite3

import autoposter.scheduler
import autoposter.sync
import autoposter.workers

if __name__ == "__main__":
    logging.basicConfig(
        filename=f"{datetime.datetime.now().isoformat()}.log",
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    autoposter.init(
        sql_connector=sqlite3.connect,
        sql_credentials={
            "database": "Autoposter.sqlite3",
        }
    )
    for job in autoposter.database.get_all_jobs():
        autoposter.scheduler.add(job)
    autoposter.scheduler.start()
    try:
        autoposter.sync.shutdown_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        autoposter.sync.shutdown_event.set()
        autoposter.scheduler.stop()
        autoposter.workers.stop_all()
