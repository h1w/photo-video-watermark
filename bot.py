#from aiogram import Bot, Dispatcher, executor, types
import aiogram
import logging
import settings
import datetime
import os
import pyffmpeg

work_directory = os.path.dirname(os.path.abspath(__file__))
downloads_directory = work_directory+'/downloads'
logging.basicConfig(level=logging.INFO)
ff = pyffmpeg.FFmpeg()

bot = aiogram.Bot(token=settings.bot['token'])
dp = aiogram.Dispatcher(bot)

@dp.message_handler(content_types=aiogram.types.ContentType.PHOTO)
async def command_watermark(message: aiogram.types.Message):
    photo_path = '{}/{}.jpg'.format(downloads_directory, datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    # Download photo
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    await bot.download_file(file_path, photo_path)
    # Work with a photo
    #ff.options("-i {} -vf scale=250:150 {}".format(photo_path, photo_path))
    # Send photo
    await message.answer_photo(aiogram.types.InputFile(photo_path), caption="Result")
    os.remove(photo_path)

if __name__ == '__main__':
    aiogram.executor.start_polling(dp, skip_updates=False)