import asyncio
import logging
import sqlite3
from urllib.parse import quote
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, LabeledPrice
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ============================================================
# --- إعدادات البوت والمدير ---
# ============================================================
API_TOKEN = "8852527009:AAGm909nYrGQM-QZW9VlVW9MJV1Zr2kgKa4ا"
ADMIN_ID = 8919826699
REQUIRED_CHANNELS = ["@r1ivk_giveaway"]
CHANNEL_LINK = "https://t.me/r1ivk_giveaway"

POINT_PACKAGES = {
    2: 5,
    5: 10,
    10: 18,
    15: 25,
    30: 45,
}

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ============================================================
# --- قاعدة البيانات ---
# ============================================================
def init_db():
    conn = sqlite3.connect("store_bot.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            points INTEGER DEFAULT 0,
            referred_by INTEGER,
            lang TEXT DEFAULT 'ar'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            category TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            account_id INTEGER,
            UNIQUE(user_id, account_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            telegram_charge_id TEXT PRIMARY KEY,
            provider_charge_id TEXT,
            user_id INTEGER NOT NULL,
            stars INTEGER NOT NULL,
            points INTEGER NOT NULL,
            payload TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_chat (
            admin_id INTEGER PRIMARY KEY,
            active_target_user_id INTEGER
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ============================================================
# --- النصوص ---
# ============================================================
texts = {
    "ar": {
        "welcome": "أهلاً بك في متجر r1ivk Store 🎮\nاختر من القائمة أدناه 👇.\n\n💬 لأي استفسار، أرسل رسالتك هنا.",
        "lang_changed": "تم تغيير اللغة إلى العربية! 🇸🇦",
        "btn_ref": "💎 تجميع رصيد (دعوة الأصدقاء)",
        "btn_info": "👤 معلومات حسابك",
        "btn_redeem": "🎁 استبدال النقاط",
        "btn_buy_points": "⭐ شراء نقاط بنجوم تيليجرام",
        "buy_points_title": "⭐ **شراء النقاط:**\n\nاختر الباقة:",
        "btn_my_purchases": "📁 حساباتي المشراة",
        "btn_lang": "🌐 تغيير اللغة / Change Language",
        "account_info": "👤 **معلومات حسابك:**\n\n🆔 ID: `{}`\n💎 النقاط: `{}`\n\n🔗 رابطك:\n`{}`\n*(1 نقطة لكل صديق جديد يتحقق!)*",
        "redeem_title": "🎁 **اختر الحساب:**",
        "my_purchases_title": "📁 **حساباتك:**",
        "no_purchases": "❌ لا يوجد مشتريات.",
        "no_accounts": "❌ لا توجد حسابات متاحة.",
        "not_enough_points": "⚠️ نقاطك غير كافية!",
        "success_redeem": "🎉 **مبروك:**\n\n👤 `{}`\n🔑 `{}`",
        "btn_back": "⬅️ رجوع",
        "btn_share": "📤 مشاركة الرابط",
        "sub_required": (
            "⚠️ **يجب الاشتراك في القناة أولاً!**\n"
            f"🔗 {CHANNEL_LINK}"
        ),
        "btn_subscribe_ch1": "📢 اشترك في القناة",
        "btn_check_sub": "🔄 تحقق من الاشتراك",
        "not_subscribed_yet": "❌ لم تشترك بعد!"
    },
    "en": {
        "welcome": "Welcome to r1ivk Store 🎮\nChoose from the menu below 👇.\n\n💬 For inquiries, send your message here.",
        "lang_changed": "Language changed to English! 🇬🇧",
        "btn_ref": "💎 Earn Points",
        "btn_info": "👤 Account Info",
        "btn_redeem": "🎁 Redeem Points",
        "btn_buy_points": "⭐ Buy Points with Stars",
        "buy_points_title": "⭐ **Buy Points:**\n\nChoose a package:",
        "btn_my_purchases": "📁 My Purchases",
        "btn_lang": "🌐 تغيير اللغة / Change Language",
        "account_info": "👤 **Your Account:**\n\n🆔 ID: `{}`\n💎 Points: `{}`\n\n🔗 Your link:\n`{}`\n*(1 point per verified friend!)*",
        "redeem_title": "🎁 **Choose account:**",
        "my_purchases_title": "📁 **Your accounts:**",
        "no_purchases": "❌ No purchases yet.",
        "no_accounts": "❌ No accounts available.",
        "not_enough_points": "⚠️ Not enough points!",
        "success_redeem": "🎉 **Congrats:**\n\n👤 `{}`\n🔑 `{}`",
        "btn_back": "⬅️ Back",
        "btn_share": "📤 Share Link",
        "sub_required": (
            "⚠️ **You must subscribe first!**\n"
            f"🔗 {CHANNEL_LINK}"
        ),
        "btn_subscribe_ch1": "📢 Subscribe",
        "btn_check_sub": "🔄 Verify",
        "not_subscribed_yet": "❌ Not subscribed yet!"
    }
}

def get_lang(user_id):
    conn = sqlite3.connect("store_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "ar"

async def check_subscription(user_id: int) -> bool:
    try:
        for channel in REQUIRED_CHANNELS:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        return True
    except Exception as e:
        logging.error(f"Error checking subscription: {e}")
        return True

def get_main_keyboard(lang):
    t = texts[lang]
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=t["btn_ref"], callback_data="earn_points"))
    builder.row(InlineKeyboardButton(text=t["btn_info"], callback_data="account_info"))
    builder.row(InlineKeyboardButton(text=t["btn_buy_points"], callback_data="buy_points_menu"))
    builder.row(InlineKeyboardButton(text=t["btn_redeem"], callback_data="redeem_menu"))
    builder.row(InlineKeyboardButton(text=t["btn_my_purchases"], callback_data="my_purchases"))
    builder.row(InlineKeyboardButton(text=t["btn_lang"], callback_data="toggle_lang"))
    return builder.as_markup()

# ============================================================
# --- أوامر الأدمن ---
# ============================================================
@dp.message(Command("stats"))
async def bot_statistics(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect("store_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    conn.close()
    await message.answer(f"📊 **إحصائيات:**\n👥 `{total_users}` مستخدم")

@dp.message(Command("add_points"))
async def add_infinite_points(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    points_to_add = int(args[1]) if len(args) > 1 and args[1].isdigit() else 999999

    conn = sqlite3.connect("store_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (ADMIN_ID,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (user_id, points, referred_by, lang) VALUES (?, ?, NULL, 'ar')", (ADMIN_ID, points_to_add))
    else:
        cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points_to_add, ADMIN_ID))

    conn.commit()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (ADMIN_ID,))
    new_balance = cursor.fetchone()[0]
    conn.close()
    await message.answer(f"♾️ رصيدك: `{new_balance}`")

@dp.message(Command("give"))
async def give_points_to_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
        await message.answer("⚠️ `/give [ID] [points]`", parse_mode="Markdown")
        return

    target_user_id = int(args[1])
    points_to_give = int(args[2])

    conn = sqlite3.connect("store_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (target_user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (user_id, points, referred_by, lang) VALUES (?, ?, NULL, 'ar')", (target_user_id, points_to_give))
        new_balance = points_to_give
    else:
        cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points_to_give, target_user_id))
        cursor.execute("SELECT points FROM users WHERE user_id = ?", (target_user_id,))
        new_balance = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    await message.answer(f"✅ +{points_to_give} للمستخدم `{target_user_id}`\n💰 رصيده: `{new_balance}`")
    try:
        await bot.send_message(chat_id=target_user_id, text=f"🎁 **+{points_to_give} نقطة!**\n💰 رصيدك: `{new_balance}`")
    except Exception as e:
        logging.error(f"Failed: {e}")

@dp.message(Command("end"))
async def end_chat_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect("store_bot.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM admin_chat WHERE admin_id = ?", (ADMIN_ID,))
    conn.commit()
    conn.close()
    await message.answer("🔴 تم إنهاء الدردشة.")

@dp.message(Command("add_accounts"))
async def seed_accounts_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect("store_bot.db")
    cursor = conn.cursor()

    accounts_to_add = [
        ("re4remake", "pinokio542", "EYK2Y99Z2TK5"),
        ("godofwar", "seekkeygow2018", "XUgStsAmHGUM"),
        ("cyberpunk", "c21282", "asdAVXab21Z"),
        ("requiem", "egoros3p41", "siski33BFa9lCBU7O67483"),
        ("rdr2", "followinghoverfly3787", "f-r-e-e-akk-tg:@hyznet"),
        ("fifa26", "svfwqhmr6zrth7rj", "Ivancito2009_"),
        ("thelastofus", "thelast1q", "playerok.com/profile/QAVIX"),
        ("spiderman_all", "dimariba51", "https://funpay.com/users/6854301/"),
        ("miles", "jayderr20", "N2DddawdUKtF2"),
        ("forza", "fdxp23374", "Tp0Ea8Cr8Rs86t"),
        ("forza5", "forza5_store_user_01", "ForzaHorizon5_Secured_2026"),
        ("tsushima", "MythicStore_GOT_01", "https://t.me/Steam_Family"),
        ("batman", "batman_arkham_trilogy_user", "pass_arkham_123"),
        ("naruto", "wwsd7878", "f1010711"),
        ("plague1", "wbtq1088894", "steamok112233"),
        ("plague2", "largecaribou3324", "c6fc0ca33d154df11!aZ"),
        ("gta", "nutritiousasp8357", "c5df4230de97f2411!aZ"),
        ("watchdogs", "jp30ekXr", "wa72ITSA"),
        ("custom_user", "yxzt46984", "Edindzeko2007"),
        ("silenthill", "silenfx", "HOLOp2025?")
    ]

    added_count = 0
    for cat, user_val, pass_val in accounts_to_add:
        cursor.execute("SELECT id FROM accounts WHERE category = ? AND username = ?", (cat, user_val))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO accounts (username, password, category) VALUES (?, ?, ?)", (user_val, pass_val, cat))
            added_count += 1

    conn.commit()
    conn.close()
    await message.answer(f"✅ تمت الإضافة: `{added_count}`")

# ============================================================
# --- /start ---
# ============================================================
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split()

    ref_id = None
    if len(args) > 1 and args[1].isdigit():
        parsed_ref = int(args[1])
        if parsed_ref != user_id:
            ref_id = parsed_ref

    conn = sqlite3.connect("store_bot.db")
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, referred_by FROM users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()

    if not existing_user:
        valid_ref = None
        if ref_id:
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (ref_id,))
            if cursor.fetchone():
                valid_ref = ref_id

        cursor.execute("INSERT INTO users (user_id, points, referred_by, lang) VALUES (?, 0, ?, 'ar')", (user_id, valid_ref))
        conn.commit()
    else:
        if ref_id and not existing_user[1]:
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (ref_id,))
            if cursor.fetchone() and ref_id != user_id:
                cursor.execute("UPDATE users SET referred_by = ? WHERE user_id = ?", (ref_id, user_id))
                conn.commit()

    conn.close()

    if not await check_subscription(user_id):
        lang = get_lang(user_id)
        t = texts[lang]
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=t["btn_subscribe_ch1"], url=CHANNEL_LINK))
        builder.row(InlineKeyboardButton(text=t["btn_check_sub"], callback_data="check_sub"))
        await message.answer(t["sub_required"], reply_markup=builder.as_markup(), disable_web_page_preview=True)
        return

    # ✅ منح النقاط للمُحيل إذا المستخدم جديد ومشترك أصلاً
    conn = sqlite3.connect("store_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,))
    urow = cursor.fetchone()
    if urow and urow[0] and urow[0] > 0:
        ref_to_reward = urow[0]
        cursor.execute("UPDATE users SET referred_by = -1 WHERE user_id = ?", (user_id,))
        cursor.execute("UPDATE users SET points = points + 1 WHERE user_id = ?", (ref_to_reward,))
        conn.commit()

        cursor.execute("SELECT lang, points FROM users WHERE user_id = ?", (ref_to_reward,))
        r_data = cursor.fetchone()
        if r_data:
            r_lang, r_points = r_data
            notif_text = f"🎉 **New Referral!**\n💎 Balance: `{r_points}`" if r_lang == "en" else f"🎉 **دعوة جديدة!**\n💎 رصيدك: `{r_points}`"
            try:
                await bot.send_message(chat_id=ref_to_reward, text=notif_text)
            except Exception as e:
                logging.error(f"Failed: {e}")
    conn.close()

    lang = get_lang(user_id)
    t = texts[lang]
    await message.answer(t["welcome"], reply_markup=get_main_keyboard(lang))

# ============================================================
# --- التحقق ---
# ============================================================
@dp.callback_query(F.data == "check_sub")
async def verify_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = get_lang(user_id)
    t = texts[lang]

    if await check_subscription(user_id):
        conn = sqlite3.connect("store_bot.db")
        cursor = conn.cursor()

        cursor.execute("SELECT lang, referred_by, points FROM users WHERE user_id = ?", (user_id,))
        user_row = cursor.fetchone()

        if not user_row:
            cursor.execute("INSERT INTO users (user_id, points, referred_by, lang) VALUES (?, 0, NULL, 'ar')", (user_id,))
            conn.commit()
            referred_by = None
        else:
            _, referred_by, _ = user_row

        if referred_by and referred_by > 0:
            cursor.execute("UPDATE users SET points = points + 1 WHERE user_id = ?", (referred_by,))
            cursor.execute("UPDATE users SET referred_by = -1 WHERE user_id = ?", (user_id,))
            conn.commit()

            cursor.execute("SELECT lang, points FROM users WHERE user_id = ?", (referred_by,))
            ref_data = cursor.fetchone()
            if ref_data:
                ref_lang, new_ref_points = ref_data
                notif_text = f"🎉 **New Referral!**\n💎 Balance: `{new_ref_points}`" if ref_lang == "en" else f"🎉 **دعوة جديدة!**\n💎 رصيدك: `{new_ref_points}`"
                try:
                    await bot.send_message(chat_id=referred_by, text=notif_text)
                except Exception as e:
                    logging.error(f"Failed: {e}")

        conn.close()
        try:
            await callback.message.edit_text(t["welcome"], reply_markup=get_main_keyboard(lang))
        except Exception:
            await callback.message.answer(t["welcome"], reply_markup=get_main_keyboard(lang))
    else:
        await callback.answer(t["not_subscribed_yet"], show_alert=True)

# ============================================================
# --- القوائم ---
# ============================================================
@dp.callback_query(F.data == "toggle_lang")
async def toggle_lang(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not await check_subscription(user_id):
        await callback.answer("⚠️ اشترك أولاً!", show_alert=True)
        return
    current_lang = get_lang(user_id)
    new_lang = "en" if current_lang == "ar" else "ar"
    conn = sqlite3.connect("store_bot.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (new_lang, user_id))
    conn.commit()
    conn.close()
    t = texts[new_lang]
    await callback.message.edit_text(t["lang_changed"], reply_markup=get_main_keyboard(new_lang))
    await callback.answer()

@dp.callback_query(F.data == "account_info")
async def show_account_info(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if not await check_subscription(user_id):
        return
    lang = get_lang(user_id)
    conn = sqlite3.connect("store_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    points_row = cursor.fetchone()
    points = points_row[0] if points_row else 0
    conn.close()
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    t = texts[lang]
    text = t["account_info"].format(user_id, points, ref_link)
    share_text = "🔥 حسابات ألعاب قوية:" if lang == "ar" else "🔥 Free game accounts:"
    share_url = f"https://t.me/share/url?url={ref_link}&text={quote(share_text)}"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=t["btn_share"], url=share_url))
    builder.row(InlineKeyboardButton(text=t["btn_back"], callback_data="main_menu"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), disable_web_page_preview=True)

@dp.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if not await check_subscription(user_id):
        return
    lang = get_lang(user_id)
    t = texts[lang]
    await callback.message.edit_text(t["welcome"], reply_markup=get_main_keyboard(lang))

@dp.callback_query(F.data == "earn_points")
async def earn_points_menu(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if not await check_subscription(user_id):
        return
    lang = get_lang(user_id)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
    t = texts[lang]
    if lang == "ar":
        text = f"💎 **تجميع النقاط:**\n\nشارك رابطك → 1 نقطة لكل صديق جديد يتحقق!\n\n🔗 `{ref_link}`"
    else:
        text = f"💎 **Earn Points:**\n\nShare your link → 1 point per verified friend!\n\n🔗 `{ref_link}`"
    share_text = "🔥 حسابات ألعاب قوية:" if lang == "ar" else "🔥 Free game accounts:"
    share_url = f"https://t.me/share/url?url={ref_link}&text={quote(share_text)}"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=t["btn_share"], url=share_url))
    builder.row(InlineKeyboardButton(text=t["btn_back"], callback_data="main_menu"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), disable_web_page_preview=True)

# ============================================================
# --- الدفع ---
# ============================================================
def parse_points_payload(payload: str):
    parts = payload.split(":")
    if len(parts) != 3 or parts[0] != "points":
        return None
    try:
        user_id = int(parts[1])
        points = int(parts[2])
    except ValueError:
        return None
    if points not in POINT_PACKAGES:
        return None
    return user_id, points

@dp.callback_query(F.data == "buy_points_menu")
async def buy_points_menu_handler(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if not await check_subscription(user_id):
        return
    lang = get_lang(user_id)
    t = texts[lang]
    builder = InlineKeyboardBuilder()
    for points, stars in POINT_PACKAGES.items():
        button_text = f"💎 {points} نقطة — ⭐ {stars} نجوم" if lang == "ar" else f"💎 {points} points — ⭐ {stars} Stars"
        builder.row(InlineKeyboardButton(text=button_text, callback_data=f"buy_points_{points}"))
    builder.row(InlineKeyboardButton(text=t["btn_back"], callback_data="main_menu"))
    await callback.message.edit_text(t["buy_points_title"], reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("buy_points_"))
async def create_points_invoice(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if not await check_subscription(user_id):
        return
    lang = get_lang(user_id)
    try:
        points = int(callback.data.rsplit("_", 1)[1])
    except (ValueError, IndexError):
        return
    stars = POINT_PACKAGES.get(points)
    if stars is None:
        return
    payload = f"points:{callback.from_user.id}:{points}"
    title = f"شراء {points} نقطة" if lang == "ar" else f"Buy {points} Points"
    description = f"إضافة {points} نقطة." if lang == "ar" else f"Add {points} points."
    price_label = f"{points} نقطة" if lang == "ar" else f"{points} points"
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=title, description=description,
        payload=payload, currency="XTR",
        prices=[LabeledPrice(label=price_label, amount=stars)],
        start_parameter=f"buy_{points}_points"
    )

@dp.pre_checkout_query()
async def approve_points_payment(query: types.PreCheckoutQuery):
    parsed = parse_points_payload(query.invoice_payload)
    if not parsed:
        await query.answer(ok=False, error_message="خطأ.")
        return
    payload_user_id, points = parsed
    if query.currency != "XTR" or query.from_user.id != payload_user_id or query.total_amount != POINT_PACKAGES[points]:
        await query.answer(ok=False, error_message="بيانات غير متطابقة.")
        return
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def points_payment_success(message: types.Message):
    payment = message.successful_payment
    parsed = parse_points_payload(payment.invoice_payload)
    if not parsed:
        return
    payload_user_id, points = parsed
    if message.from_user.id != payload_user_id or payment.currency != "XTR" or payment.total_amount != POINT_PACKAGES[points]:
        return
    conn = sqlite3.connect("store_bot.db")
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute("""
            INSERT OR IGNORE INTO payments (telegram_charge_id, provider_charge_id, user_id, stars, points, payload)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (payment.telegram_payment_charge_id, payment.provider_payment_charge_id, message.from_user.id, payment.total_amount, points, payment.invoice_payload))
        is_new_payment = cursor.rowcount == 1
        if is_new_payment:
            cursor.execute("INSERT OR IGNORE INTO users (user_id, points, referred_by, lang) VALUES (?, 0, NULL, 'ar')", (message.from_user.id,))
            cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (points, message.from_user.id))
        cursor.execute("SELECT points FROM users WHERE user_id = ?", (message.from_user.id,))
        row = cursor.fetchone()
        new_balance = row[0] if row else 0
        conn.commit()
    except Exception:
        conn.rollback()
        return
    finally:
        conn.close()
    lang = get_lang(message.from_user.id)
    text = f"✅ تم الدفع!\n⭐ {payment.total_amount}\n💎 +{points}\n💰 {new_balance}" if lang == "ar" else f"✅ Paid!\n⭐ {payment.total_amount}\n💎 +{points}\n💰 {new_balance}"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=texts[lang]["btn_back"], callback_data="main_menu"))
    await message.answer(text, reply_markup=builder.as_markup())

# ============================================================
# --- المشتريات ---
# ============================================================
@dp.callback_query(F.data == "my_purchases")
async def show_my_purchases(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if not await check_subscription(user_id):
        return
    lang = get_lang(user_id)
    t = texts[lang]
    conn = sqlite3.connect("store_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.category, a.username, a.password FROM purchases p
        JOIN accounts a ON p.account_id = a.id
        WHERE p.user_id = ?
    """, (user_id,))
    purchased_accounts = cursor.fetchall()
    conn.close()
    if not purchased_accounts:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=t["btn_back"], callback_data="main_menu"))
        await callback.message.edit_text(t["no_purchases"], reply_markup=builder.as_markup())
        return
    builder = InlineKeyboardBuilder()
    for acc_id, cat, username, password in purchased_accounts:
        builder.row(InlineKeyboardButton(text=f"📁 {cat}", callback_data=f"show_acc_{acc_id}"))
    builder.row(InlineKeyboardButton(text=t["btn_back"], callback_data="main_menu"))
    await callback.message.edit_text(t["my_purchases_title"], reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("show_acc_"))
async def show_purchased_account_details(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if not await check_subscription(user_id):
        return
    try:
        acc_id = int(callback.data.split("_")[2])
    except (ValueError, IndexError):
        return
    conn = sqlite3.connect("store_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.username, a.password FROM purchases p
        JOIN accounts a ON p.account_id = a.id
        WHERE p.user_id = ? AND a.id = ?
    """, (user_id, acc_id))
    acc = cursor.fetchone()
    conn.close()
    if not acc:
        await callback.answer("❌ غير موجود.", show_alert=True)
        return
    username, password = acc
    text = f"🔐 **بيانات الحساب:**\n\n👤 `{username}`\n🔑 `{password}`"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ العودة", callback_data="my_purchases"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

# ============================================================
# --- Redeem ---
# ============================================================
@dp.callback_query(F.data == "redeem_menu")
async def redeem_menu(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if not await check_subscription(user_id):
        return
    lang = get_lang(user_id)
    t = texts[lang]
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Batman Arkham Knight +30 AAA (30 pts)", callback_data="redeem_spiderman_all"))
    builder.row(InlineKeyboardButton(text="🔥 RE4 Remake + 30 AAA (18 pts)", callback_data="redeem_re4remake"))
    builder.row(InlineKeyboardButton(text="🪓 God of War + Ragnarok (12 pts)", callback_data="redeem_godofwar"))
    builder.row(InlineKeyboardButton(text="🤖 Cyberpunk 2077 (12 pts)", callback_data="redeem_cyberpunk"))
    builder.row(InlineKeyboardButton(text="🧟 RE Requiem (10 pts)", callback_data="redeem_requiem"))
    builder.row(InlineKeyboardButton(text="🤠 RDR2 (6 pts)", callback_data="redeem_rdr2"))
    builder.row(InlineKeyboardButton(text="⚽ FC 26 (6 pts)", callback_data="redeem_fifa26"))
    builder.row(InlineKeyboardButton(text="🌿 The Last of Us I&II (6 pts)", callback_data="redeem_thelastofus"))
    builder.row(InlineKeyboardButton(text="🕷️ Spider-Man Miles (6 pts)", callback_data="redeem_miles"))
    builder.row(InlineKeyboardButton(text="🏎️ Forza Horizon 4 (6 pts)", callback_data="redeem_forza"))
    builder.row(InlineKeyboardButton(text="🏎️ Forza Horizon 5 (6 pts)", callback_data="redeem_forza5"))
    builder.row(InlineKeyboardButton(text="🗡️ Ghost of Tsushima (6 pts)", callback_data="redeem_tsushima"))
    builder.row(InlineKeyboardButton(text="🦇 Batman Trilogy (6 pts)", callback_data="redeem_batman"))
    builder.row(InlineKeyboardButton(text="🌀 Naruto Storm (6 pts)", callback_data="redeem_naruto"))
    builder.row(InlineKeyboardButton(text="🐀 A Plague Tale 1 (6 pts)", callback_data="redeem_plague1"))
    builder.row(InlineKeyboardButton(text="🐀 A Plague Tale 2 (6 pts)", callback_data="redeem_plague2"))
    builder.row(InlineKeyboardButton(text="🏎️ GTA V (4 pts)", callback_data="redeem_gta"))
    builder.row(InlineKeyboardButton(text="💻 Watch Dogs (3 pts)", callback_data="redeem_watchdogs"))
    builder.row(InlineKeyboardButton(text="🎁 Custom Account (3 pts)", callback_data="redeem_custom_user"))
    builder.row(InlineKeyboardButton(text="🌫️ Silent Hill f (8 pts)", callback_data="redeem_silenthill"))
    builder.row(InlineKeyboardButton(text=t["btn_back"], callback_data="main_menu"))
    await callback.message.edit_text(t["redeem_title"], reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("redeem_"))
async def process_redeem(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not await check_subscription(user_id):
        await callback.answer("⚠️ اشترك أولاً!", show_alert=True)
        return

    lang = get_lang(user_id)
    t = texts[lang]
    category = callback.data.replace("redeem_", "", 1)

    costs = {
