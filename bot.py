import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, LabeledPrice
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- إعدادات البوت والمدير ---
API_TOKEN = "8948074959:AAG5_PFOSO-pzNrZENuowrWA3HtdMyeIGfo"
ADMIN_ID = 6266959915
REQUIRED_CHANNELS = ["@r1iv_k"]

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

# --- قاعدة البيانات ---
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
            account_id INTEGER
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

    conn.commit()
    conn.close()

init_db()

# --- النصوص والترجمات ---
texts = {
    "ar": {
        "welcome": "أهلاً بك في متجر r1ivk Store 🎮\nاختر لغتك المفضلة أو استعرض الأقسام الجديدة من القائمة أدناه 👇.\n\n💬 **ملاحظة:** لأي استفسار أو مشكلة، أرسل رسالتك هنا وسأتلقاها شخصياً فوراً.",
        "lang_changed": "تم تغيير اللغة إلى العربية بنجاح! 🇸🇦",
        "btn_ref": "💎 تجميع رصيد (دعوة الأصدقاء)",
        "btn_info": "👤 معلومات حسابك",
        "btn_redeem": "🎁 استبدال النقاط (سحب حساب)",
        "btn_buy_points": "⭐ شراء نقاط بنجوم تيليجرام",
        "buy_points_title": "⭐ **شراء النقاط:**\n\nاختر الباقة المناسبة، وبعد تأكيد الدفع ستُضاف النقاط تلقائياً إلى رصيدك.",
        "btn_my_purchases": "📁 حساباتي المشراة",
        "btn_lang": "🌐 تغيير اللغة / Change Language",
        "account_info": "👤 **معلومات حسابك:**\n\n🆔 رقم المستخدم: `{}`\n💎 النقاط: `{}` نقطة\n\n🔗 رابط الدعوة الخاص بك:\n`{}`\n*(ستحصل على **1 نقطة** فوراً مقابل كل صديق جديد ينضم عبر رابطك!)*",
        "redeem_title": "🎁 **قسم استبدال الحسابات (متاحة للجميع بشكل دائم):**\n\nاختر نوع الحساب الذي تريد استبداله بنقاطك:",
        "my_purchases_title": "📁 **حساباتك المشراة (متاحة لك للأبد):**\n\nاضغط على الحساب لعرض بياناته متى شئت بدون خصم أي نقاط:",
        "no_purchases": "❌ لم تقم بشراء أي حسابات حتى الآن.",
        "no_accounts": "❌ عذراً، لا توجد حسابات متاحة حالياً في هذا القسم.",
        "not_enough_points": "⚠️ نقاطك غير كافية! يلزمك المزيد من النقاط لفتح هذا الحساب.",
        "success_redeem": "🎉 **مبروك! تم شراء الحساب بنجاح:**\n\n👤 **اسم المستخدم (Username):** `{}`\n🔑 **كلمة المرور (Password):**\n`{}`\n\n*(تم حفظ الحساب في سجلك للأبد)*",
        "btn_back": "⬅️ رجوع للقائمة الرئيسية",
        "btn_share": "📤 مشاركة الرابط مع الأصدقاء",
        "sub_required": "⚠️ **عذراً، يجب عليك الاشتراك في قنوات المتجر وشات القناة أولاً لكي تتمكن من استخدام البوت!**\n\nيرجى الانضمام إليهما ثم اضغط على زر التحقق أدناه 👇",
        "btn_subscribe_ch1": "📢 اشترك في القناة الأولى",
        "btn_subscribe_ch2": "💬 انضم لشات القناة",
        "btn_check_sub": "🔄 تحقق من الاشتراك",
        "not_subscribed_yet": "❌ لم تقم بالاشتراك في جميع القنوات بعد! يرجى الاشتراك ثم حاول مجدداً."
    },
    "en": {
        "welcome": "Welcome to r1ivk Store 🎮\nChoose your preferred language or explore the updated game sections below 👇.\n\n💬 **Note:** For any inquiry or issue, send your message here and I will receive it directly.",
        "lang_changed": "Language changed to English successfully! 🇬🇧",
        "btn_ref": "💎 Earn Points (Invite Friends)",
        "btn_info": "👤 Account Info",
        "btn_redeem": "🎁 Redeem Points",
        "btn_buy_points": "⭐ Buy Points with Telegram Stars",
        "buy_points_title": "⭐ **Buy Points:**\n\nChoose a package. Points will be added automatically after payment.",
        "btn_my_purchases": "📁 My Purchased Accounts",
        "btn_lang": "🌐 تغيير اللغة / Change Language",
        "account_info": "👤 **Account Info:**\n\n🆔 User ID: `{}`\n💎 Points: `{}` pts\n\n🔗 Your Referral Link:\n`{}`\n*(You will get **1 point** instantly for every new friend who joins via your link!)*",
        "redeem_title": "🎁 **Accounts Redemption Section (Unlimited Access):**\n\nChoose the account category you want to redeem:",
        "my_purchases_title": "📁 **Your Purchased Accounts (Yours Forever):**\n\nClick on any account to view its details anytime for free:",
        "no_purchases": "❌ You haven't purchased any accounts yet.",
        "no_accounts": "❌ Sorry, no accounts are currently available in this category.",
        "not_enough_points": "⚠️ Not enough points! You need more points to redeem this account.",
        "success_redeem": "🎉 **Congratulations! Account purchased successfully:**\n\n👤 **Username:** `{}`\n🔑 **Password:**\n`{}`\n*(Saved to your profile forever)*",
        "btn_back": "Main Menu",
        "btn_share": "📤 Share Link with Friends",
        "sub_required": "⚠️ **Sorry, you must subscribe to the store channels first to use this bot!**\n\nPlease join them and click the check button below 👇",
        "btn_subscribe_ch1": "📢 Subscribe to Channel 1",
        "btn_subscribe_ch2": "💬 Join Channel Chat",
        "btn_check_sub": "🔄 Check Subscription",
        "not_subscribed_yet": "❌ You haven't subscribed to all channels yet! Please subscribe and try again."
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
        return False

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

@dp.message(Command("stats"))
async def bot_statistics(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    conn = sqlite3.connect("store_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    conn.close()
    await message.answer(f"📊 **إحصائيات البوت:**\n\n👥 إجمالي عدد المستخدمين: `{total_users}` مستخدم")

@dp.message(Command("add_points"))
async def add_admin_points(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    amount = int(args[1]) if len(args) > 1 and args[1].isdigit() else 100

    conn = sqlite3.connect("store_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, points, referred_by, lang) VALUES (?, 0, NULL, 'ar')", (ADMIN_ID,))
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, ADMIN_ID))
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (ADMIN_ID,))
    new_points = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    await message.answer(f"💎 تمت إضافة `{amount}` نقطة إلى رصيدك بنجاح!\n💰 رصيدك الحالي: `{new_points}` نقطة.")

@dp.message(Command("give"))
async def give_points_to_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 3 or not args[1].isdigit() or not args[2].isdigit():
        await message.answer("⚠️ الاستخدام الصحيح:\n`/give [آيدي_المستخدم] [عدد_النقاط]`", parse_mode="Markdown")
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

    await message.answer(f"✅ تمت إضافة `{points_to_give}` نقطة للمستخدم `{target_user_id}` بنجاح!\n💰 رصيده الحالي: `{new_balance}` نقطة.")
    try:
        await bot.send_message(chat_id=target_user_id, text=f"🎁 **تم شحن رصيدك! أضاف لك المدير `{points_to_give}` نقطة.**\n💰 رصيدك الحالي: `{new_balance}` نقطة.")
    except Exception as e:
        logging.error(f"Failed to notify user: {e}")

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
        ("requiem", "req_user_official_1984", "pass_req_secure_99"),
        ("rdr2", "followinghoverfly3787", "f-r-e-e-akk-tg:@hyznet"),
        ("fifa26", "svfwqhmr6zrth7rj", "Ivancito2009_"),
        ("thelastofus", "thelast1q", "playerok.com/profile/QAVIX"),
        ("spiderman_all", "hamorilal", "Gk6q63F1"),
        ("miles", "jayderr20", "N2DddawdUKtF2"),
        ("forza", "duhl15773", "Muhammadknio12!"),
        ("forza5", "forza5_store_user_01", "ForzaHorizon5_Secured_2026"),
        ("tsushima", "MythicStore_GOT_01", "https://t.me/Steam_Family"),
        ("batman", "batman_arkham_trilogy_user", "pass_arkham_123"),
        ("naruto", "naruto_storm_series_pc", "pass_naruto_storm_99"),
        ("plague1", "aplaguetale_innocence_pc", "pass_plague_innocence_1"),
        ("plague2", "aplaguetale_requiem_pc", "pass_plague_requiem_2"),
        ("gta", "nutritiousasp8357", "c5df4230de97f2411!aZ"),
        ("watchdogs", "jp30ekXr", "wa72ITSA"),
        ("netflix", "netflix_premium_acc_01", "pass_net_789"),
        ("steam", "random_steam_user_01", "steam_pass_secure_123"),
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
    await message.answer(f"✅ تمت إضافة الحسابات بنجاح!\n📦 عدد الحسابات الجديدة المضافة: `{added_count}`")

pending_referrals = {}

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
        referred_by = None
        if ref_id:
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (ref_id,))
            if cursor.fetchone():
                referred_by = ref_id

        cursor.execute("INSERT INTO users (user_id, points, referred_by, lang) VALUES (?, 0, ?, 'ar')", (user_id, referred_by))
        conn.commit()
        if ref_id:
            pending_referrals[user_id] = ref_id
    else:
        if ref_id and not existing_user[1]:
            pending_referrals[user_id] = ref_id

    conn.close()

    if not await check_subscription(user_id):
        if ref_id:
            pending_referrals[user_id] = ref_id
        lang = get_lang(user_id)
        t = texts[lang]
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=t["btn_subscribe_ch1"], url=f"https://t.me/{REQUIRED_CHANNELS[0].replace('@', '')}"))
        builder.row(InlineKeyboardButton(text=t["btn_subscribe_ch2"], url=f"https://t.me/{REQUIRED_CHANNELS[1].replace('@', '')}"))
        builder.row(InlineKeyboardButton(text=t["btn_check_sub"], callback_data="check_sub"))
        await message.answer(t["sub_required"], reply_markup=builder.as_markup())
        return

    lang = get_lang(user_id)
    t = texts[lang]
    await message.answer(t["welcome"], reply_markup=get_main_keyboard(lang))

@dp.callback_query(F.data == "check_sub")
async def verify_subscription(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = get_lang(user_id)
    t = texts[lang]

    if await check_subscription(user_id):
        conn = sqlite3.connect("store_bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT lang, referred_by FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            ref_id = pending_referrals.get(user_id)
            cursor.execute("INSERT INTO users (user_id, points, referred_by, lang) VALUES (?, 0, ?, 'ar')", (user_id, ref_id))
            conn.commit()
            user = ('ar', ref_id)

        lang, referred_by = user

        if not referred_by and user_id in pending_referrals:
            referred_by = pending_referrals[user_id]
            cursor.execute("UPDATE users SET referred_by = ? WHERE user_id = ?", (referred_by, user_id))
            conn.commit()

        if referred_by:
            cursor.execute("SELECT points FROM users WHERE user_id = ?", (referred_by,))
            if cursor.fetchone():
                cursor.execute("UPDATE users SET points = points + 1 WHERE user_id = ?", (referred_by,))
                conn.commit()
                cursor.execute("SELECT lang, points FROM users WHERE user_id = ?", (referred_by,))
                ref_data = cursor.fetchone()
                if ref_data:
                    ref_lang, new_ref_points = ref_data
                    notif_text = f"🎉 **New Referral!**\n\n👤 A new person joined via your link.\n💎 Your balance is now: `{new_ref_points}` pts." if ref_lang == "en" else f"🎉 **تم تسجيل دعوة جديدة!**\n\n👤 انضم شخص جديد عبر رابطك.\n💎 زاد رصيدك وأصبح: `{new_ref_points}` نقطة."
                    try:
                        await bot.send_message(chat_id=referred_by, text=notif_text)
                    except Exception as e:
                        logging.error(f"Failed to send notification: {e}")
            if user_id in pending_referrals:
                del pending_referrals[user_id]

        conn.close()
        await callback.message.edit_text(t["welcome"], reply_markup=get_main_keyboard(lang))
    else:
        await callback.answer(t["not_subscribed_yet"], show_alert=True)

@dp.callback_query(F.data == "toggle_lang")
async def toggle_lang(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if not await check_subscription(user_id):
        await callback.answer("⚠️ يجب الاشتراك في القنوات أولاً!", show_alert=True)
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
    share_text = "🔥 احصل على حسابات ألعاب قوية مجاناً عبر الانضمام لهذا المتجر المميز:" if lang == "ar" else "🔥 Get free game accounts by joining this awesome store:"
    share_url = f"https://t.me/share/url?url={ref_link}&text={share_text}"

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
        text = f"💎 **طريقة تجميع النقاط (دعوة الأصدقاء):**\n\nقم بمشاركة رابط الدعوة الخاص بك مع أصدقائك أو في المجموعات.\nلكل شخص جديد يدخل البوت عبر رابطك، ستحصل أنت على **1 نقطة** فوراً!\n\n🔗 رابطك الخاص:\n`{ref_link}`"
    else:
        text = f"💎 **How to earn points (Invite Friends):**\n\nShare your referral link with friends or groups.\nFor every new person who joins via your link, you will get **1 point** instantly!\n\n🔗 Your link:\n`{ref_link}`"

    share_text = "🔥 احصل على حسابات ألعاب قوية مجاناً عبر الانضمام لهذا المتجر المميز:" if lang == "ar" else "🔥 Get free game accounts by joining this awesome store:"
    share_url = f"https://t.me/share/url?url={ref_link}&text={share_text}"

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=t["btn_share"], url=share_url))
    builder.row(InlineKeyboardButton(text=t["btn_back"], callback_data="main_menu"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup(), disable_web_page_preview=True)

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
    description = f"إضافة {points} نقطة إلى رصيدك داخل البوت." if lang == "ar" else f"Add {points} points to your bot balance."
    price_label = f"{points} نقطة" if lang == "ar" else f"{points} points"

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=title,
        description=description,
        payload=payload,
        currency="XTR",
        prices=[LabeledPrice(label=price_label, amount=stars)],
        start_parameter=f"buy_{points}_points"
    )

@dp.pre_checkout_query()
async def approve_points_payment(query: types.PreCheckoutQuery):
    parsed = parse_points_payload(query.invoice_payload)
    if not parsed:
        await query.answer(ok=False, error_message="تعذر التحقق من الباقة.")
        return
    payload_user_id, points = parsed
    if query.currency != "XTR" or query.from_user.id != payload_user_id or query.total_amount != POINT_PACKAGES[points]:
        await query.answer(ok=False, error_message="بيانات الدفع غير متطابقة.")
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
    text = f"✅ تم الدفع بنجاح!\n\n⭐ المدفوع: {payment.total_amount} نجمة\n💎 تمت إضافة: {points} نقطة\n💰 رصيدك الحالي: {new_balance} نقطة" if lang == "ar" else f"✅ Payment successful!\n\n⭐ Paid: {payment.total_amount} Stars\n💎 Added: {points} points\n💰 Current balance: {new_balance} points"
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=texts[lang]["btn_back"], callback_data="main_menu"))
    await message.answer(text, reply_markup=builder.as_markup())

@dp.callback_query(F.data == "redeem_menu")
async def redeem_menu(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if not await check_subscription(user_id):
        return

    lang = get_lang(user_id)
    t = texts[lang]

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔥 Resident Evil 4 Remake + 30 AAA Games (18 pts)", callback_data="redeem_re4remake"))
    builder.row(InlineKeyboardButton(text="🪓 God of War (2018) + Ragnarok (12 pts)", callback_data="redeem_godofwar"))
    builder.row(InlineKeyboardButton(text="🤖 Cyberpunk 2077 (12 pts)", callback_data="redeem_cyberpunk"))
    builder.row(InlineKeyboardButton(text="🧟 Resident Evil Requiem (10 pts)", callback_data="redeem_requiem"))
    builder.row(InlineKeyboardButton(text="🤠 Red Dead Redemption 2 (6 pts)", callback_data="redeem_rdr2"))
    builder.row(InlineKeyboardButton(text="⚽ FC 26 / FIFA 26 (6 pts)", callback_data="redeem_fifa26"))
    builder.row(InlineKeyboardButton(text="🌿 The Last of Us Part I & II (6 pts)", callback_data="redeem_thelastofus"))
    builder.row(InlineKeyboardButton(text="🕷️ جميع اجزاء سبايدر مان 1 2 3 (10 pts)", callback_data="redeem_spiderman_all"))
    builder.row(InlineKeyboardButton(text="🕷️ Spider-Man: Miles Morales (6 pts)", callback_data="redeem_miles"))
    builder.row(InlineKeyboardButton(text="🏎️ Forza Horizon 4 (6 pts)", callback_data="redeem_forza"))
    builder.row(InlineKeyboardButton(text="🏎️ Forza Horizon 5 (6 pts)", callback_data="redeem_forza5"))
    builder.row(InlineKeyboardButton(text="🗡️ Ghost of Tsushima (Gold Edition) (6 pts)", callback_data="redeem_tsushima"))
    builder.row(InlineKeyboardButton(text="🦇 Batman Arkham Trilogy (6 pts)", callback_data="redeem_batman"))
    builder.row(InlineKeyboardButton(text="🌀 Naruto Shippuden: Ultimate Ninja Storm (6 pts)", callback_data="redeem_naruto"))
    builder.row(InlineKeyboardButton(text="🐀 A Plague Tale: Innocence (Part 1) (6 pts)", callback_data="redeem_plague1"))
    builder.row(InlineKeyboardButton(text="🐀 A Plague Tale: Requiem (Part 2) (6 pts)", callback_data="redeem_plague2"))
    builder.row(InlineKeyboardButton(text="🏎️ GTA V Account (4 pts)", callback_data="redeem_gta"))
    builder.row(InlineKeyboardButton(text="💻 Watch Dogs (3 pts)", callback_data="redeem_watchdogs"))
    builder.row(InlineKeyboardButton(text="🍿 Netflix Account (2 pts)", callback_data="redeem_netflix"))
    builder.row(InlineKeyboardButton(text="🎮 حساب ستيم عشوائي (1 pts)", callback_data="redeem_steam"))
    builder.row(InlineKeyboardButton(text="🎁 حساب مخصص / Custom Account (3 pts)", callback_data="redeem_custom_user"))
    builder.row(InlineKeyboardButton(text="🌫️ Silent Hill f Deluxe (8 pts)", callback_data="redeem_silenthill"))
    builder.row(InlineKeyboardButton(text=t["btn_back"], callback_data="main_menu"))

    await callback.message.edit_text(t["redeem_title"], reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("redeem_"))
async def process_redeem(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    if not await check_subscription(user_id):
        return

    lang = get_lang(user_id)
    t = texts[lang]
    category = callback.data.replace("redeem_", "", 1)

    costs = {
        "re4remake": 18, "godofwar": 12, "cyberpunk": 12, "requiem": 10,
        "rdr2": 6, "fifa26": 6, "thelastofus": 6, "spiderman_all": 10,
        "miles": 6, "forza": 6, "forza5": 6, "tsushima": 6,
        "batman": 6, "naruto": 6, "plague1": 6, "plague2": 6,
        "gta": 4, "watchdogs": 3, "netflix": 2, "steam": 1,
        "custom_user": 3, "silenthill": 8
    }

    required_points = costs.get(category, 5)

    conn = sqlite3.connect("store_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    user_row = cursor.fetchone()
    user_points = user_row[0] if user_row else 0

    if user_points < required_points:
        conn.close()
        await callback.answer(t["not_enough_points"], show_alert=True)
        return

    cursor.execute("""
        SELECT id, username, password FROM accounts 
        WHERE category = ? 
        ORDER BY RANDOM() LIMIT 1
    """, (category,))
    account = cursor.fetchone()

    if not account:
        conn.close()
        await callback.answer(t["no_accounts"], show_alert=True)
        return

    acc_id, acc_user, acc_pass = account

    cursor.execute("UPDATE users SET points = points - ? WHERE user_id = ?", (required_points, user_id))
    cursor.execute("INSERT INTO purchases (user_id, account_id) VALUES (?, ?)", (user_id, acc_id))
    conn.commit()
    conn.close()

    success_text = t["success_redeem"].format(acc_user, acc_pass)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=t["btn_back"], callback_data="main_menu"))
    await callback.message.edit_text(success_text, reply_markup=builder.as_markup())

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
        SELECT a.username, a.password, a.category FROM purchases p
        JOIN accounts a ON p.account_id = a.id
        WHERE p.user_id = ?
    """, (user_id,))
    purchases = cursor.fetchall()
    conn.close()

    if not purchases:
        await callback.message.edit_text(t["no_purchases"], reply_markup=InlineKeyboardBuilder().row(InlineKeyboardButton(text=t["btn_back"], callback_data="main_menu")).as_markup())
        return

    text = f"{t['my_purchases_title']}\n\n"
    for idx, (u, p, cat) in enumerate(purchases, 1):
        text += f"📦 {idx} - **{cat}**\n👤 ` {u} `\n🔑 ` {p} `\n-------------------\n"

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=t["btn_back"], callback_data="main_menu"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_user_messages(message: types.Message):
    user_id = message.from_user.id
    
    if user_id == ADMIN_ID:
        return

    forward_text = (
        f"📩 **رسالة جديدة من عميل / مستخدم:**\n\n"
        f"👤 الاسم: {message.from_user.full_name}\n"
        f"🆔 الآيدي: `{user_id}`\n\n"
        f"💬 النص:\n{message.text}"
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💬 مراسلة المستخدم (خاص)", url=f"tg://user?id={user_id}"))

    try:
        await bot.send_message(ADMIN_ID, forward_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
        await message.answer("✅ تم إرسال رسالتك إلى إدارة المتجر بنجاح، سيتم الرد عليك قريباً.")
    except Exception as e:
        logging.error(f"Failed to forward message to admin: {e}")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
