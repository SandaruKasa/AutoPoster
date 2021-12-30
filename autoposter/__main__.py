import datetime
import logging

import autoposter.database
import autoposter.scheduler
import autoposter.sync
import autoposter.workers

if __name__ == "__main__":
    logging.basicConfig(
        filename=f"{datetime.datetime.now().isoformat()}.log",
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    for job in autoposter.database.get_all_jobs():
        autoposter.scheduler.add(job)
    autoposter.scheduler.start()
    autoposter.sync.shutdown_event.wait()
    autoposter.scheduler.stop()
    autoposter.workers.stop_all()
