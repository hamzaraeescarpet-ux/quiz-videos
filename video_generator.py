import os
import shutil
import random
import asyncio
import numpy as np
import edge_tts
from moviepy.editor import *
from moviepy.config import change_settings
from moviepy.video.fx.all import loop, fadein
from PIL import Image, ImageDraw, ImageFilter

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
    if font_path == 'Arial':
        font_path = 'Arial-Bold'
    txt_clip = TextClip(
        text, fontsize=fontsize, color=txt_color, font=font_path,
        method='caption', align=align, size=size,
        stroke_color=txt_color, stroke_width=1.5
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

def safe_print(msg):
    try:
        print(msg, flush=True)
    except Exception:
        try:
            print(msg.encode('ascii', errors='replace').decode('ascii'), flush=True)
        except Exception:
            pass
    try:
        log_file = os.path.join(BASE_DIR, "error_logs.txt")
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")
    except Exception:
        pass

import urllib.request
import urllib.parse
import json

def extract_subject(row):
    answer = str(row.get('answer', '')).strip()
    question = str(row.get('question', '')).strip()
    
    # Check if answer is a valid entity (not a simple number, date, or percentage)
    is_number = False
    try:
        float(answer.replace('%', '').replace('$', '').strip())
        is_number = True
    except ValueError:
        pass
        
    if len(answer) > 2 and not is_number and answer.lower() not in ["yes", "no", "true", "false", "none"]:
        return answer
        
    # Fallback to proper nouns in the question
    words = question.split()
    proper_nouns = []
    for idx, w in enumerate(words):
        clean_w = w.strip('?.,!""\'()')
        if idx > 0 and clean_w and clean_w[0].isupper() and clean_w.lower() not in ["the", "a", "an", "is", "are", "which", "what", "who", "where", "when", "how"]:
            proper_nouns.append(clean_w)
            
    if proper_nouns:
        return " ".join(proper_nouns)
        
    return answer

def fetch_wikipedia_image(subject):
    import ssl
    try:
        context = ssl._create_unverified_context()
        # Step 1: Search Wikipedia for the best matching page title
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(subject)}&utf8=&format=json&srlimit=1"
        req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
        with urllib.request.urlopen(req, timeout=10, context=context) as response:
            search_data = json.loads(response.read().decode('utf-8'))
            search_results = search_data.get("query", {}).get("search", [])
            if not search_results:
                return None
            best_title = search_results[0]["title"]
            
        # Step 2: Get the thumbnail image of the best matching page (max width 1280)
        image_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=thumbnail&pithumbsize=1280&titles={urllib.parse.quote(best_title)}&redirects=1"
        req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
        with urllib.request.urlopen(req, timeout=10, context=context) as response:
            img_data = json.loads(response.read().decode('utf-8'))
            pages = img_data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if "thumbnail" in page_data:
                    return page_data["thumbnail"]["source"]
    except Exception as e:
        safe_print(f"Error fetching Wikipedia image for {subject}: {e}")
    return None

def create_parallax_background_files(image_path, temp_dir, vid_id):
    img = Image.open(image_path).convert("RGBA")
    
    # 1. Generate full-screen background (1080x1920)
    bg_w, bg_h = 1080, 1920
    scale = max(bg_w / img.width, bg_h / img.height)
    new_w = int(img.width * scale) + 1
    new_h = int(img.height * scale) + 1
    bg_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    left = (new_w - bg_w) // 2
    top = (new_h - bg_h) // 2
    bg_cropped = bg_resized.crop((left, top, left + bg_w, top + bg_h))
    
    # Apply 30% Black Overlay for HD look and readability (no blur)
    overlay = Image.new("RGBA", bg_cropped.size, (0, 0, 0, 80))
    bg_final = Image.alpha_composite(bg_cropped, overlay)
    
    bg_path = os.path.join(temp_dir, f"temp_full_bg_{vid_id}.png")
    bg_final.save(bg_path, "PNG")
    return bg_path

async def generate_voice(text, filename):
    voice = "en-US-ChristopherNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)

async def generate_both_audios(speech_1, audio_path_1, speech_2, audio_path_2):
    await asyncio.gather(
        generate_voice(speech_1, audio_path_1),
        generate_voice(speech_2, audio_path_2)
    )

def hex_to_rgb(hex_str, default_rgb):
    if not hex_str:
        return default_rgb
    hex_str = hex_str.lstrip('#')
    try:
        if len(hex_str) == 6:
            return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        return default_rgb
    except Exception:
        return default_rgb

# safe_print was moved to the top of the file

def resolve_local_fallback_bg(category, tried_paths):
    category_path = os.path.join(BG_VIDEO_FOLDER, category)
    
    # Step A: Category direct files
    if os.path.exists(category_path) and os.path.isdir(category_path):
        bg_files = [os.path.join(category_path, f) for f in os.listdir(category_path) if f.lower().endswith((".mp4", ".mov", ".mkv", ".webm"))]
        available = [p for p in bg_files if p not in tried_paths]
        if available:
            return random.choice(available)
            
    # Step B: Recursive search in backgrounds/
    all_fallback_videos = []
    for root_dir, dirs, files in os.walk(BG_VIDEO_FOLDER):
        for file in files:
            if file.lower().endswith((".mp4", ".mov", ".mkv", ".webm")):
                path = os.path.join(root_dir, file)
                if path not in tried_paths:
                    all_fallback_videos.append(path)
    if all_fallback_videos:
        return random.choice(all_fallback_videos)
        
    # Step C: cache directory
    cache_dir = os.path.join(BASE_DIR, "backgrounds_cache")
    if os.path.exists(cache_dir) and os.path.isdir(cache_dir):
        cache_files = [os.path.join(cache_dir, f) for f in os.listdir(cache_dir) if f.lower().endswith((".mp4", ".mov", ".mkv", ".webm"))]
        available = [os.path.join(cache_dir, f) for f in cache_files if os.path.join(cache_dir, f) not in tried_paths]
        if available:
            return random.choice(available)
            
    # Step D: root directory
    root_files = [os.path.join(BASE_DIR, f) for f in os.listdir(BASE_DIR) if f.lower().endswith((".mp4", ".mov", ".mkv", ".webm"))]
    available = [p for p in root_files if p not in tried_paths]
    if available:
        return random.choice(available)
        
    return None

def load_bg_clip_safely(bg_video_path, category, custom_bg_paths=None):
    tried_paths = set()
    
    while True:
        if not bg_video_path or bg_video_path in tried_paths:
            # Pick from custom_bg_paths first (excluding tried ones)
            available_custom = [p for p in (custom_bg_paths or []) if p not in tried_paths]
            if available_custom:
                bg_video_path = random.choice(available_custom)
            else:
                bg_video_path = resolve_local_fallback_bg(category, tried_paths)
                
        if not bg_video_path:
            raise Exception("No valid background video files could be resolved.")
            
        safe_print(f"Attempting to load background video clip: {bg_video_path}")
        tried_paths.add(bg_video_path)
        
        try:
            clip = VideoFileClip(bg_video_path, audio=False)
            fps = clip.fps
            if not fps or fps <= 0:
                raise ValueError("Video file has invalid FPS metadata.")
            # Success!
            return clip, bg_video_path
        except Exception as e:
            safe_print(f"Error loading background clip {bg_video_path}: {e}. Deleting bad file and falling back...")
            # Delete corrupted file if it exists
            if os.path.exists(bg_video_path):
                try:
                    os.remove(bg_video_path)
                    safe_print(f"Deleted corrupted background file: {bg_video_path}")
                except Exception as del_err:
                    safe_print(f"Could not delete corrupted file {bg_video_path}: {del_err}")
            bg_video_path = None

def create_video_from_row(row, category, custom_logo_path, output_dir, box_color=None, custom_bg_paths=None):
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

    # 1) Background pick dynamically
    if custom_bg_paths and len(custom_bg_paths) > 0:
        bg_video_path = random.choice(custom_bg_paths)
    else:
        bg_video_path = None
        category_path = os.path.join(BG_VIDEO_FOLDER, category)
        try:
            # Step A: Try to find video files directly in the specific category directory
            if os.path.exists(category_path) and os.path.isdir(category_path):
                bg_files = [f for f in os.listdir(category_path) if f.lower().endswith((".mp4", ".mov", ".mkv", ".webm"))]
                if bg_files:
                    bg_video_path = os.path.join(category_path, random.choice(bg_files))
            
            # Step B: If not found in the category directory, search recursively in BG_VIDEO_FOLDER
            if not bg_video_path:
                safe_print(f"Fallback: No videos directly in category '{category}' folder ({category_path}). Searching recursively in {BG_VIDEO_FOLDER}...")
                all_fallback_videos = []
                for root_dir, dirs, files in os.walk(BG_VIDEO_FOLDER):
                    for file in files:
                        if file.lower().endswith((".mp4", ".mov", ".mkv", ".webm")):
                            all_fallback_videos.append(os.path.join(root_dir, file))
                
                if all_fallback_videos:
                    bg_video_path = random.choice(all_fallback_videos)
                    safe_print(f"Fallback selected recursive video: {bg_video_path}")
            
            # Step C: If still not found, check in backgrounds_cache
            if not bg_video_path:
                cache_dir = os.path.join(BASE_DIR, "backgrounds_cache")
                safe_print(f"Fallback: Searching in cache directory {cache_dir}...")
                if os.path.exists(cache_dir) and os.path.isdir(cache_dir):
                    cache_files = [f for f in os.listdir(cache_dir) if f.lower().endswith((".mp4", ".mov", ".mkv", ".webm"))]
                    if cache_files:
                        bg_video_path = os.path.join(cache_dir, random.choice(cache_files))
                        safe_print(f"Fallback selected cache video: {bg_video_path}")
            
            # Step D: If still not found, look in BASE_DIR root for any mp4 files
            if not bg_video_path:
                safe_print(f"Fallback: Searching in root directory {BASE_DIR}...")
                root_files = [f for f in os.listdir(BASE_DIR) if f.lower().endswith((".mp4", ".mov", ".mkv", ".webm"))]
                if root_files:
                    bg_video_path = os.path.join(BASE_DIR, random.choice(root_files))
                    safe_print(f"Fallback selected root video: {bg_video_path}")
            
            if not bg_video_path:
                raise Exception(f"No background files found anywhere. Checked {category_path}, recursive {BG_VIDEO_FOLDER}, cache, and root.")
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
    is_image_bg = False
    temp_image_clips = []
    temp_image_paths = []
    
    if "image" in category.lower():
        try:
            subject = extract_subject(row)
            safe_print(f"Extracted subject for contextual image: '{subject}'")
            image_url = fetch_wikipedia_image(subject)
            if image_url:
                safe_print(f"Found Wikipedia image URL: {image_url}")
                parsed_url = urllib.parse.urlparse(image_url)
                ext = os.path.splitext(parsed_url.path)[1]
                if not ext or ext.lower() not in [".png", ".jpg", ".jpeg", ".webp"]:
                    ext = ".png"
                raw_filename = f"temp_raw_{vid_id}{ext}"
                local_img_path = os.path.join(TEMP_FOLDER, raw_filename)
                
                import ssl
                req = urllib.request.Request(image_url, headers={'User-Agent': 'QuizViralBot/1.0'})
                with urllib.request.urlopen(req, timeout=15, context=ssl._create_unverified_context()) as response:
                    with open(local_img_path, "wb") as f:
                        f.write(response.read())
                
                bg_img_path = create_parallax_background_files(local_img_path, TEMP_FOLDER, vid_id)
                temp_image_paths.extend([local_img_path, bg_img_path])
                
                bg_layer = ImageClip(bg_img_path).set_duration(total_duration)
                
                try:
                    bg_layer = bg_layer.resize(lambda t: 1.0 + 0.1 * (t / total_duration))
                except Exception:
                    pass
                
                clip = bg_layer.set_audio(final_audio)
                temp_image_clips.append(bg_layer)
                is_image_bg = True
                safe_print("Successfully built animated contextual image background.")
            else:
                safe_print("Wikipedia image URL not found. Falling back to default video background.")
        except Exception as e:
            safe_print(f"Failed to create image background: {e}. Falling back to default video background.")

    if not is_image_bg:
        clip, resolved_path = load_bg_clip_safely(bg_video_path, category, custom_bg_paths)
        clip = clip.fx(loop, duration=total_duration)
        # Skip expensive CPU resize/crop operations if the video is already 1080x1920
        if clip.w != 1080 or clip.h != 1920:
            target_ratio = 1080 / 1920
            clip_ratio = clip.w / clip.h
            if clip_ratio > target_ratio:
                # Video is wider than target (landscape or less vertical)
                clip = clip.resize(height=1920)
                x1 = (clip.w - 1080) / 2
                clip = clip.crop(x1=x1, y1=0, width=1080, height=1920)
            else:
                # Video is narrower than target (more vertical)
                clip = clip.resize(width=1080)
                y1 = (clip.h - 1920) / 2
                clip = clip.crop(x1=0, y1=y1, width=1080, height=1920)
        clip = clip.set_audio(final_audio)

    # 4) Text setup
    font_to_use = FONT_PATH if os.path.exists(FONT_PATH) else 'Arial'
    
    # Simple plain theme color (Vibrant stylish red "#E74C3C" by default, or user custom color)
    theme_color = box_color if box_color else "#E74C3C"
    theme_rgb = hex_to_rgb(theme_color, (231, 76, 60))
    
    # Beautiful Question Card using plain theme color with solid white border (6px)
    txt_q = create_rounded_text(
        q_text, fontsize=70, txt_color='white', bg_color=theme_rgb + (255,), font_path=font_to_use,
        size=(800, None), align='center', padding=25, radius=35, border_color=(255, 255, 255, 255), border_width=6
    ).set_position(('center', 220)).set_duration(total_duration).crossfadein(0.5)

    # High-quality dynamic Option Cards (A, B, C, D) fully rounded like capsules with White Borders
    opt_labels = ["A", "B", "C", "D"]
    opt_vals = [opt1_val, opt2_val, opt3_val, opt4_val]
    y_coords = [680, 830, 980, 1130]
    
    option_clips = []
    for idx, (label, val, y) in enumerate(zip(opt_labels, opt_vals, y_coords), start=1):
        opt_text = f"  {label})  {val}"
        
        if idx == correct_idx:
            # Active normal card before reveal with thick white border (padding=30 for narrower look)
            normal_before = create_rounded_text(
                opt_text, fontsize=52, txt_color='white', bg_color=theme_rgb + (255,), font_path=font_to_use,
                size=(800, None), align='West', padding=30, radius=-1, border_color=(255, 255, 255, 255), border_width=5
            ).set_position(('center', y)).set_start(0.5).set_duration(reveal_time - 0.5).crossfadein(0.3)
            
            # Active green card after reveal with thick white border
            green_after = create_rounded_text(
                opt_text, fontsize=52, txt_color='white', bg_color=(46, 204, 113, 255), font_path=font_to_use,
                size=(800, None), align='West', padding=30, radius=-1, border_color=(255, 255, 255, 255), border_width=5
            ).set_position(('center', y)).set_start(reveal_time).set_duration(total_duration - reveal_time).crossfadein(0.2)
            
            option_clips.extend([normal_before, green_after])
        else:
            # Normal card before reveal with thick white border
            normal_before = create_rounded_text(
                opt_text, fontsize=52, txt_color='white', bg_color=theme_rgb + (255,), font_path=font_to_use,
                size=(800, None), align='West', padding=30, radius=-1, border_color=(255, 255, 255, 255), border_width=5
            ).set_position(('center', y)).set_start(0.5).set_duration(reveal_time - 0.5).crossfadein(0.3)
            
            # Dimmed card after reveal (to highlight the correct answer) - keeps theme color but with transparency
            dimmed_after = create_rounded_text(
                opt_text, fontsize=52, txt_color='#d0d0d0', bg_color=theme_rgb + (100,), font_path=font_to_use,
                size=(800, None), align='West', padding=30, radius=-1, border_color=(255, 255, 255, 100), border_width=5
            ).set_position(('center', y)).set_start(reveal_time).set_duration(total_duration - reveal_time).crossfadein(0.2)
            
            option_clips.extend([normal_before, dimmed_after])

    # Beautiful Green Bottom Answer Banner with White Border
    txt_ans = create_rounded_text(
        f"Correct Answer: {correct_label} 🎉", fontsize=75, txt_color='white', bg_color=(39, 174, 96, 255), font_path=font_to_use,
        size=(800, None), align='center', padding=25, radius=30, border_color=(255, 255, 255, 255), border_width=6
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

            logo_clip_final = logo_clip.set_mask(mask_clip).set_position((840, 40)).set_duration(total_duration).fadein(1.0)
        except Exception as e:
            print(f"Logo Processing Warning: {e}")

    final_elements = [clip, txt_q] + option_clips + [txt_ans]
    if logo_clip_final:
        final_elements.append(logo_clip_final)

    final = CompositeVideoClip(final_elements)
    output_path = os.path.join(output_dir, f"quiz_{vid_id}.mp4")

    # Use a specific temp_audiofile in the temp folder to avoid Windows permission/lock issues
    temp_audio_file_path = os.path.join(TEMP_FOLDER, f"temp_audio_merge_{vid_id}.m4a")

    final.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=temp_audio_file_path,
        remove_temp=True,
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
        if os.path.exists(temp_audio_file_path):
            try:
                os.remove(temp_audio_file_path)
            except Exception:
                pass
    except Exception:
        pass

    if is_image_bg:
        for c in temp_image_clips:
            try:
                c.close()
            except Exception:
                pass
        for p in temp_image_paths:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

    return output_path
