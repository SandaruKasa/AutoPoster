import typing
from pathlib import Path

import pydantic
import pyrogram
from pyrogram.types import InputMediaDocument, InputMediaPhoto, InputMediaVideo, Message

from ..types import Media, MediaType, Post
from . import Poster

T = typing.TypeVar("T")


def _split_list(l: list[T], n: int) -> list[list[T]]:
    return [l[i : i + n] for i in range(0, len(l), n)]


class TelegramPoster(Poster):
    chat: int | str
    reply_when_splitting: bool = True

    class Config:
        arbitrary_types_allowed = True

    client: pyrogram.client.Client

    # TODO: use a subdir?
    _SESSIONS_DIR: Path = Path.cwd()

    @pydantic.validator("client", pre=True)
    def _make_client(cls, kwargs: dict, values: dict) -> pyrogram.client.Client:
        kwargs.setdefault("name", values["name"])
        kwargs.setdefault("workdir", str(TelegramPoster._SESSIONS_DIR))
        kwargs["no_updates"] = True
        return pyrogram.client.Client(**kwargs)

    async def post(self, post: Post) -> list[list[Message]]:
        assert post.caption or post.media
        result = []
        reply_ro_message_id = None
        for piece in TelegramPoster.split_post(post):
            posted = await self.post_no_split(piece, reply_ro_message_id)
            result.append(posted)
            if self.reply_when_splitting:
                reply_ro_message_id = posted[0].id
        return result

    # FIXME: breaks on mixing documents and non-documents together.
    #        Because there are photo/video media groups and there document media groups.
    #        Separate things, cannot be mixed. Wow.
    #        Then there are also GIFs. Probably THE most broken thing in telegram.
    #        They cannot be sent as a part of ANY group.
    #        (Note that mp4 videos with no audio stream are also considered to be GIFs. Sometimes.)
    #        And I suspect there are also distinct media-groups for audio,
    #        but I do not feel like checking and ruining my mood even more.
    #        So yeah, for now this code mixes "unmixable" types of media and gets
    #        a very "informative" [400 MEDIA_INVALID] back from Telegram.
    # Telegram has WONDERFUL api
    async def post_no_split(
        self,
        post: Post,
        reply_to_message_id: int | None = None,
    ) -> list[Message]:
        assert post.caption or post.media

        match len(post.media):
            case 0:
                return [
                    await self.post_text(
                        text=post.caption,
                        reply_to_message_id=reply_to_message_id,
                    )
                ]
            case 1:
                return [
                    await self.post_one_media(
                        media=post.media[0],
                        caption=post.caption,
                        reply_to_message_id=reply_to_message_id,
                    )
                ]
            case _:
                return await self.post_media_group(
                    media=post.media,
                    caption=post.caption,
                    reply_to_message_id=reply_to_message_id,
                )

    async def post_text(
        self,
        text: str,
        reply_to_message_id: int | None = None,
    ) -> Message:
        return await self.client.send_message(
            chat_id=self.chat,
            text=text,
            reply_to_message_id=reply_to_message_id,  # type: ignore [arg-type]
        )

    async def post_one_media(
        self,
        media: Media,
        caption: str = "",
        reply_to_message_id: int | None = None,
    ) -> Message:
        # Exercise for reader: try to spot similar code pieces
        match media.media_type:
            case MediaType.IMAGE:
                result = await self.client.send_photo(
                    chat_id=self.chat,
                    photo=str(media.source),
                    caption=caption,
                    reply_to_message_id=reply_to_message_id,  # type: ignore [arg-type]
                )
            case MediaType.VIDEO:
                result = await self.client.send_video(
                    chat_id=self.chat,
                    video=str(media.source),
                    caption=caption,
                    reply_to_message_id=reply_to_message_id,  # type: ignore [arg-type]
                )
            # Telegram treats GIFs very poorly.
            # Let's minimize the damage and send GIFs as documents.
            case MediaType.DOCUMENT | MediaType.GIF:
                result = await self.client.send_document(
                    chat_id=self.chat,
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
            chat_id=self.chat,
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

    async def __aenter__(self):
        return await self.client.__aenter__()

    async def __aexit__(self, *args):
        return await self.client.__aexit__(*args)
