import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

# --- إعدادات البوت ---
TOKEN = "YOUR_BOT_TOKEN_HERE"  # ضع توكن بوتك هنا
ADMIN_ID = YOUR_ADMIN_ID_HERE  # ضع آيدي الأذمن الخاص بك هنا

# القنوات المطلوبة للاشتراك الإلزامي (تم الاكتفاء بالقناة الأساسية التي تمتلك يوزرنيم صحيح)
REQUIRED_CHANNELS = ["@r1iv_k"]

# إعداد قاعدة البيانات
conn = sqlite3.connect("store_bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    invited_by INTEGER DEFAULT 0
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    username TEXT,
    password TEXT,
    is_sold INTEGER DEFAULT 0
)
"""
)
conn.commit()

# --- الترجمة ---
LANGS = {
    "ar": {
        "welcome": "أهلاً بك في متجرنا! 🎮\nاستخدم الأزرار أدناه لتصفح القسم أو تجميع النقاط.",
        "sub_required": (
            "⚠️ **عذراً، يجب عليك الاشتراك في قناة المتجر أولاً لكي تتمكن من استخدام البوت!**\n\n"
            "يرجى الانضمام إليها ثم اضغط على زر التحقق أدناه 👇"
        ),
        "btn_subscribe_ch1": "📢 اشترك في القناة",
        "btn_check_sub": "✅ تحقق من الاشتراكات",
        "btn_store": "🛒 المتجر",
        "btn_profile": "👤 حسابي",
        "btn_earn": "🎁 تجميع النقاط",
        "not_subscribed": "❌ لم تقم بالاشتراك في القناة بعد!",
        "profile_text": (
            "👤 **معلومات الحساب:**\n\n🆔 الآيدي: `{user_id}`\n💎 النقاط: `{points}`"
        ),
        "earn_text": (
            "🎁 **تجميع النقاط المجانية:**\n\n"
            "قم بدعوة أصدقائك عبر رابط الدعوة الخاص بك لتحصل على نقاط لكل شخص يدخل البوت:\n\n"
            "`{ref_link}`"
        ),
    },
    "en": {
        "welcome": "Welcome to our store! 🎮\nUse the buttons below to navigate.",
        "sub_required": (
            "⚠️ **Sorry, you must subscribe to the channel first!**\n\n"
            "Please join it and then click verify below 👇"
        ),
        "btn_subscribe_ch1": "📢 Join Channel",
        "btn_check_sub": "✅ Verify Subscription",
        "btn_store": "🛒 Store",
        "btn_profile": "👤 Profile",
        "btn_earn": "🎁 Earn Points",
        "not_subscribed": "❌ You haven't subscribed to the channel yet!",
        "profile_text": (
            "👤 **Account Info:**\n\n🆔 ID: `{user_id}`\n💎 Points: `{points}`"
        ),
        "earn_text": (
            "🎁 **Earn Free Points:**\n\n"
            "Invite your friends using your referral link:\n\n`{ref_link}`"
        ),
    },
}

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()


# --- دالة التحقق من الاشتراكات ---
async def check_subscriptions(user_id: int) -> bool:
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            logging.error(f"Error checking sub for {channel}: {e}")
            return False
    return True


# --- أمر البداية /start ---
@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id

    # معالجة نظام الدعوات (Referral)
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id != user_id:
            cursor.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            )
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO users (user_id, invited_by) VALUES (?, ?)",
                    (user_id, referrer_id),
                )
                # منح نقاط للمُحيل (مثلا 5 نقاط)
                cursor.execute(
                    "UPDATE users SET points = points + 5 WHERE user_id = ?",
                    (referrer_id,),
                )
                conn.commit()
                try:
                    await bot.send_message(
                        referrer_id,
                        "🎉 لقد انضم شخص جديد عبر رابط دعوتك وحصلت على 5 نقاط!",
                    )
                except:
                    pass

    # تسجيل المستخدم إذا لم يكن موجوداً
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

    # التحقق من الاشتراك الإلزامي
    is_subbed = await check_subscriptions(user_id)
    lang = "ar"  # اللغة الافتراضية

    if not is_subbed:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=LANGS[lang]["btn_subscribe_ch1"],
                        url=f"https://t.me/{REQUIRED_CHANNELS[0].replace('@', '')}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=LANGS[lang]["btn_check_sub"],
                        callback_data="check_sub",
                    )
                ],
            ]
        )
        await message.answer(
            LANGS[lang]["sub_required"],
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    # القائمة الرئيسية إذا كان مشتركاً
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=LANGS[lang]["btn_store"], callback_data="store_menu"
                ),
                InlineKeyboardButton(
                    text=LANGS[lang]["btn_profile"],
                    callback_data="profile_menu",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=LANGS[lang]["btn_earn"], callback_data="earn_menu"
                )
            ],
        ]
    )
    await message.answer(LANGS[lang]["welcome"], reply_markup=keyboard)


# --- زر التحقق من الاشتراكات ---
@router.callback_query(F.data == "check_sub")
async def callback_check_sub(callback: CallbackQuery):
    user_id = callback.from_user.id
    is_subbed = await check_subscriptions(user_id)
    lang = "ar"

    if not is_subbed:
        await callback.answer(LANGS[lang]["not_subscribed"], show_alert=True)
        return

    await callback.message.delete()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=LANGS[lang]["btn_store"], callback_data="store_menu"
                ),
                InlineKeyboardButton(
                    text=LANGS[lang]["btn_profile"],
                    callback_data="profile_menu",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=LANGS[lang]["btn_earn"], callback_data="earn_menu"
                )
            ],
        ]
    )
    await callback.message.answer(LANGS[lang]["welcome"], reply_markup=keyboard)


# --- زر الملف الشخصي (الحساب) ---
@router.callback_query(F.data == "profile_menu")
async def callback_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    points = res[0] if res else 0
    lang = "ar"

    text = LANGS[lang]["profile_text"].format(user_id=user_id, points=points)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 عودة", callback_data="back_to_home"
                )
            ]
        ]
    )
    await callback.message.edit_text(
        text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN
    )


# --- زر تجميع النقاط ---
@router.callback_query(F.data == "earn_menu")
async def callback_earn(callback: CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    lang = "ar"

    text = LANGS[lang]["earn_text"].format(ref_link=ref_link)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 عودة", callback_data="back_to_home"
                )
            ]
        ]
    )
    await callback.message.edit_text(
        text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN
    )


# --- زر العودة للقائمة الرئيسية ---
@router.callback_query(F.data == "back_to_home")
async def callback_home(callback: CallbackQuery):
    lang = "ar"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=LANGS[lang]["btn_store"], callback_data="store_menu"
                ),
                InlineKeyboardButton(
                    text=LANGS[lang]["btn_profile"],
                    callback_data="profile_menu",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=LANGS[lang]["btn_earn"], callback_data="earn_menu"
                )
            ],
        ]
    )
    await callback.message.edit_text(
        LANGS[lang]["welcome"], reply_markup=keyboard
    )


# --- زر المتجر (مثال) ---
@router.callback_query(F.data == "store_menu")
async def callback_store(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎮 قسم الحسابات", callback_data="dummy_category"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 عودة", callback_data="back_to_home"
                )
            ],
        ]
    )
    await callback.message.edit_text(
        "🛒 **اختر القسم المناسب:**",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )


@router.callback_query(F.data == "dummy_category")
async def dummy_cat(callback: CallbackQuery):
    await callback.answer("المتجر قيد التحديث حالياً!", show_alert=True)


async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
