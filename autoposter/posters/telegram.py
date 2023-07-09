import asyncio
import typing
from pathlib import Path

import pydantic
import pyrogram
from pyrogram.types import InputMediaDocument, InputMediaPhoto, InputMediaVideo, Message

from ..types import Media, MediaType, Post
from . import Poster

T = typing.TypeVar("T")
ChatId = typing.Union[int, str]
MessageOrGroup = list[Message]
Messages = list[MessageOrGroup]


def _split_list(l: list[T], n: int) -> list[list[T]]:
    return [l[i : i + n] for i in range(0, len(l), n)]


class TelegramPoster(Poster):
    chat: ChatId | list[ChatId]
    reply_when_splitting: bool = False
    client: pyrogram.client.Client = pydantic.Field({})

    class Config:
        arbitrary_types_allowed = True

    # TODO: use a subdir?
    _SESSIONS_DIR: Path = Path.cwd()

    @pydantic.validator("client", pre=True, always=True)
    def _make_client(cls, kwargs: dict, values: dict) -> pyrogram.client.Client:
        kwargs.setdefault("name", values["name"])
        kwargs.setdefault("workdir", str(TelegramPoster._SESSIONS_DIR))
        kwargs["no_updates"] = True
        return pyrogram.client.Client(**kwargs)

    # FIXME: breaks on mixing documents and non-documents together.
    #        Because there are photo/video media groups and there are document media groups.
    #        Different things, cannot be mixed. Wow.
    #        Then there are also GIFs. Probably THE most broken thing in telegram.
    #        They cannot be sent as a part of ANY group.
    #        (Note that mp4 videos with no audio stream are also considered to be GIFs. Sometimes.)
    #        And I suspect there are also special media-groups for audio files,
    #        but I do not feel like checking and ruining my mood even more.
    #        So yeah, for now this code mixes "unmixable" types of media and gets
    #        a very "informative" [400 MEDIA_INVALID] back from Telegram.
    async def post(self, post: Post) -> list[Messages]:
        assert post.caption or post.media
        pieces = TelegramPoster.split_post(post)
        return await asyncio.gather(
            *(
                self.post_to_one_chat(
                    post_pieces=pieces,
                    chat_id=chat_id,
                )
                for chat_id in (
                    self.chat if isinstance(self.chat, list) else [self.chat]
                )
            )
        )

    async def post_to_one_chat(
        self,
        post_pieces: list[Post],
        chat_id: ChatId,
    ) -> Messages:
        result = []
        reply_ro_message_id = None
        for piece in post_pieces:
            posted = await self.post_no_split(
                post=piece,
                chat_id=chat_id,
                reply_to_message_id=reply_ro_message_id,
            )
            result.append(posted)
            if self.reply_when_splitting:
                reply_ro_message_id = posted[0].id
        return result

    # Telegram has WONDERFUL api
    async def post_no_split(
        self,
        post: Post,
        chat_id: ChatId,
        reply_to_message_id: int | None = None,
    ) -> MessageOrGroup:
        assert post.caption or post.media

        match len(post.media):
            case 0:
                return [
                    await self.post_text(
                        text=post.caption,
                        chat_id=chat_id,
                        reply_to_message_id=reply_to_message_id,
                    )
                ]
            case 1:
                return [
                    await self.post_one_media(
                        media=post.media[0],
                        caption=post.caption,
                        chat_id=chat_id,
                        reply_to_message_id=reply_to_message_id,
                    )
                ]
            case _:
                return await self.post_media_group(
                    media=post.media,
                    caption=post.caption,
                    chat_id=chat_id,
                    reply_to_message_id=reply_to_message_id,
                )

    async def post_text(
        self,
        text: str,
        chat_id: ChatId,
        reply_to_message_id: int | None = None,
    ) -> Message:
        return await self.client.send_message(
            chat_id=chat_id,
            text=text,
            reply_to_message_id=reply_to_message_id,  # type: ignore [arg-type]
        )

    async def post_one_media(
        self,
        chat_id: ChatId,
        media: Media,
        caption: str = "",
        reply_to_message_id: int | None = None,
    ) -> Message:
        # Exercise for reader: try to spot similar code pieces
        match media.media_type:
            case MediaType.IMAGE:
                result = await self.client.send_photo(
                    chat_id=chat_id,
                    photo=str(media.source),
                    caption=caption,
                    reply_to_message_id=reply_to_message_id,  # type: ignore [arg-type]
                )
            case MediaType.VIDEO:
                result = await self.client.send_video(
                    chat_id=chat_id,
                    video=str(media.source),
                    caption=caption,
                    reply_to_message_id=reply_to_message_id,  # type: ignore [arg-type]
                )
            # Telegram treats GIFs very poorly.
            # Let's minimize the damage and send GIFs as documents.
            case MediaType.DOCUMENT | MediaType.GIF:
                result = await self.client.send_document(
                    chat_id=chat_id,
                    document=str(media.source),
                    caption=caption,
                    reply_to_message_id=reply_to_message_id,  # type: ignore [arg-type]
                )
        assert (
            result is not None
        )  # We don't use pyrogram.Client.stop_transmission, so no None's
        return result

    async def post_media_group(
        self,
        chat_id: ChatId,
        media: list[Media],
        caption: str = "",
        reply_to_message_id: int | None = None,
    ) -> list[Message]:
        assert len(media) <= 10, "Too many attachments"
        # Why can't Telegram accept 1-10 instead of 2-10? Because sOfTwArE.
        # Why can't Telegram have a method that accepts 1 InputMedia
        # and then does all if-else-ing server-side (see boilerplate above)?
        # Because sOfTwArE!!!1!
        media_group = [TelegramPoster._wrap_media(m) for m in media]
        media_group[0].caption = caption
        return await self.client.send_media_group(
            chat_id=chat_id,
            media=media_group,  # type: ignore [arg-type]
            reply_to_message_id=reply_to_message_id,  # type: ignore [arg-type]
        )

    @staticmethod
    def split_post(post: Post) -> list[Post]:
        media_groups = _split_list(post.media, 10)
        if len(media_groups) <= 1:
            return [post]
        result = [Post(media=media_group) for media_group in media_groups]
        result[0].caption = post.caption
        return result

    @staticmethod
    def _wrap_media(
        media: Media,
    ) -> InputMediaPhoto | InputMediaVideo | InputMediaDocument:
        # Hmmm, this code looks oddly familiar!
        match media.media_type:
            case MediaType.IMAGE:
                return InputMediaPhoto(str(media.source))
            case MediaType.VIDEO:
                return InputMediaVideo(str(media.source))
            # Telegram treats GIFs very poorly.
            # Let's minimize the damage and send GIFs as documents.
            case MediaType.DOCUMENT | MediaType.GIF:
                return InputMediaDocument(str(media.source))

    # FIXME: repeated reconnection
    async def __aenter__(self):
        return await self.client.__aenter__()

    async def __aexit__(self, *args):
        return await self.client.__aexit__(*args)
