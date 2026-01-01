import os
import math
import asyncio
import hashlib
from typing import BinaryIO, Optional, Tuple

from telethon import TelegramClient, helpers, utils
from telethon.network import MTProtoSender
from telethon.crypto import AuthKey
from telethon.tl.alltlobjects import LAYER
from telethon.tl.functions import InvokeWithLayerRequest
from telethon.tl.functions.auth import ExportAuthorizationRequest, ImportAuthorizationRequest
from telethon.tl.functions.upload import SaveFilePartRequest, SaveBigFilePartRequest
from telethon.tl.types import InputFile, InputFileBig


class _UploadSender:
    def __init__(self, client, sender, req, stride, loop):
        self.client = client
        self.sender = sender
        self.req = req
        self.stride = stride
        self.loop = loop
        self.prev = None

    async def send(self, data: bytes):
        if self.prev:
            await self.prev
        self.req.bytes = data
        self.prev = self.loop.create_task(self.client._call(self.sender, self.req))
        self.req.file_part += self.stride

    async def close(self):
        if self.prev:
            await self.prev
        await self.sender.disconnect()


class FastUploader:
    def __init__(self, client: TelegramClient):
        self.client = client
        self.loop = client.loop
        self.dc_id = client.session.dc_id
        self.auth_key: Optional[AuthKey] = client.session.auth_key

    async def _create_sender(self) -> MTProtoSender:
        dc = await self.client._get_dc(self.dc_id)
        sender = MTProtoSender(self.auth_key, loggers=self.client._log)
        await sender.connect(
            self.client._connection(
                dc.ip_address, dc.port, dc.id,
                loggers=self.client._log,
                proxy=self.client._proxy,
            )
        )

        if not self.auth_key:
            auth = await self.client(ExportAuthorizationRequest(self.dc_id))
            req = InvokeWithLayerRequest(
                LAYER,
                self.client._init_request.__class__(
                    query=ImportAuthorizationRequest(auth.id, auth.bytes)
                )
            )
            await sender.send(req)
            self.auth_key = sender.auth_key

        return sender

    async def upload(
        self,
        file: BinaryIO,
        filename: str,
        progress=None
    ):
        file_id = helpers.generate_random_long()
        size = os.path.getsize(file.name)
        part_size = utils.get_appropriated_part_size(size) * 1024
        part_count = math.ceil(size / part_size)
        is_big = size > 10 * 1024 * 1024

        connections = 4 if size < 100 * 1024 * 1024 else 8
        senders = []

        for i in range(connections):
            sender = await self._create_sender()
            req = (
                SaveBigFilePartRequest(file_id, i, part_count, b"")
                if is_big
                else SaveFilePartRequest(file_id, i, b"")
            )
            senders.append(_UploadSender(self.client, sender, req, connections, self.loop))

        md5 = hashlib.md5()
        buf = bytearray()
        idx = 0

        while True:
            chunk = file.read(part_size)
            if not chunk:
                break

            if not is_big:
                md5.update(chunk)

            buf.extend(chunk)
            if len(buf) >= part_size:
                await senders[idx % connections].send(bytes(buf[:part_size]))
                buf = buf[part_size:]
                idx += 1

                if progress:
                    await progress(min(idx * part_size, size), size)

        if buf:
            await senders[idx % connections].send(bytes(buf))

        for s in senders:
            await s.close()

        if is_big:
            return InputFileBig(file_id, part_count, filename)
        return InputFile(file_id, part_count, filename, md5.hexdigest())