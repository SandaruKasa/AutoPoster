import pathlib

import telegram

import autoposter.sync


def post_with_highres_to_discussion(
        source: pathlib.Path,
        worker: telegram.Bot,
        channel_id: int,
        discussion_group_id: int,
):
    with autoposter.sync.Arbitrator(
            autoposter.sync.get_chat_lock(channel_id),
            autoposter.sync.get_chat_lock(discussion_group_id)
    ):
        pass  # todo post with highres to the comments


def post(
        source: pathlib.Path,
        worker: telegram.Bot,
        chat_id: int,
        post_highres: bool,
):
    with autoposter.sync.get_chat_lock(chat_id):
        pass  # todo post with highres to the same chat or without highres
