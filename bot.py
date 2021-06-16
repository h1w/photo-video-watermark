#from aiogram import Bot, Dispatcher, executor, types
import aiogram
import logging

from aiogram.types import message_entity
import settings
import datetime
import os
import pyffmpeg
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import re

work_directory = os.path.dirname(os.path.abspath(__file__))
downloads_directory = work_directory+'/downloads'

logging.basicConfig(level=logging.INFO)
#ff = pyffmpeg.FFmpeg()

bot = aiogram.Bot(token=settings.bot['token'])
dp = aiogram.Dispatcher(bot)

async def PhotoWatermark(photo_abspath, user_text_fill):
    photo = Image.open(photo_abspath) # .convert("RGBA")
    with BytesIO() as f:
        photo.save(f, format='PNG')
        photo = Image.open(f).convert("RGBA")
        f.close()
        text = settings.watermark['watermark_default_text']

        photo_width, photo_height = photo.size
        txt = Image.new("RGBA", photo.size, (255,255,255,0))
        
        font_size = photo_width//14
        font = ImageFont.truetype("{}/fonts/{}".format(work_directory, "Hack-Bold.ttf"), font_size)
        draw = ImageDraw.Draw(txt)
        
        text_width, text_height = draw.textsize(text, font)
        margin_x = photo_width//55
        margin_y = photo_height//55
        x = photo_width - text_width - margin_x
        y = photo_height - text_height - margin_y
        pos = (x, y)

        text_fill = user_text_fill
        text_stroke_fill = text_fill
        draw.text(pos, text, fill=text_fill, font=font, stroke_fill=text_stroke_fill)
        photo_outpath = str(*photo_abspath.split('.')[:-1]) +'.png' # Creat same photo in .png format
        
        combined = Image.alpha_composite(photo, txt)
        combined.save(photo_outpath)
        return photo_outpath
        

@dp.message_handler(content_types=aiogram.types.ContentType.PHOTO)
async def PhotoProcess(message: aiogram.types.Message):
    photo_abspath = '{}/photos/{}.jpg'.format(downloads_directory, datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")) # Save photo to downloads/photos
    
    # Download photo
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    await bot.download_file(file_path, photo_abspath)

    # Work with a photo
    user_text_fill = settings.watermark['watermark_default_rgba']
    warning_answer = ""
    user_text=""
    try:
        user_text = message.md_text.replace(' ', '', -1).strip('\()')
        user_text_fill = tuple(map(lambda x: x if x >= 0 and x <= 255 else None, map(int, user_text.split(','))))
    except Exception:
        user_text_fill = settings.watermark['watermark_default_rgba']
        if user_text != "":
            warning_answer = settings.help['photo_help_answer']
    photo_outpath = await PhotoWatermark(photo_abspath, user_text_fill)

    # Send photo
    await message.answer_photo(aiogram.types.InputFile(photo_outpath), caption=warning_answer)
    os.remove(photo_abspath) # Delete .jpg
    os.remove(photo_outpath) # Delete .png

@dp.message_handler(commands=['start'])
async def start(message: aiogram.types.Message):
    await message.answer("Hi. It's watermark bot.\nType /help for details.")

@dp.message_handler(commands=['help'])
async def help(message: aiogram.types.Message):
    if len(message.text.split(' ')) == 1:
        await message.answer(settings.help['help_info'])
    else:
        params = message.text.split(' ')
        if params[1] == 'photo':
            await message.answer(settings.help['photo_help_answer'])
        elif params[1] == 'video':
            await message.answer('video help')
        elif params[1] == 'link':
            await message.answer('link help')
if __name__ == '__main__':
    aiogram.executor.start_polling(dp, skip_updates=False)