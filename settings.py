bot = {
    'token': open('BOT_SETTINGS/TOKEN', 'r').readline(), # Bot token
    'admin': int(open('BOT_SETTINGS/ADMIN_ID', 'r').readline()), # Admin id
    'allowed_users': list(map(lambda x: int(x.strip('\n')), open('BOT_SETTINGS/USERS_ID', 'r').readlines())) # List ids of allowed users
}

watermark = {
    'watermark': 'watermark4.png',
    'watermark_default_text': "@boxthread",
    'watermark_default_rgba': (150, 150, 150, 220),
    'watermark_default_rgba_presets': """(150, 150, 150, 220)
(0, 0, 0, 255)
(30, 250, 90, 220)
"""
}

help = {
    'help_info': """photo
video
link photo{jpeg,png},video{mp4,webm}.
""",
    'photo_help_answer': """
RGBA input format:
R, G, B, A - Example: 24, 210, 8, 217
(You can send rgba with () and without spaces.)
Presets:
{}
""".format(watermark['watermark_default_rgba_presets'])
}