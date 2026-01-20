import asyncio
import os
from datetime import datetime, timedelta, timezone
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

from database import set_language, get_language
from languages import texts
from movies import movies

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNELS = [(os.getenv("CHANNEL_USERNAME"), os.getenv("CHANNEL_LINK"))]
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()



# OBUNA TEKSHIRISH
async def check_subscriptions(user_id):
    for channel, _ in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except:
            return False
    return True

def subscription_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📺 Venus Kino", url="https://t.me/venuskino")]
    ])



# TIL TANLASH
def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang_uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
    ])



# BROADCAST
@dp.message(F.text.startswith("/broadcast"))
async def broadcast(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("⛔ Bu buyruq faqat adminlar uchun!")

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await message.answer(
            "❌ Matn yo‘q!\n\n"
            "To‘g‘ri foydalanish:\n"
            "<code>/broadcast Xabar matni</code>"
        )

    text = parts[1]
    sent = 0
    failed = 0
    user_ids = set()

    try:
        with open("users.txt", "r", encoding="utf-8") as f:
            for line in f:
                if "ID:" in line:
                    uid = line.split("ID:")[1].split("|")[0].strip()
                    if uid.isdigit():
                        user_ids.add(int(uid))
    except FileNotFoundError:
        return await message.answer("❌ users.txt topilmadi.")

    for uid in user_ids:
        try:
            await bot.send_message(uid, f"\n\n{text}")
            sent += 1
            await asyncio.sleep(0.05)  # flood bo‘lmasligi uchun
        except:
            failed += 1

    await message.answer(
        f"✅ Yuborildi: {sent}\n"
        f"❌ Yetib bormadi: {failed}"
    )



# Log qiladi
def log_user(message: types.Message):
    user = message.from_user

    # 🇺🇿 O‘zbekiston vaqti (UTC+5)
    uz_time = datetime.now(timezone(timedelta(hours=5))).strftime("%Y-%m-%d %H:%M:%S")

    username = f"@{user.username}" if user.username else "@yoq"
    line = f"Ism: {user.first_name} | Username: {username} | ID: {user.id} | Sana: {uz_time}\n"

    # Agar fayl yo‘q bo‘lsa — yaratadi
    if not os.path.exists("users.txt"):
        with open("users.txt", "w", encoding="utf-8") as f:
            f.write(line)
        return

    # Agar foydalanuvchi oldin yozilgan bo‘lsa — qayta yozmaydi
    with open("users.txt", "r", encoding="utf-8") as f:
        if f"ID: {user.id}" in f.read():
            return

    # 1 marta yozadi
    with open("users.txt", "a", encoding="utf-8") as f:
        f.write(line)

def log_user(message: types.Message):
    user = message.from_user
    uz_time = datetime.now(timezone(timedelta(hours=5))).strftime("%Y-%m-%d %H:%M:%S")
    username = f"@{user.username}" if user.username else "@yoq"
    text = message.text if message.text else "[media]"

    line = (
        f"Sana: {uz_time} | "
        f"ID: {user.id} | "
        f"Ism: {user.first_name} | "
        f"Username: {username} | "
        f"Xabar: {text}\n"
    )

    with open("users.txt", "a", encoding="utf-8") as f:
        f.write(line)



# START
@dp.message(F.text == "/start")
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    if not await check_subscriptions(user_id):
        await message.answer("📢 Iltimos, kanalga obuna bo‘ling:", reply_markup=subscription_keyboard())
        return

    await message.answer("🇺🇿 Tilni tanla    ng / Выберите язык / Choose language", reply_markup=language_keyboard())



# TIL TANLASH
@dp.callback_query(F.data.startswith("lang"))
async def handle_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id
    set_language(user_id, lang)
    await callback.message.answer(texts["language_selected"][lang])
    await callback.message.answer(texts["send_movie_code"][lang])



# ADMIN VIDEO FILE_ID OLISH
@dp.message(F.video)
async def get_file_id(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        file_id = message.video.file_id
        await message.answer(f"🎥 Kino fayl kodi:\n<code>{file_id}</code>")
    else:
        await message.answer("⛔ Siz admin emassiz.")



# ADMIN USERS
@dp.message(F.text == "/users")
async def show_users(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("⛔ Bu buyruq faqat adminlar uchun!")

    try:
        with open("users.txt", "r", encoding="utf-8") as f:
            data = f.read()

        if not data:
            await message.answer("📂 Hozircha ma’lumot yo‘q.")
        else:
            await message.answer(
                "📋 <b>Foydalanuvchilar va xabarlar:</b>\n\n"
                f"{data[-3800:]}"
            )
    except FileNotFoundError:
        await message.answer("❌ users.txt topilmadi.")



# KINO KODI
@dp.message(F.text)
async def handle_movie_code(message: types.Message):
    if message.text.startswith("/"):
        return

    user_id = message.from_user.id
    if not await check_subscriptions(user_id):
        await message.answer("📢 Iltimos, kanalga obuna bo‘ling:", reply_markup=subscription_keyboard())
        return

    log_user(message)

    lang = get_language(user_id)
    code = message.text.lower().strip()

    if code in movies:
        await message.answer(f"🎬 {movies[code]['title']}")
        await bot.send_video(
            chat_id=message.chat.id,
            video=movies[code]['file_id'],
            protect_content=True
        )
    else:
        await message.answer("❌ Bunday kino topilmadi.")



# BOTNI ISHGA TUSHIRISH
async def main():
    print("Bot ishga tushdi ✅")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())