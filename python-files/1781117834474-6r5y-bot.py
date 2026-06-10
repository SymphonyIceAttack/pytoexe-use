import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен вашего основного бота (получите у @BotFather)
MAIN_BOT_TOKEN = "7989535324:AAHEF8yj_X4viSzaNChxLWYX-nxRS0353d4"

# ID канала(ов), откуда будут пересылаться сообщения
ALLOWED_CHANNELS = [-1001685349748]  # замените на реальные ID

# Целевой бот для пересылки — @alice_speaker_bot
TARGET_BOT_USERNAME = "@alice_speaker_bot"

async def handle_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post and update.channel_post.chat.id in ALLOWED_CHANNELS:
        message_text = update.channel_post.text or update.channel_post.caption

        if message_text and message_text.startswith('/say '):
            # Извлекаем текст после команды /say
            text_to_send = message_text[5:].strip()

            try:
                # Отправляем сообщение целевому боту
                await context.bot.send_message(
                    chat_id=TARGET_BOT_USERNAME,
                    text=text_to_send
                )
                logger.info(f"Сообщение '{text_to_send}' успешно переслано в {TARGET_BOT_USERNAME}")

                # Подтверждение в канале (опционально)
                await update.channel_post.reply_text(
                    f"✅ Сообщение переслано на Яндекс Станцию: {text_to_send}"
                )

            except Exception as e:
                logger.error(f"Ошибка при пересылке в {TARGET_BOT_USERNAME}: {e}")
                await update.channel_post.reply_text("❌ Ошибка при пересылке сообщения.")

def main():
    # Создаём приложение
    application = Application.builder().token(MAIN_BOT_TOKEN).build()

    # Добавляем обработчик сообщений из каналов
    application.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_channel_message))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
