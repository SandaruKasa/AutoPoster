# todo add more logging to the module
# todo add more comments to the module

import logging

import autoposter.database


def init(sql_credentials):
    autoposter.database.init(sql_credentials=sql_credentials)
    logging.getLogger("Autoposter").info("Init successful")
