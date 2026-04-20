import asyncio
import threading
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

app_instance = None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ehehe~ Hii! Main hoon Cyra! Tumhara personal AI companion~! Kya haal hai? 🌸"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from modules.llm import chat
    from modules.memory import save_memory

    user_message = update.message.text
    user_name = update.message.from_user.first_name

    print(f"\n[Telegram] {user_name}: {user_message}")

    history = context.user_data.get("history", [])

    response, history = chat(user_message, history)
    context.user_data["history"] = history

    reply = response["response"]
    emotion = response["emotion"]

    emotion_emojis = {
        "happy": "😊",
        "excited": "🎉",
        "sad": "😢",
        "curious": "🤔",
        "concerned": "😟",
        "angry": "😤",
        "surprised": "😲",
        "neutral": "💬"
    }

    emoji = emotion_emojis.get(emotion, "💬")
    await update.message.reply_text(f"{emoji} {reply}")

    if response.get("action") and response["action"] not in ["see_screen", "see_webcam"]:
        from modules.agent import handle_action
        result = handle_action(response["action"], response.get("params"))
        if result:
            await update.message.reply_text(f"✅ {result}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming photos and save as background.png."""
    user_name = update.message.from_user.first_name
    print(f"\n[Telegram] {user_name} sent a photo.")
    
    photo_file = await update.message.photo[-1].get_file()
    save_path = "background.png"
    await photo_file.download_to_drive(save_path)
    
    await update.message.reply_text("📸 Wah! Kitni sundar photo hai! Maine ise background ke liye save kar liya hai. Apply karne ke liye /setbg bolo! ✨")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🌸 Main hoon Cyra! Yeh sab kar sakti hoon:

💬 Baat karo — bas message karo!
🎵 /play [song] — gaana chalao
⏯️ /pause (ya /playpause) — media pause/resume karo
🌤 /weather [city] — weather batao  
📝 /note [text] — note save karo
📋 /notes — notes dekho
⏱ /timer [minutes] — timer set karo
📸 /screenshot — screenshot lo
📸 /livescreenshot — har 30 sec screenshot
🔊 /volume [0-100] — volume set karo
📰 /briefing — daily briefing
📁 /sendfile [filename] — PC se file bhejo
📂 /sendfolder [folder] — folder ki files bhejo
🔒 /lockpc — PC lock karo
⚠️ /shutdown — PC band karo
🔄 /restart — PC restart karo
🖼 /setbg — Uploaded photo ko wallpaper banao
📱 /remotemsg [name]|[msg] — WhatsApp message bhejo
⏰ /alarm [time] — alarm set karo
🖱 /mouse [up/down/left/right/click] — mouse control
⌨️ /type [text] — PC pe type karo
🌐 /myip — PC ka IP address
📋 /clipboard — clipboard content
🖥 /processes — running apps
💻 /run [command] — terminal command run karo
📧 /email [to]|[subject]|[body] — email bhejo
"""
    await update.message.reply_text(help_text)

async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from modules.agent import handle_action
    query = " ".join(context.args)
    if query:
        result = handle_action("play_song", query)
        await update.message.reply_text(f"🎵 {result}")
    else:
        await update.message.reply_text("Kya gaana chalana hai? /play [song name]")

async def playpause_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from modules.agent import handle_action
    result = handle_action("media_play_pause", None)
    await update.message.reply_text(f"⏯️ {result}")

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from modules.agent import handle_action
    city = " ".join(context.args) if context.args else "Delhi"
    result = handle_action("weather", city)
    await update.message.reply_text(f"🌤 {result}")

async def note_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from modules.agent import handle_action
    note = " ".join(context.args)
    if note:
        result = handle_action("save_note", note)
        await update.message.reply_text(f"📝 {result}")
    else:
        await update.message.reply_text("Kya note karna hai? /note [text]")

async def notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from modules.agent import handle_action
    result = handle_action("read_notes", None)
    await update.message.reply_text(f"📋 {result}")

async def timer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from modules.agent import handle_action, parse_timer, set_timer
    minutes = " ".join(context.args) if context.args else "5"
    seconds, message = parse_timer(f"{minutes} minutes")
    result = set_timer(seconds, message)
    await update.message.reply_text(f"⏱ {result}")

async def screenshot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from modules.agent import take_screenshot
    import glob

    result = take_screenshot()
    screenshots_dir = os.path.expanduser("~") + r"\Pictures\Cyra Screenshots"
    files = glob.glob(os.path.join(screenshots_dir, "*.png"))

    if files:
        latest = max(files, key=os.path.getctime)
        await update.message.reply_photo(photo=open(latest, "rb"))
        await update.message.reply_text(f"📸 {result}")
    else:
        await update.message.reply_text(f"📸 {result}")

async def volume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from modules.agent import handle_action
    level = " ".join(context.args) if context.args else "50"
    result = handle_action("volume_set", level)
    await update.message.reply_text(f"🔊 {result}")

async def briefing_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from modules.agent import handle_action
    result = handle_action("daily_briefing", None)
    await update.message.reply_text(f"📰 {result}")

async def bulb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from modules.smart_home import turn_on_bulb, turn_off_bulb, set_brightness, set_color
    
    args = context.args
    if not args:
        await update.message.reply_text("""
💡 Bulb commands:
/bulb on — jalao
/bulb off — band karo
/bulb brightness 50 — brightness set karo
/bulb color red — color change karo
        """)
        return
    
    action = args[0].lower()
    
    if action == "on":
        result = turn_on_bulb()
    elif action == "off":
        result = turn_off_bulb()
    elif action == "brightness" and len(args) > 1:
        result = set_brightness(args[1])
    elif action == "color" and len(args) > 1:
        result = set_color(args[1])
    else:
        result = "Command samajh nahi aaya!"
    
    await update.message.reply_text(f"💡 {result}")

async def email_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from modules.email_handler import send_email
    args = " ".join(context.args)
    
    if "|" not in args:
        await update.message.reply_text("Format: /email to@gmail.com|Subject|Body")
        return
    
    parts = args.split("|")
    to = parts[0].strip()
    subject = parts[1].strip() if len(parts) > 1 else "No Subject"
    body = parts[2].strip() if len(parts) > 2 else ""
    
    result = send_email(to, subject, body)
    await update.message.reply_text(f"📧 {result}") 

async def sendfile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for a file on the PC and send it via Telegram."""
    filename = " ".join(context.args)
    if not filename:
        await update.message.reply_text("Kaunsi file chahiye? /sendfile [filename]")
        return

    await update.message.reply_text(f"🔍 '{filename}' dhundh rahi hoon...")

    search_paths = [
        os.path.expanduser("~") + r"\Desktop",
        os.path.expanduser("~") + r"\Documents",
        os.path.expanduser("~") + r"\Downloads",
        os.path.expanduser("~") + r"\Pictures",
        os.path.expanduser("~") + r"\Videos",
        os.path.expanduser("~") + r"\Music",
    ]

    found_files = []
    for path in search_paths:
        if not os.path.exists(path):
            continue
        for root, dirs, files in os.walk(path):
            for file in files:
                if filename.lower() in file.lower():
                    found_files.append(os.path.join(root, file))

    if not found_files:
        await update.message.reply_text(f"❌ '{filename}' nahi mila!")
        return

    if len(found_files) > 1:
        file_list = "\n".join([f"{i+1}. {os.path.basename(f)}" for i, f in enumerate(found_files[:5])])
        await update.message.reply_text(f"Multiple files mili:\n{file_list}\n\nSabhi bhej rahi hoon!")

    for file_path in found_files[:3]:
        try:
            file_size = os.path.getsize(file_path)
            if file_size > 50 * 1024 * 1024:
                await update.message.reply_text(f"⚠️ {os.path.basename(file_path)} bahut badi hai (50MB+)")
                continue

            await update.message.reply_text(f"📤 Bhej rahi hoon: {os.path.basename(file_path)}")
            with open(file_path, "rb") as f:
                await update.message.reply_document(document=f, filename=os.path.basename(file_path))
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

async def lockpc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        await update.message.reply_text("🔒 PC lock kar diya!")
    except Exception as e:
        await update.message.reply_text(f"❌ Lock nahi hua: {str(e)}")

async def shutdown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from modules.agent import handle_action
    await update.message.reply_text("⚠️ PC shutdown ho raha hai 10 seconds mein!")
    await asyncio.sleep(2)
    handle_action("shutdown", None)

async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from modules.agent import handle_action
    await update.message.reply_text("⚠️ PC restart ho raha hai 10 seconds mein!")
    await asyncio.sleep(2)
    handle_action("restart", None)

async def sendfolder_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for a folder on the PC and send its files via Telegram."""
    folder_name = " ".join(context.args)
    if not folder_name:
        await update.message.reply_text("Kaunsa folder chahiye? /sendfolder [folder name]")
        return

    search_paths = [
        os.path.expanduser("~") + r"\Desktop",
        os.path.expanduser("~") + r"\Documents",
        os.path.expanduser("~") + r"\Downloads",
    ]

    found_folder = None
    for path in search_paths:
        if not os.path.exists(path):
            continue
        for root, dirs, files in os.walk(path):
            for d in dirs:
                if folder_name.lower() in d.lower():
                    found_folder = os.path.join(root, d)
                    break
            if found_folder:
                break
        if found_folder:
            break

    if not found_folder:
        await update.message.reply_text(f"❌ '{folder_name}' folder nahi mila!")
        return

    files = os.listdir(found_folder)
    if not files:
        await update.message.reply_text("Folder empty hai!")
        return

    await update.message.reply_text(f"📁 {len(files)} files mil gayi — pehli kuch bhej rahi hoon!")

    sent = 0
    for file in files[:5]:
        file_path = os.path.join(found_folder, file)
        if os.path.isfile(file_path):
            try:
                file_size = os.path.getsize(file_path)
                if file_size < 50 * 1024 * 1024:
                    with open(file_path, "rb") as f:
                        await update.message.reply_document(
                            document=f,
                            filename=file
                        )
                    sent += 1
            except:
                pass

    await update.message.reply_text(f"✅ {sent} files send kar di!")

async def alarm_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from modules.agent import set_alarm
    time_str = " ".join(context.args)
    if not time_str:
        await update.message.reply_text("Format: /alarm 7:30 AM")
        return
    result = set_alarm(time_str)
    await update.message.reply_text(f"⏰ {result}")

async def mouse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import pyautogui
    args = context.args
    
    if not args:
        await update.message.reply_text("""
🖱 Mouse commands:
/mouse up [pixels]
/mouse down [pixels]
/mouse left [pixels]
/mouse right [pixels]
/mouse click
/mouse rightclick
/mouse doubleclick
/mouse scroll up
/mouse scroll down
        """)
        return
    
    action = args[0].lower()
    amount = int(args[1]) if len(args) > 1 and args[1].isdigit() else 100
    
    try:
        if action == "up":
            pyautogui.moveRel(0, -amount)
            await update.message.reply_text(f"🖱 Mouse {amount}px upar!")
        elif action == "down":
            pyautogui.moveRel(0, amount)
            await update.message.reply_text(f"🖱 Mouse {amount}px neeche!")
        elif action == "left":
            pyautogui.moveRel(-amount, 0)
            await update.message.reply_text(f"🖱 Mouse {amount}px left!")
        elif action == "right":
            pyautogui.moveRel(amount, 0)
            await update.message.reply_text(f"🖱 Mouse {amount}px right!")
        elif action == "click":
            pyautogui.click()
            await update.message.reply_text("🖱 Click kar diya!")
        elif action == "rightclick":
            pyautogui.rightClick()
            await update.message.reply_text("🖱 Right click kar diya!")
        elif action == "doubleclick":
            pyautogui.doubleClick()
            await update.message.reply_text("🖱 Double click kar diya!")
        elif action == "scroll":
            direction = args[1].lower() if len(args) > 1 else "up"
            if direction == "up":
                pyautogui.scroll(3)
                await update.message.reply_text("🖱 Scroll up kar diya!")
            else:
                pyautogui.scroll(-3)
                await update.message.reply_text("🖱 Scroll down kar diya!")
        else:
            await update.message.reply_text("Command nahi pata!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def type_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import pyautogui
    import pyperclip
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Kya type karna hai? /type [text]")
        return
    try:
        pyperclip.copy(text)
        pyautogui.hotkey("ctrl", "v")
        await update.message.reply_text(f"⌨️ Type kar diya: {text}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def myip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        import requests
        ip = requests.get("https://api.ipify.org").text
        await update.message.reply_text(f"🌐 Tera public IP: `{ip}`", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ IP nahi mila: {str(e)}")

async def processes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import psutil
    procs = []
    for proc in psutil.process_iter(['name', 'memory_info']):
        try:
            name = proc.info['name']
            mem = proc.info['memory_info'].rss // 1024 // 1024
            if mem > 50:
                procs.append((name, mem))
        except:
            pass
    
    procs.sort(key=lambda x: x[1], reverse=True)
    
    result = "🖥 Top running processes:\n"
    for name, mem in procs[:10]:
        result += f"• {name} — {mem}MB\n"
    
    await update.message.reply_text(result)

async def clipboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import pyperclip
    try:
        content = pyperclip.paste()
        if content:
            await update.message.reply_text(f"📋 Clipboard:\n{content[:1000]}")
        else:
            await update.message.reply_text("Clipboard empty hai!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def run_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = " ".join(context.args)
    if not cmd:
        await update.message.reply_text("Kaunsa command run karna hai? /run [command]")
        return
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=10
        )
        output = result.stdout or result.stderr or "Command complete!"
        await update.message.reply_text(f"💻 Output:\n{output[:1000]}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

live_screenshot_jobs = {}

async def livescreenshot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in live_screenshot_jobs:
        live_screenshot_jobs[chat_id] = False
        await update.message.reply_text("🛑 Live screenshot band kar diya!")
        return

    await update.message.reply_text("📸 Live screenshot shuru! Har 30 sec mein screenshot aayega. /livescreenshot dobara bolo band karne ke liye!")
    live_screenshot_jobs[chat_id] = True

    async def send_screenshots():
        from modules.agent import take_screenshot
        import glob

        while live_screenshot_jobs.get(chat_id, False):
            take_screenshot()
            screenshots_dir = os.path.expanduser("~") + r"\Pictures\Cyra Screenshots"
            files = glob.glob(os.path.join(screenshots_dir, "*.png"))
            if files:
                latest = max(files, key=os.path.getctime)
                try:
                    with open(latest, "rb") as f:
                        await context.bot.send_photo(chat_id=chat_id, photo=f)
                except:
                    pass
            await asyncio.sleep(30)

    asyncio.create_task(send_screenshots())

async def remotemsg_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = " ".join(context.args)
    if "|" not in args:
        await update.message.reply_text("Format: /remotemsg [name]|[message]\nExample: /remotemsg rahul saini|Hello yaar!")
        return

    from modules.agent import handle_action
    result = handle_action("whatsapp", args)
    await update.message.reply_text(f"📱 {result}")

async def setbg_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from modules.agent import handle_action
    result = handle_action("set_background", "background.png")
    await update.message.reply_text(f"🖼 {result}")

def run_bot():
    import nest_asyncio
    nest_asyncio.apply()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def main():
        application = Application.builder().token(TOKEN).build()

        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("play", play_command))
        application.add_handler(CommandHandler("pause", playpause_command))
        application.add_handler(CommandHandler("playpause", playpause_command))
        application.add_handler(CommandHandler("weather", weather_command))
        application.add_handler(CommandHandler("note", note_command))
        application.add_handler(CommandHandler("notes", notes_command))
        application.add_handler(CommandHandler("timer", timer_command))
        application.add_handler(CommandHandler("screenshot", screenshot_command))
        application.add_handler(CommandHandler("volume", volume_command))
        application.add_handler(CommandHandler("briefing", briefing_command))
        application.add_handler(CommandHandler("sendfile", sendfile_command))
        application.add_handler(CommandHandler("lockpc", lockpc_command))
        application.add_handler(CommandHandler("shutdown", shutdown_command))
        application.add_handler(CommandHandler("restart", restart_command))
        application.add_handler(CommandHandler("sendfolder", sendfolder_command))
        application.add_handler(CommandHandler("livescreenshot", livescreenshot_command))
        application.add_handler(CommandHandler("remotemsg", remotemsg_command))
        application.add_handler(CommandHandler("alarm", alarm_command))
        application.add_handler(CommandHandler("mouse", mouse_command))
        application.add_handler(CommandHandler("type", type_command))
        application.add_handler(CommandHandler("myip", myip_command))
        application.add_handler(CommandHandler("processes", processes_command))
        application.add_handler(CommandHandler("clipboard", clipboard_command))
        application.add_handler(CommandHandler("run", run_command_handler))
        application.add_handler(CommandHandler("email", email_command))
        application.add_handler(CommandHandler("bulb", bulb_command))
        application.add_handler(CommandHandler("setbg", setbg_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        

        print("[Telegram] Cyra bot is online!")
        await application.run_polling(drop_pending_updates=True)

    loop.run_until_complete(main())

def start_telegram_bot():
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    print("[Telegram] Bot thread started!")
