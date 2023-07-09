from pathlib import Path
from typing import Generator

from PIL import Image
from pyrogram.errors import BotMethodInvalid, PeerIdInvalid
from pyrogram.types import InputMediaDocument, Message

from ..types import Media, MediaType, Post
from .telegram import ChatId, TelegramPoster


class TelegramHighresPoster(TelegramPoster):
    async def post_no_split(
        self,
        post: Post,
        chat_id: ChatId,
        reply_to_message_id: int | None = None,
    ) -> list[Message]:
        main_post = await super().post_no_split(
            post=post,
            chat_id=chat_id,
            reply_to_message_id=reply_to_message_id,
        )

        match list(self.gather_compression_victims(post.media)):
            case []:
                pass
            case [media]:
                reply_to = await self.try_get_comment_chain(main_post[0])
                await self.client.send_document(
                    chat_id=reply_to.chat.id,
                    reply_to_message_id=reply_to.id,
                    document=str(media),
                )
            case many_media:
                reply_to = await self.try_get_comment_chain(main_post[0])
                await self.client.send_media_group(
                    chat_id=reply_to.chat.id,
                    reply_to_message_id=reply_to.id,
                    media=[InputMediaDocument(media=str(path)) for path in many_media],
                )

        return main_post

    def gather_compression_victims(
        self, medias: list[Media]
    ) -> Generator[Path, None, None]:
        for media in medias:
            if media.media_type == MediaType.IMAGE:
                source = media.source
                image = Image.open(source)
                if image.width > 1280 or image.height > 1280:
                    yield source

    # Find a message to reply to when sending the uncompressed images.
    # Will attempt to find a comment chain.
    # If it fails (not a channel, no comments, self.client is a bot, etc.) will default to
    # replying to the previous message.
    async def try_get_comment_chain(self, message: Message) -> Message:
        try:
            return await self.client.get_discussion_message(
                chat_id=message.chat.id, message_id=message.id
            )
        except BotMethodInvalid:
            return message
        except PeerIdInvalid:  # for whatever reason you'll sometime get this
            return message
