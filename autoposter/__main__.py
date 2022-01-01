import datetime
import logging

import autoposter.scheduler
import autoposter.sync
import autoposter.workers

logger = logging.getLogger("Autoposter")


def main(debug: bool = False):
    logging.basicConfig(
        filename=f"{datetime.datetime.now().isoformat()}.log",
        level=logging.DEBUG if debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    autoposter.init(
        sql_credentials={
            "database": "Autoposter.sqlite3",
        }
    )
    logger.info("Getting jobs...")
    job_count = 0
    for job in autoposter.database.get_all_jobs():
        logger.debug("Adding job %s to scheduler", job)
        autoposter.scheduler.add(job)
        job_count += 1
    logger.info("Scheduled %d jobs, starting scheduler...", job_count)
    autoposter.scheduler.start()
    try:
        autoposter.sync.shutdown_event.wait()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        pass
    finally:
        logger.info("Shutting down...")
        autoposter.sync.shutdown_event.set()
        logger.info("Stopping scheduler...")
        autoposter.scheduler.stop()
        logger.info("Stopping workers...")
        autoposter.workers.stop_all()
        logger.info("Goodbye!")


if __name__ == "__main__":
    try:
        main(debug=True)
    except BaseException as e:
        logger.error("%s", str(e))
        raise
