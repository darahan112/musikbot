import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID
from player import MusicPlayer

logging.basicConfig(level=logging.INFO)
bot = Client("ytmusicbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
player = MusicPlayer(bot)

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(_, m: Message):
    await m.reply("👋 Selamat datang di MusicBot!\nPerintah: /play [judul atau url], /pause, /resume, /skip, /stop")

@bot.on_message(filters.command("play") & filters.group)
async def play_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("Kirim judul lagu atau url YouTube setelah /play")
    query = " ".join(message.command[1:])
    await player.play(message, query)

@bot.on_message(filters.command("pause") & filters.group)
async def pause_handler(_, m): await player.pause(m)

@bot.on_message(filters.command("resume") & filters.group)
async def resume_handler(_, m): await player.resume(m)

@bot.on_message(filters.command("skip") & filters.group)
async def skip_handler(_, m): await player.skip(m)

@bot.on_message(filters.command("stop") & filters.group)
async def stop_handler(_, m): await player.stop(m)

@bot.on_message(filters.command("playlist") & filters.group)
async def playlist_handler(_, m): await player.show_playlist(m)

if __name__ == "__main__":
    bot.run()
