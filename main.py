from bs4 import BeautifulSoup
import sys
import os
import argparse
from tqdm import tqdm


#     ┓         
# ┏┏┓╋┣┓┓┏┏┓┏┓┏┏
# ┗┗┻┗┛┗┛┗┛ ┛┗┫┛
#             ┛ 

# https://github.com/cathxrsys
# https://t.me/cathxrsys


parser = argparse.ArgumentParser(description="Convert Telegram HTML export with voice messages to playable audio tags.")
parser.add_argument("export_path", nargs="?", help="Path to the exported Telegram HTML file")
args = parser.parse_args()

if not args.export_path:
    print("Please specify the path to the exported Telegram HTML file as an argument.")
    sys.exit(1)

export_path = args.export_path

if not os.path.isdir(export_path):
    print(f"Path not found: {export_path}")
    sys.exit(1)


def convert(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # Change voices

    for a in soup.find_all('a', class_='media_voice_message'):
        ogg_href = a['href']

        audio_tag = soup.new_tag('audio', controls=True)
        audio_tag['src'] = ogg_href
        audio_tag.string = 'Ваш браузер не поддерживает аудио'

        a.replace_with(audio_tag)

    # Add round message

    for a in soup.find_all('a', class_='media_video'):
        mp4_href = a.get('href')
        if 'round' in mp4_href:
            thumb_img = a.find('img', class_='thumb pull_left')
            poster = thumb_img['src'] if thumb_img and thumb_img.has_attr('src') else ""
            video_tag = soup.new_tag('video', controls=True)
            video_tag['src'] = mp4_href
            video_tag['width'] = "300"
            video_tag['height'] = "300"
            if poster:
                video_tag['poster'] = poster
            video_tag['style'] = "border-radius:50%; background:#000;"  # Круглый стиль как у Telegram
            video_tag.string = 'Ваш браузер не поддерживает видео'
            a.replace_with(video_tag)

    # Change GIFS

    for a in soup.find_all('a', class_='animated_wrap') + soup.find_all('a', class_='media_video'):
        mp4_href = a['href']
        if 'video' in mp4_href and 'round' not in mp4_href:
            video_tag = soup.new_tag('video', controls=True, loop=True, autoplay=False)
            video_tag['src'] = mp4_href
            video_tag['width'] = "260"  # Можно взять из style, если нужно
            video_tag['height'] = "260"
            video_tag.string = 'Ваш браузер не поддерживает видео'
            # Можно добавить постер (обложку), если есть <img ... src="..._thumb.jpg">
            thumb_img = a.find('img', class_='animated')
            if thumb_img and thumb_img.has_attr('src'):
                video_tag['poster'] = thumb_img['src']
            a.replace_with(video_tag)

    # Change videos

    for a in soup.find_all('a', class_='video_file_wrap'):
        mp4_href = a['href']
        thumb_img = a.find('img', class_='video_file')
        width = thumb_img['width'] if thumb_img and thumb_img.has_attr('width') else "320"
        height = thumb_img['height'] if thumb_img and thumb_img.has_attr('height') else "240"
        poster = thumb_img['src'] if thumb_img and thumb_img.has_attr('src') else ""
        duration = a.find('div', class_='video_duration')
        video_tag = soup.new_tag('video', controls=True)
        video_tag['src'] = mp4_href
        video_tag['width'] = width
        video_tag['height'] = height
        if poster:
            video_tag['poster'] = poster
        video_tag.string = 'Ваш браузер не поддерживает видео'
        a.replace_with(video_tag)
        if duration:
            video_tag.insert_after(duration)

    # Add JS for scaling images

    lightbox_html = '''
<style>
.lightbox-bg {
  position: fixed; left:0; top:0; width:100vw; height:100vh; background:rgba(0,0,0,0.8);
  display:none; justify-content:center; align-items:center; z-index:1000;
}
.lightbox-bg.active { display:flex; }
.lightbox-img {
  max-width:90vw; max-height:90vh; border-radius:10px; box-shadow:0 0 24px #000;
  cursor: grab;
  transition: box-shadow 0.2s;
  user-select: none;
}
.lightbox-close {
  position: absolute; top: 30px; right: 40px; font-size: 3em; color: #fff; cursor: pointer; z-index:1001;
}
.lightbox-save {
  position: absolute; bottom: 30px; right: 40px; font-size: 2em; color: #fff; cursor: pointer; z-index:1001;
}
</style>
<div class="lightbox-bg" id="lightbox">
  <span class="lightbox-close" onclick="closeLightbox()">✖</span>
  <img id="lightbox-img" class="lightbox-img" src="" alt="photo" />
  <a id="lightbox-save" class="lightbox-save" href="#" download>💾</a>
</div>
<script>
let scale = 1, originX = 0, originY = 0, lastX = 0, lastY = 0;
const img = document.getElementById('lightbox-img');
const lightbox = document.getElementById('lightbox');
function showLightbox(src) {
  scale = 1; originX = 0; originY = 0; lastX = 0; lastY = 0;
  updateTransform();
  img.src = src;
  document.getElementById('lightbox-save').href = src;
  lightbox.classList.add('active');
}
function closeLightbox() {
  lightbox.classList.remove('active');
}
img.addEventListener('wheel', function(e) {
  e.preventDefault();
  const rect = img.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  const offsetX = mx - rect.width/2;
  const offsetY = my - rect.height/2;
  const oldScale = scale;
  if (e.deltaY < 0) scale = Math.min(scale + 0.1, 5);
  else scale = Math.max(scale - 0.1, 0.2);
  originX += offsetX * (1 - scale/oldScale);
  originY += offsetY * (1 - scale/oldScale);
  updateTransform();
});
let dragging = false, dragStartX, dragStartY;
img.addEventListener('mousedown', function(e) {
  if (scale > 1) {
    dragging = true;
    dragStartX = e.clientX - originX;
    dragStartY = e.clientY - originY;
    img.style.cursor = 'grabbing';
  }
});
window.addEventListener('mousemove', function(e) {
  if (dragging) {
    originX = e.clientX - dragStartX;
    originY = e.clientY - dragStartY;
    updateTransform();
  }
});
window.addEventListener('mouseup', function() {
  dragging = false;
  img.style.cursor = 'grab';
});
img.addEventListener('dblclick', function() {
  scale = 1; originX = 0; originY = 0;
  updateTransform();
});
function updateTransform() {
  img.style.transform = `scale(${scale}) translate(${originX/scale}px, ${originY/scale}px)`;
}
document.querySelectorAll('.photo_wrap').forEach(function(photo) {
  photo.addEventListener('click', function(e) {
    e.preventDefault();
    var src = photo.getAttribute('href');
    showLightbox(src);
  });
});
</script>
    '''

    # Add a CSS

    lightbox_css = '''
<style>
.lightbox-bg {
  position: fixed; left:0; top:0; width:100vw; height:100vh; background:rgba(0,0,0,0.8);
  display:none; justify-content:center; align-items:center; z-index:1000;
}
.lightbox-bg.active { display:flex; }
.lightbox-img { max-width:90vw; max-height:90vh; border-radius:10px; box-shadow:0 0 24px #000; }
.lightbox-close {
  position: absolute; top: 30px; right: 40px; font-size: 3em; color: #fff; cursor: pointer; z-index:1001;
}
.lightbox-save {
  position: absolute; bottom: 30px; right: 40px; font-size: 2em; color: #fff; cursor: pointer; z-index:1001;
}
</style>
'''

    head = soup.head
    if head:
        head.append(BeautifulSoup(lightbox_css, 'html.parser'))

    # BeautifulSoup insert не всегда корректно работает с <body>, поэтому делаем вручную
    body = soup.body
    if body:
        body.append(BeautifulSoup(lightbox_html, 'html.parser'))

    # Save the modified HTML

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))


for p in tqdm(os.listdir(export_path)):
    if p.endswith('.html') and 'converted' not in p:
        convert(os.path.join(export_path, p))


print('Done!')