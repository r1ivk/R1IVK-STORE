import logging
import telebot
from telebot import types

# ضع التوكن الخاص بك هنا بحذر وتجنب نشره علناً لتفادي تنبيهات الأمان
TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_ID = 123456789  # ضع آيدي الحساب الخاص بك كمشرف

bot = telebot.TeleBot(TOKEN)
logging.basicConfig(level=logging.INFO)

# قاعدة بيانات مؤقتة لتخزين النقاط والحسابات
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"points": 0, "purchased": []}
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_store = types.InlineKeyboardButton("🛒 متجر الحسابات", callback_data="store")
    btn_profile = types.InlineKeyboardButton("👤 معلومات حسابك", callback_data="profile")
    btn_support = types.InlineKeyboardButton("💬 تواصل مع الدعم", callback_data="support")
    markup.add(btn_store, btn_profile, btn_support)
    
    bot.send_message(
        message.chat.id, 
        "أهلاً بك في متجر الحسابات والخدمات الرقمية!\nاختر ما يناسبك من القائمة أدناه:", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"points": 0, "purchased": []}

    if call.data == "profile":
        points = user_data[user_id]["points"]
        purchased_count = len(user_data[user_id]["purchased"])
        text = (
            f"👤 **معلومات حسابك:**\n"
            f"🆔 الآيدي: `{user_id}`\n"
            f"⭐ رصيد النقاط: {points}\n"
            f"📦 الحسابات المشتراة: {purchased_count}"
        )
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

    elif call.data == "store":
        markup = types.InlineKeyboardMarkup()
        btn_buy = types.InlineKeyboardButton("🎮 شراء حساب (10 نقاط)", callback_data="buy_account")
        markup.add(btn_buy)
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "🛒 **قسم المتجر:**\nاختر الحساب المناسب لرصيدك:", 
            call.message.chat.id, 
            call.message.message_id, 
            reply_markup=markup, 
            parse_mode="Markdown"
        )

    elif call.data == "buy_account":
        if user_data[user_id]["points"] >= 10:
            user_data[user_id]["points"] -= 10
            account_info = "🎮 حساب لعبة مميز: User: sample@game.com | Pass: 123456"
            user_data[user_id]["purchased"].append(account_info)
            bot.answer_callback_query(call.id, "تم الشراء بنجاح!")
            bot.send_message(call.message.chat.id, f"✅ تم شراء الحساب بنجاح:\n`{account_info}`", parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "رصيدك غير كافي!", show_alert=True)

    elif call.data == "support":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "✍️ أرسل رسالتك الآن وسيقوم المدير بالرد عليك في أقرب وقت:")
        bot.register_next_step_handler(msg, forward_to_admin)

def forward_to_admin(message):
    user_id = message.from_user.id
    username = message.from_user.username or "بدون معرف"
    text = message.text

    markup = types.InlineKeyboardMarkup()
    btn_reply = types.InlineKeyboardButton("💬 رد على المستخدم", callback_data=f"reply_{user_id}")
    markup.add(btn_reply)

    bot.send_message(
        ADMIN_ID, 
        f"📩 رسالة جديدة من:\n👤 الاسم: {message.from_user.first_name}\n🔗 المعرف: @{username}\n🆔 الآيدي: `{user_id}`\n\n💬 النص:\n{text}", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )
    bot.send_message(message.chat.id, "✅ تم إرسال رسالتك للمشرف بنجاح.")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
