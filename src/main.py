import asyncio
import logging
from src.core.generator import Generation
from src.integrations.telegram_bot import dp, bot

logger = logging.getLogger(__name__)

async def auto_reply_task(interval_seconds: int = 60):
    """Tác vụ chạy ngầm định kỳ quét và trả lời email."""
    gen = Generation()
    logger.info("Bắt đầu tác vụ chạy ngầm: Auto Reply Mail.")
    
    while True:
        try:
            logger.info("Đang kiểm tra và xử lý email mới...")
            # Nếu hàm của Generation là hàm đồng bộ (blocking), dùng asyncio.to_thread
            await asyncio.to_thread(gen.get_deccision)
            
            # Nếu bản thân gen.autorepmail đã là async def:
            # await gen.autorepmail()
            
        except Exception as e:
            logger.error(f"Lỗi trong vòng lặp auto reply: {e}", exc_info=True)
            
        await asyncio.sleep(interval_seconds)

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
    )
    
    # 1. Tạo task chạy ngầm cho tác vụ email
    email_task = asyncio.create_task(auto_reply_task(interval_seconds=60))
    
    try:
        # 2. Chạy Telegram Bot ở luồng chính
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Telegram Bot đang lắng nghe...")
        await dp.start_polling(bot)
    finally:
        # Hủy background task và đóng kết nối an toàn khi tắt bot
        email_task.cancel()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Đã dừng toàn bộ dịch vụ.")