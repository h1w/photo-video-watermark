from aiogram import Bot, Dispatcher, executor, types
import logging
import settings

logging.basicConfig(level=logging.INFO)

bot = Bot(token=settings.bot['token'])
dp = Dispatcher(bot)

@dp.message_handler(commands=['watermark'])
async def command_watermark(message: types.Message):
    await message.answer('Watermark command')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)