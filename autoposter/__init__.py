# todo add more logging to the module
import autoposter.database


def init(sql_connector, sql_credentials):
    autoposter.database.init(sql_connector, sql_credentials)
