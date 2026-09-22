from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root=Path(__file__).resolve().parents[1]
image=Image.new('RGBA',(256,256),(16,35,63,255));d=ImageDraw.Draw(image)
d.rounded_rectangle((25,25,231,231),radius=46,fill='#087f78')
d.ellipse((55,60,180,191),outline='white',width=24)
d.rounded_rectangle((152,135,175,202),radius=4,fill='#6ee7d8')
d.rounded_rectangle((130,157,198,180),radius=4,fill='#6ee7d8')
(root/'assets').mkdir(exist_ok=True)
image.save(root/'assets'/'orcaprime.ico',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
image.save(root/'assets'/'orcaprime.png')
