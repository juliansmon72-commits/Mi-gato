# Se ejecuta en la nube después de "npx cap add android": agrega permisos e íconos.
import os
from PIL import Image, ImageDraw

man = 'android/app/src/main/AndroidManifest.xml'
s = open(man, encoding='utf-8').read()
perms = ['ACCESS_COARSE_LOCATION', 'ACCESS_FINE_LOCATION', 'FOREGROUND_SERVICE',
         'FOREGROUND_SERVICE_LOCATION', 'POST_NOTIFICATIONS', 'WAKE_LOCK']
add = ''.join('    <uses-permission android:name="android.permission.%s" />\n' % p
              for p in perms if p not in s)
s = s.replace('<application', add + '    <application', 1)
open(man, 'w', encoding='utf-8').write(s)

icon = Image.open('icon-512.png').convert('RGBA')
fg = Image.open('icon-maskable-512.png').convert('RGBA')
for d, (l, f) in {'mdpi': (48, 108), 'hdpi': (72, 162), 'xhdpi': (96, 216),
                  'xxhdpi': (144, 324), 'xxxhdpi': (192, 432)}.items():
    r = 'android/app/src/main/res/mipmap-' + d
    if not os.path.isdir(r):
        continue
    sq = icon.resize((l, l), Image.LANCZOS)
    sq.save(r + '/ic_launcher.png')
    mask = Image.new('L', (l, l), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, l - 1, l - 1], fill=255)
    rd = sq.copy(); rd.putalpha(mask); rd.save(r + '/ic_launcher_round.png')
    fg.resize((f, f), Image.LANCZOS).save(r + '/ic_launcher_foreground.png')

bg = 'android/app/src/main/res/values/ic_launcher_background.xml'
open(bg, 'w', encoding='utf-8').write(
    '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">#F27D84</color>\n</resources>\n')
print('listo')
