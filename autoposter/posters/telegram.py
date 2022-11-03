from pathlib import Path

import pydantic
import pyrogram
from pyrogram.types import InputMediaDocument, InputMediaPhoto, InputMediaVideo, Message

from ..types import Media, MediaType, Post
from . import Poster


class TelegramPoster(Poster):
    chat: int | str

    class Config:
        arbitrary_types_allowed = True

    client: pyrogram.client.Client = pydantic.Field(alias="credentials")

    # TODO: use a subdir?
    _SESSIONS_DIR: Path = Path.cwd()

    @pydantic.validator("client", pre=True)
    def _make_client(cls, credentials: dict, values: dict) -> pyrogram.client.Client:
        return pyrogram.client.Client(
            name=values["name"],
            workdir=str(TelegramPoster._SESSIONS_DIR),
            **credentials,
            no_updates=True,
        )

    # FIXME: breaks on GIFs.
    #        Because even if you send them as documents,
    #        Telegram sometimes converts them to .gif.mp4 and refuses to send them
    #        as a part of a media group, returning a very "informative" [400 MEDIA_INVALID]
    # FIXME: breaks on mixing documents and non-documents together.
    #        Because there are photo/video media groups and there document media groups.
    #        Separate things, cannot be mixed. Wow. I suspect there is also the third type:
    #        audio media-groups, but I do not feel like checking ruining my mood even more.
    #        So yeah, for now this code mixes documents with non-documents and gets
    #        a very "informative" [400 MEDIA_INVALID] back from Telegram.
    # Telegram has WONDERFUL api
    async def post(self, post: Post) -> Message | list[Message]:
        assert post.caption or post.media
        match len(post.media):
            case 0:
                return await self.client.send_message(
                    chat_id=self.chat,
                    text=post.caption,
                )
            case 1:
                media = post.media[0]
                # Exercise for reader: try to spot similar code pieces
                match media.media_type:
                    case MediaType.IMAGE:
                        return await self.client.send_photo(
                            chat_id=self.chat,
                            photo=str(media.source),
                            caption=post.caption,
                        )  # type: ignore [return-value]
                        # ^ We don't use pyrogram.Client.stop_transmission, so no None's
                    case MediaType.VIDEO:
                        return await self.client.send_video(
                            chat_id=self.chat,
                            video=str(media.source),
                            caption=post.caption,
                        )  # type: ignore [return-value]
                        # ^ We don't use pyrogram.Client.stop_transmission, so no None's
                    # Telegram treats GIFs very poorly.
                    # Let's minimize the damage and send GIFs as documents.
                    case MediaType.DOCUMENT | MediaType.GIF:
                        return await self.client.send_document(
                            chat_id=self.chat,
                            document=str(media.source),
                            caption=post.caption,
                        )  # type: ignore [return-value]
                        # ^ We don't use pyrogram.Client.stop_transmission, so no None's
            case n:
                # FIXME: split into several posts manually
                assert n <= 10, "Too many attachments"
                # Why can't Telegram accept 1-10 instead of 2-10? Because sOfTwArE.
                # Why can't Telegram have a method that accepts 1 InputMedia
                # and then does all if-else-ing server-side (see boilerplate above)?
                # Because sOfTwArE!!!1!
                media_group = [self._wrap_media(m) for m in post.media]
                media_group[0].caption = post.caption
                return await self.client.send_media_group(
                    chat_id=self.chat,
                    media=media_group,  # type: ignore [arg-type]
                )

    def _wrap_media(
        self, media: Media
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
