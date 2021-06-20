import settings
import aiogram
import logging
import datetime
import os
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from colorthief import ColorThief
import asyncio
import aiohttp

work_directory = os.path.dirname(os.path.abspath(__file__))
downloads_directory = '/tmp/photo-video-watermark/downloads'
# Create directories if not exists
if not os.path.exists(downloads_directory):
    os.makedirs(downloads_directory)
if not os.path.exists(downloads_directory+'/videos'):
    os.makedirs(downloads_directory+'/videos')
if not os.path.exists(downloads_directory+'/photos'):
    os.makedirs(downloads_directory+'/photos')

logging.basicConfig(level=logging.INFO)

bot = aiogram.Bot(token=settings.bot['token'])
dp = aiogram.Dispatcher(bot)

class IsAllowedUser(aiogram.dispatcher.filters.BoundFilter):
    key = 'is_allowed_user' # Use is_allowed_user=True in aiogram Dispather for check user permission to use this function via bot implementations
    def __init__(self, is_allowed_user):
        self.is_allowed_user = is_allowed_user
    async def check(self, message: aiogram.types.Message):
        user = message.from_user.id
        if user in settings.bot['allowed_users']:
            return True
        else:
            return False

dp.filters_factory.bind(IsAllowedUser) # Register custom filter

@dp.message_handler(commands=['start'], is_allowed_user=True)
async def start(message: aiogram.types.Message):
    await message.answer("Hi. It's watermark bot.\nType /help for details.")

@dp.message_handler(commands=['help'], is_allowed_user=True)
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

async def AnalyzeWatermarkColor(photo_abspath, pos, size):
    photo = Image.open(photo_abspath).copy().convert("RGB").crop((pos[0], pos[1], pos[0]+size[0], pos[1]+size[1]))
    photo.save(photo_abspath)
    img = ColorThief(photo_abspath)
    dominant_color = img.get_color()
    d = 0
    luminance = (0.299 * dominant_color[0] + 0.587 * dominant_color[1] + 0.114 * dominant_color[2])/255
    il = float(str(luminance)[0:3])
    if il == 0.1:
        d = 230
    elif il == 0.2:
        d = 210
    elif il == 0.3:
        d = 190
    elif il == 0.4:
        d = 170
    elif il == 0.5:
        d = 150
    elif il == 0.6:
        d = 130
    elif il == 0.7:
        d = 110
    elif il == 0.8:
        d = 90
    elif il == 0.9:
        d = 70
    user_text_fill = (d, d, d, 220)
    return user_text_fill

async def PhotoWatermark(photo_abspath, user_text_fill, user_input):
    photo = Image.open(photo_abspath)
    with BytesIO() as f:
        photo.save(f, format='PNG')
        photo = Image.open(f).convert("RGBA")
        f.close()
        text = settings.watermark['watermark_default_text']

        photo_width, photo_height = photo.size
        txt = Image.new("RGBA", photo.size, (255,255,255,0))
        
        photo_min_side=photo_width if photo_width < photo_height else photo_height
        font_size = photo_min_side//14
        font = ImageFont.truetype("{}/fonts/{}".format(work_directory, "Hack-Bold.ttf"), font_size)
        draw = ImageDraw.Draw(txt)
        
        text_width, text_height = draw.textsize(text, font)
        margin_x = photo_width//55
        margin_y = photo_height//60
        x = photo_width - text_width - margin_x
        y = photo_height - text_height - margin_y
        pos = (x, y)

        text_fill = user_text_fill
        if user_input == False:
            text_fill = await AnalyzeWatermarkColor(photo_abspath, pos, (text_width, text_height))
        text_stroke_fill = text_fill
        draw.text(pos, text, fill=text_fill, font=font, stroke_fill=text_stroke_fill)
        photo_outpath = str(*photo_abspath.split('.')[:-1]) +'_edited.png' # Creat same photo in .png format
        
        combined = Image.alpha_composite(photo, txt)
        combined.save(photo_outpath)
        return photo_outpath
        

@dp.message_handler(content_types=aiogram.types.ContentType.PHOTO, is_allowed_user=True)
async def PhotoProcess(message: aiogram.types.Message):
    photo_abspath = '{}/photos/{}.jpg'.format(downloads_directory, datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")) # Downloaded photo path to downloads/photos
    
    # Download photo
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    await bot.download_file(file_path, photo_abspath)

    # Work with photo
    user_text_fill = settings.watermark['watermark_default_rgba']
    warning_answer = ""
    user_text=""
    user_input = False
    try:
        user_text = message.md_text.replace(' ', '', -1).strip('\()')
        user_text_fill = tuple(map(lambda x: x if x >= 0 and x <= 255 else None, map(int, user_text.split(','))))
        user_input = True
    except Exception:
        user_text_fill = settings.watermark['watermark_default_rgba']
        if user_text != "":
            warning_answer = settings.help['photo_help_answer']
            user_input = False
    photo_outpath = await PhotoWatermark(photo_abspath, user_text_fill, user_input)

    # Send photo
    await message.answer_photo(aiogram.types.InputFile(photo_outpath), caption=warning_answer)
    logging.info('[PHOTO] - [{}] - Watermark has been successfully inserted to photo {} owned user {}.'.format(datetime.datetime.now().strftime("%H:%M:%S-%d.%m.%Y"), file_id, message.from_user.id))
    os.remove(photo_abspath) # Delete .jpg
    os.remove(photo_outpath) # Delete .png

@dp.message_handler(content_types=aiogram.types.ContentType.VIDEO, is_allowed_user=True)
async def VideoProcess(message: aiogram.types.Message):
    video_abspath = '{}/videos/{}.mp4'.format(downloads_directory, datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")) # Downloaded video path to downloads/video
    watermark_abspath = '{}/watermarks/{}'.format(work_directory, settings.watermark['watermark'])

    # Download video
    file_id = message.video.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    await bot.download_file(file_path, video_abspath)

    # Work with video
    video_edited_abspath = str(*video_abspath.split('.')[:-1])+'_edited.mp4'
    ffmpeg_cmd = """ffmpeg -i {} -i {} -filter_complex "[1]format=rgba,colorchannelmixer=aa=0.6,scale=iw*0.6:-1[logo];[0][logo]overlay=W-w-W/55:H-h-H/70:format=auto,format=yuv420p" -c:a copy -c:v libx264 -crf 25 -profile:v high -level 4.2 -max_muxing_queue_size 4096 -pix_fmt yuv420p -preset medium -map V:0? -map 0:a? -movflags +faststart -strict -2 {}""".format(
        video_abspath,
        watermark_abspath,
        video_edited_abspath
    )
    proc = await asyncio.create_subprocess_shell(
        ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    
    # Send video
    await message.answer_video(aiogram.types.InputFile(video_edited_abspath), caption="")
    logging.info('[VIDEO] - [{}] - Video {} has been converted from user {}. And watermark has been successfully inserted into the video.'.format(datetime.datetime.now().strftime("%H:%M:%S-%d.%m.%Y"), file_id, message.from_user.id))

    os.remove(video_abspath)
    os.remove(video_edited_abspath)

async def LinkPhotoProcess(message, link):
    photo_abspath = '{}/photos/{}.png'.format(downloads_directory, datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")) # Downloaded photo path to downloads/photos
    # Download photo in jpg or png format
    async with aiohttp.ClientSession() as session:
        async with session.get(link, allow_redirects=True) as response:
            # Download photo
            assert response.status == 200
            photo_bytes = await response.read()
            photo = Image.open(BytesIO(photo_bytes))
            photo.save(photo_abspath)

            # Work with photo
            photo_outpath = await PhotoWatermark(photo_abspath, user_text_fill="", user_input=False)

            # Send photo
            await message.answer_photo(aiogram.types.InputFile(photo_outpath), caption="")
            logging.info('[PHOTO] - [{}] - Watermark has been successfully inserted to photo by link {} owned user {}.'.format(datetime.datetime.now().strftime("%H:%M:%S-%d.%m.%Y"), link, message.from_user.id))
            os.remove(photo_abspath) # Delete downloaded photo
            os.remove(photo_outpath) # Delete edited photo

async def LinkVideoProcess(file_extension, message):
    if file_extension == 'mp4':
        print('mp4')
    elif file_extension == 'webm':
        print('webm')

@dp.message_handler(content_types=aiogram.types.ContentType.TEXT, is_allowed_user=True)
async def LinkProcess(message: aiogram.types.Message):
    try:
        user_input = message.text
        file_extension = user_input.split('.')[-1]
        if file_extension == 'mp4':
            print('mp4')
        elif file_extension == 'webm':
            print('wemb')
        elif file_extension == 'png' or file_extension == 'jpg':
            await LinkPhotoProcess(message, user_input)
        else:
            await message.answer("Try another link please.")
    except Exception:
        print(Exception)
        await message.answer('Link: {} - is invalid.'.format(user_input))

if __name__ == '__main__':
    aiogram.executor.start_polling(dp, skip_updates=False)
