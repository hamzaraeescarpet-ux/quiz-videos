import os
import shutil
import random
import asyncio
import numpy as np
import edge_tts
from moviepy.editor import *
from moviepy.config import change_settings
from moviepy.video.fx.all import loop, fadein
from PIL import Image, ImageDraw

magick_path = shutil.which("magick")
if magick_path:
    os.environ["IMAGEMAGICK_BINARY"] = magick_path
    change_settings({"IMAGEMAGICK_BINARY": magick_path})

try:
    if not hasattr(Image, "ANTIALIAS"):
        Image.ANTIALIAS = Image.Resampling.LANCZOS
except Exception:
    pass

def create_rounded_text(text, fontsize, txt_color, bg_color, font_path, size, align='center', radius=40, padding=70, border_color=None, border_width=0):
    txt_clip = TextClip(
        text, fontsize=fontsize, color=txt_color, font=font_path,
        method='caption', align=align, size=size
    )
    w, h = txt_clip.size
    bg_w, bg_h = w + padding, h + padding
    
    # If radius is -1, make it a perfect pill capsule
    if radius == -1:
        radius = bg_h // 2
        
    img = Image.new('RGBA', (bg_w, bg_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, bg_w, bg_h), radius=radius, fill=bg_color, outline=border_color, width=border_width)
    
    img_array = np.array(img)
    rgb = img_array[:, :, :3]
    alpha = img_array[:, :, 3] / 255.0
    
    bg_clip = ImageClip(rgb).set_mask(ImageClip(alpha, ismask=True))
    composite = CompositeVideoClip([bg_clip, txt_clip.set_position('center')], size=(bg_w, bg_h))
    return composite

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_FOLDER = os.path.join(BASE_DIR, "temp")
ASSETS_FOLDER = os.path.join(BASE_DIR, "assets")
BG_VIDEO_FOLDER = os.path.join(BASE_DIR, "backgrounds")

os.makedirs(TEMP_FOLDER, exist_ok=True)

# Define font directly
FONT_PATH = os.path.join(ASSETS_FOLDER, "fonts", "Milker.ttf")

async def generate_voice(text, filename):
    voice = "en-US-ChristopherNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)

async def generate_both_audios(speech_1, audio_path_1, speech_2, audio_path_2):
    await asyncio.gather(
        generate_voice(speech_1, audio_path_1),
        generate_voice(speech_2, audio_path_2)
    )

def create_video_from_row(row, category, custom_logo_path, output_dir):
    vid_id = str(row.get('id', random.randint(1000, 9999)))
    q_text = str(row.get('question', ''))
    opt1_val = str(row.get('option1', '')).strip()
    opt2_val = str(row.get('option2', '')).strip()
    opt3_val = str(row.get('option3', '')).strip()
    opt4_val = str(row.get('option4', '')).strip()
    ans_val = str(row.get('answer', '')).strip()

    correct_idx = None
    correct_label = "A"
    if ans_val.lower() == opt1_val.lower():
        correct_idx = 1
        correct_label = "A"
    elif ans_val.lower() == opt2_val.lower():
        correct_idx = 2
        correct_label = "B"
    elif ans_val.lower() == opt3_val.lower():
        correct_idx = 3
        correct_label = "C"
    elif ans_val.lower() == opt4_val.lower():
        correct_idx = 4
        correct_label = "D"

    # 1) Background pick dynamically from category
    category_path = os.path.join(BG_VIDEO_FOLDER, category)
    try:
        if not os.path.exists(category_path):
            category_path = BG_VIDEO_FOLDER # fallback
        bg_files = [f for f in os.listdir(category_path) if f.lower().endswith((".mp4", ".mov", ".mkv", ".webm"))]
        if not bg_files:
            raise Exception(f"No background files found in {category_path}")
        bg_video_path = os.path.join(category_path, random.choice(bg_files))
    except Exception as e:
        raise Exception(f"Error finding background: {e}")

    # 2) Audio generation
    audio_path_1 = os.path.join(TEMP_FOLDER, f"temp_q_{vid_id}.mp3")
    speech_1 = f"Question... {q_text} ... Is it ... {opt1_val} ... {opt2_val} ... {opt3_val} ... or {opt4_val}"

    audio_path_2 = os.path.join(TEMP_FOLDER, f"temp_a_{vid_id}.mp3")
    speech_2 = f"The correct answer is ... {ans_val}"

    try:
        asyncio.run(generate_both_audios(speech_1, audio_path_1, speech_2, audio_path_2))
    except Exception as e:
        print(f"edge-tts failed: {e}. Falling back to gTTS...", flush=True)
        try:
            from gtts import gTTS
            gTTS(text=speech_1, lang='en', tld='us').save(audio_path_1)
            gTTS(text=speech_2, lang='en', tld='us').save(audio_path_2)
        except Exception as e2:
            raise Exception(f"Both edge-tts and gTTS failed. gTTS Error: {e2}")

    import time
    time.sleep(1.0) # Ensure files are written

    if not (os.path.exists(audio_path_1) and os.path.exists(audio_path_2)):
        raise Exception("Audio files were not created on disk")

    voice_clip_1 = AudioFileClip(audio_path_1).volumex(1.4)
    voice_clip_2 = AudioFileClip(audio_path_2).volumex(1.4)

    reveal_time = voice_clip_1.duration
    total_duration = reveal_time + voice_clip_2.duration + 2.0

    # Pick random sounds dynamically
    sounds_folder = os.path.join(ASSETS_FOLDER, "sounds")
    tick_path = os.path.join(sounds_folder, "clock-ticking-down-376897.mp3")
    hurray_path = os.path.join(sounds_folder, "mixkit-fairy-arcade-sparkle-866.wav")

    tick_sfx = AudioFileClip(tick_path).fx(loop, duration=reveal_time).volumex(0.3)
    hurray_sfx = AudioFileClip(hurray_path).volumex(0.5).set_start(reveal_time)

    final_audio_list = [
        voice_clip_1.set_start(0),
        voice_clip_2.set_start(reveal_time),
        tick_sfx.set_start(0),
        hurray_sfx
    ]

    music_folder = os.path.join(ASSETS_FOLDER, "music")
    music_files = [f for f in os.listdir(music_folder) if f.lower().endswith('.mp3')]
    bg_music = None
    if music_files:
        random_music = os.path.join(music_folder, random.choice(music_files))
        bg_music = AudioFileClip(random_music).fx(loop, duration=total_duration).volumex(0.15).audio_fadeout(1.0)
        final_audio_list.append(bg_music)

    final_audio = CompositeAudioClip(final_audio_list).set_duration(total_duration)

    # 3) Video base
    clip = VideoFileClip(bg_video_path).fx(loop, duration=total_duration)
    clip = clip.resize(height=1920).crop(x1=clip.w / 2 - 540, y1=0, width=1080, height=1920)
    clip = clip.set_audio(final_audio)

    # 4) Text setup
    font_to_use = FONT_PATH if os.path.exists(FONT_PATH) else 'Arial'
    
    # Beautiful Question Card (Red Rounded Rectangle with Bright Red Outlined border matching the second image)
    txt_q = create_rounded_text(
        q_text, fontsize=70, txt_color='white', bg_color=(192, 10, 20, 255), font_path=font_to_use,
        size=(880, None), align='center', padding=35, radius=35, border_color=(255, 80, 80, 255), border_width=10
    ).set_position(('center', 220)).set_duration(total_duration).crossfadein(0.5)

    # High-quality Red Option Cards (A, B, C, D) fully rounded like capsules with White Borders
    opt_labels = ["A", "B", "C", "D"]
    opt_vals = [opt1_val, opt2_val, opt3_val, opt4_val]
    y_coords = [680, 830, 980, 1130]
    
    option_clips = []
    for idx, (label, val, y) in enumerate(zip(opt_labels, opt_vals, y_coords), start=1):
        opt_text = f"  {label})  {val}"
        
        if idx == correct_idx:
            # Active red normal card with White Border before reveal
            normal_before = create_rounded_text(
                opt_text, fontsize=52, txt_color='white', bg_color=(200, 20, 20, 255), font_path=font_to_use,
                size=(880, None), align='West', padding=30, radius=-1, border_color=(255, 255, 255, 255), border_width=5
            ).set_position(('center', y)).set_start(0.5).set_duration(reveal_time - 0.5).crossfadein(0.3)
            
            # Highlighted green card with White Border after reveal
            green_after = create_rounded_text(
                opt_text, fontsize=52, txt_color='white', bg_color=(46, 204, 113, 255), font_path=font_to_use,
                size=(880, None), align='West', padding=30, radius=-1, border_color=(255, 255, 255, 255), border_width=5
            ).set_position(('center', y)).set_start(reveal_time).set_duration(total_duration - reveal_time).crossfadein(0.2)
            
            option_clips.extend([normal_before, green_after])
        else:
            # Normal red option card with White Border before reveal
            normal_before = create_rounded_text(
                opt_text, fontsize=52, txt_color='white', bg_color=(200, 20, 20, 255), font_path=font_to_use,
                size=(880, None), align='West', padding=30, radius=-1, border_color=(255, 255, 255, 255), border_width=5
            ).set_position(('center', y)).set_start(0.5).set_duration(reveal_time - 0.5).crossfadein(0.3)
            
            # Dimmed red card with semi-transparent White Border after reveal
            dimmed_after = create_rounded_text(
                opt_text, fontsize=52, txt_color=(200, 200, 200), bg_color=(130, 20, 20, 100), font_path=font_to_use,
                size=(880, None), align='West', padding=30, radius=-1, border_color=(255, 255, 255, 100), border_width=5
            ).set_position(('center', y)).set_start(reveal_time).set_duration(total_duration - reveal_time).crossfadein(0.2)
            
            option_clips.extend([normal_before, dimmed_after])

    # Beautiful Green Bottom Answer Banner with White Border
    txt_ans = create_rounded_text(
        f"Correct Answer: {correct_label} 🎉", fontsize=75, txt_color='white', bg_color=(39, 174, 96, 255), font_path=font_to_use,
        size=(880, None), align='center', padding=35, radius=30, border_color=(255, 255, 255, 255), border_width=6
    ).set_position(('center', 1350)).set_start(reveal_time).set_duration(total_duration - reveal_time).crossfadein(0.3)

    # 5) Custom Logo Check
    logo_clip_final = None
    if custom_logo_path and os.path.exists(custom_logo_path):
        try:
            logo_size = 140
            logo_clip = ImageClip(custom_logo_path).resize((logo_size, logo_size))

            Y, X = np.ogrid[:logo_size, :logo_size]
            center = (logo_size / 2, logo_size / 2)
            dist_from_center = np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2)
            radius = logo_size / 2

            circular_mask_np = (dist_from_center <= radius) * 1.0
            mask_clip = ImageClip(circular_mask_np, ismask=True)

            logo_clip_final = logo_clip.set_mask(mask_clip).set_position((900, 40)).set_duration(total_duration).fadein(1.0)
        except Exception as e:
            print(f"Logo Processing Warning: {e}")

    final_elements = [clip, txt_q] + option_clips + [txt_ans]
    if logo_clip_final:
        final_elements.append(logo_clip_final)

    final = CompositeVideoClip(final_elements)
    output_path = os.path.join(output_dir, f"quiz_{vid_id}.mp4")

    final.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4,
        verbose=False,
        logger=None
    )

    final.close()
    clip.close()
    txt_q.close()
    for o_clip in option_clips:
        o_clip.close()
    txt_ans.close()
    voice_clip_1.close()
    voice_clip_2.close()
    tick_sfx.close()
    hurray_sfx.close()
    if bg_music:
        bg_music.close()
    if logo_clip_final:
        logo_clip_final.close()

    try:
        if os.path.exists(audio_path_1): os.remove(audio_path_1)
        if os.path.exists(audio_path_2): os.remove(audio_path_2)
    except Exception:
        pass

    return output_path
