import asyncio
import yt_dlp
from pyrogram.types import Message
from pytgcalls import PyTgCalls, idle
from pytgcalls.types.input_stream import InputStream, AudioPiped

class MusicPlayer:
    def __init__(self, bot):
        self.bot = bot
        self.call = PyTgCalls(self.bot)
        self.queues = {}  # chat_id: [ {title, url, file} ]
        self.now_playing = {}
        self.is_running = False

        @self.call.on_stream_end()
        async def on_end(_, update):
            chat_id = update.chat_id
            await self._next(chat_id)

    async def play(self, message: Message, query):
        chat_id = message.chat.id
        if chat_id not in self.queues:
            self.queues[chat_id] = []

        info = await self._search_youtube(query)
        if not info:
            return await message.reply("❌ Lagu tidak ditemukan.")

        self.queues[chat_id].append(info)
        await message.reply(f"Ditambahkan ke antrean: {info['title']}")

        if chat_id not in self.now_playing:
            await self._play_next(message, chat_id)

        if not self.is_running:
            asyncio.create_task(self.call.start())
            self.is_running = True

    async def _play_next(self, message, chat_id):
        if not self.queues[chat_id]:
            await message.reply("Antrean kosong.")
            if chat_id in self.now_playing:
                del self.now_playing[chat_id]
            await self.call.leave_group_call(chat_id)
            return
        info = self.queues[chat_id].pop(0)
        audio = AudioPiped(info["file"])
        await self.call.join_group_call(chat_id, audio)
        self.now_playing[chat_id] = info
        await message.reply(f"🎶 Sedang diputar: {info['title']}")

    async def pause(self, message):
        await self.call.pause_stream(message.chat.id)
        await message.reply("⏸️ Musik dijeda.")

    async def resume(self, message):
        await self.call.resume_stream(message.chat.id)
        await message.reply("▶️ Musik dilanjutkan.")

    async def skip(self, message):
        await self._next(message.chat.id)
        await message.reply("⏭️ Lagu berikutnya.")

    async def stop(self, message):
        chat_id = message.chat.id
        await self.call.leave_group_call(chat_id)
        self.queues[chat_id] = []
        self.now_playing.pop(chat_id, None)
        await message.reply("⏹️ Streaming dihentikan.")

    async def show_playlist(self, message):
        chat_id = message.chat.id
        queue = self.queues.get(chat_id, [])
        if not queue:
            return await message.reply("Antrean kosong.")
        teks = "🎶 **Antrean Musik**:\n" + "\n".join([f"{i+1}. {x['title']}" for i, x in enumerate(queue)])
        await message.reply(teks)

    async def _next(self, chat_id):
        if self.queues.get(chat_id):
            # dummy message, only for internal use, not for showing
            class DummyMsg:
                def __init__(self, chat_id): self.chat = type("obj", (), {"id": chat_id})()
                async def reply(self, x): pass
            await self._play_next(DummyMsg(chat_id), chat_id)
        else:
            await self.call.leave_group_call(chat_id)
            self.now_playing.pop(chat_id, None)

    async def _search_youtube(self, query):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'quiet': True,
            'noplaylist': True,
            'cookiefile': "cookies.txt",
        }
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=True))
            except Exception:
                return None
            title = info.get("title")
            file = ydl.prepare_filename(info)
            url = info.get("webpage_url")
            return {"title": title, "file": file, "url": url}
