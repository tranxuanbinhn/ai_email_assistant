import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery
)
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv
load_dotenv()
import os
from src.core.generator import Generation
from src.core.logging.logger_config import setup_logger
TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
bot = Bot(token=TOKEN_TELEGRAM)
dp = Dispatcher()
gen = Generation()
# ==========================================
# CÁC HÀM BACKEND CỦA BẠN (Mô phỏng tích hợp)
# ==========================================
logger = setup_logger(__name__)
async def get_pending_review_emails():
    """Lấy danh sách email AI đã soạn cần người dùng duyệt"""
    return [
        {
            "id": "p101",
            "to": "partner@techcorp.io",
            "subject": "Đề xuất hợp tác Q3/2026",
            "body": "Chào anh/chị,\nAI đề xuất nội dung kết nối dịch vụ tự động hóa quy trình..."
        },
        {
            "id": "p102",
            "to": "support@saas.com",
            "subject": "Yêu cầu gia hạn license",
            "body": "Xin chào,\nChúng tôi muốn gia hạn gói Pro thêm 1 năm..."
        }
    ]

async def send_email_by_id(email_id: str) -> bool:
    """Thực thi gửi email cụ thể"""
    # Gọi hàm gửi mail thực tế của bạn ở đây
    return True

# ==========================================
# KEYBOARD BUILDERS
# ==========================================
def main_menu_kb(pending_count: int, sent_count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"📥 Cần duyệt ({pending_count})",
                    callback_data="view_pending:0"
                ),
                InlineKeyboardButton(
                    text=f"📤 Đã gửi hôm nay ({sent_count})",
                    callback_data="view_sent"
                )
            ],
            [
                InlineKeyboardButton(text="🔄 Làm mới Dashboard", callback_data="refresh_dashboard")
            ]
        ]
    )

def email_review_kb(email_id: str, current_index: int, total: int) -> InlineKeyboardMarkup:
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Trước", callback_data=f"view_pending:{current_index - 1}"))
    if current_index < total - 1:
        nav_buttons.append(InlineKeyboardButton(text="Sau ➡️", callback_data=f"view_pending:{current_index + 1}"))

    buttons = [
        [
            
            InlineKeyboardButton(text="❌ Bỏ qua", callback_data=f"discard:{email_id}:{current_index}")
        ]
    ]
    if nav_buttons:
        buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton(text="🔙 Quay lại Menu", callback_data="refresh_dashboard")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ==========================================
# HANDLERS
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: Message):
    pending = await gen.get_email_not_process_and_return_data()
    sent = await gen.get_sent_mail_one_day()
    
    text = (
        "🤖 **AI EMAIL DISPATCHER DASHBOARD**\n\n"
        f"• Email đã gửi hôm nay: `{len(sent)}`\n"
        f"• Email đang chờ duyệt: `{len(pending)}`\n\n"
        "Chọn tác vụ bên dưới để kiểm tra hoặc gửi email:"
    )
    await message.answer(text, reply_markup=main_menu_kb(len(pending), len(sent)), parse_mode="Markdown")

@dp.callback_query(F.data == "refresh_dashboard")
async def cb_refresh_dashboard(query: CallbackQuery):
    pending = await gen.get_email_not_process_and_return_data()
    sent = await gen.get_sent_mail_one_day()
    
    text = (
        "🤖 **AI EMAIL DISPATCHER DASHBOARD**\n\n"
        f"• Email đã gửi hôm nay: `{len(sent)}`\n"
        f"• Email đang chờ duyệt: `{len(pending)}`\n\n"
        "Chọn tác vụ bên dưới để kiểm tra hoặc gửi email:"
    )
    await query.message.edit_text(text, reply_markup=main_menu_kb(len(pending), len(sent)), parse_mode="Markdown")
    await query.answer("Đã cập nhật dữ liệu mới nhất")

@dp.callback_query(F.data == "view_sent")
async def cb_view_sent(query: CallbackQuery):
    sent_list = await gen.get_sent_mail_one_day()
    
    if not sent_list:
        text = "📤 **Hôm nay chưa có email nào được gửi.**"
    else:
        text = f"📤 **DANH SÁCH EMAIL ĐÃ GỬI HÔM NAY ({len(sent_list)})**\n\n"
        for idx, item in enumerate(sent_list, 1):
            text += f"`{idx}.` **Đến:** `{item.to}`\n"
            text += f"   **Tiêu đề:** {item.subject}\n"
            text += f"   **Thời gian:** `{item.time}`\n\n"

    back_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Quay lại Menu", callback_data="refresh_dashboard")]]
    )
    await query.message.edit_text(text, reply_markup=back_kb, parse_mode="Markdown")
    try:
        await query.answer()
    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            logger.warning("Bỏ qua lỗi timeout của callback query cũ.")
        else:
            raise e 

@dp.callback_query(F.data.startswith("view_pending:"))
async def cb_view_pending(query: CallbackQuery):
    index = int(query.data.split(":")[1])
    pending = await gen.get_email_not_process_and_return_data()

    if not pending:
        text = "🎉 **Tuyệt vời! Không còn email nào cần duyệt.**"
        back_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 Quay lại Menu", callback_data="refresh_dashboard")]]
        )
        try:
            await query.message.edit_text(text, reply_markup=back_kb, parse_mode="None")
            await query.answer()
            return
        except TelegramBadRequest as e:
            if "query is too old" in str(e):
                logger.warning("Bỏ qua lỗi timeout của callback query cũ.")
            else:
                raise e

    # Giới hạn index nếu mảng bị thay đổi
    index = min(index, len(pending) - 1)
    mail = pending[index]

    text = (
        f"📋 **DUYỆT MAIL TỰ ĐỘNG ({index + 1}/{len(pending)})**\n"
        "────────────────────\n"
        f"**Gửi tới:** `{mail.to}`\n"
        f"**Tiêu đề:** `{mail.subject}`\n"
        "────────────────────\n"
        f"**Nội dung AI đề xuất:**\n\n"
        f"{mail.body}\n"
    )
    await query.message.edit_text(
        text,
        reply_markup=email_review_kb(mail.id, index, len(pending)),
        parse_mode=None
    )
    try:
        await query.answer()
    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            logger.warning("Bỏ qua lỗi timeout của callback query cũ.")
        else:
            raise e

@dp.callback_query(F.data.startswith("approve_send:"))
async def cb_approve_send(query: CallbackQuery):
    _, email_id, current_index = query.data.split(":")
    current_index = int(current_index)

    await query.answer("Đang gửi mail...", show_alert=False)
    
    # Thực thi hàm gửi
    success = await send_email_by_id(email_id)
    
    if success:
        await query.answer("✅ Đã gửi mail thành công!", show_alert=True)
        # Chuyển tiếp sang item tiếp theo hoặc refresh
        pending = await gen.get_email_not_process_and_return_data()
        next_index = max(0, min(current_index, len(pending) - 1))
        
        # Gọi lại handler xem pending để cập nhật màn hình
        query.data = f"view_pending:{next_index}"
        await cb_view_pending(query)
    else:
        await query.answer("❌ Lỗi khi gửi mail. Vui lòng thử lại!", show_alert=True)

@dp.callback_query(F.data.startswith("discard:"))
async def cb_discard(query: CallbackQuery):
    _, email_id, current_index = query.data.split(":")
    current_index = int(current_index)
    
    # TODO: Gọi hàm đánh dấu bỏ qua/xóa mail nháp trong DB của bạn ở đây
    
    await query.answer("🗑️ Đã bỏ qua email này.")
    next_index = max(0, current_index)
    query.data = f"view_pending:{next_index}"
    await cb_view_pending(query)

# ==========================================
# MAIN RUNNER
# ==========================================
#async def main():
#    logging.basicConfig(level=logging.INFO)
#    await dp.start_polling(bot)

#if __name__ == "__main__":
#    asyncio.run(main())
async def main():
    logger.info("Bot đang khởi động...")
    try:
        # Bỏ qua các update cũ khi bot offline
        await bot.delete_webhook(drop_pending_updates=True)
        # Bắt đầu lắng nghe tin nhắn
        await dp.start_polling(bot)
    finally:
        # Đảm bảo đóng kết nối HTTP an toàn khi tắt bot
        await bot.session.close()
        logger.info("Bot đã tắt kết nối an toàn.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Dừng bot bởi người dùng (Ctrl+C).")