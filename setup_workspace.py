import os
import shutil

base_dir = r"c:\Users\hamza\OneDrive\Desktop\QuizBot"
bg_dir = os.path.join(base_dir, "backgrounds")
assets_dir = os.path.join(base_dir, "assets")

# Create category subfolders
categories = ["Minecraft", "Satisfying", "Nature", "Space"]
for cat in categories:
    os.makedirs(os.path.join(bg_dir, cat), exist_ok=True)

# Distribute existing videos into categories
videos = [f for f in os.listdir(bg_dir) if f.endswith('.mp4')]
for i, vid in enumerate(videos):
    cat = categories[i % len(categories)]
    shutil.move(os.path.join(bg_dir, vid), os.path.join(bg_dir, cat, vid))

# Organize assets
os.makedirs(os.path.join(assets_dir, "music"), exist_ok=True)
os.makedirs(os.path.join(assets_dir, "sounds"), exist_ok=True)
os.makedirs(os.path.join(assets_dir, "fonts"), exist_ok=True)

for f in os.listdir(assets_dir):
    src = os.path.join(assets_dir, f)
    if os.path.isfile(src):
        if f.endswith('.mp3') and 'synthwave' in f:
            shutil.move(src, os.path.join(assets_dir, "music", f))
        elif f.endswith('.mp3') or f.endswith('.wav'):
            shutil.move(src, os.path.join(assets_dir, "sounds", f))
        elif f.endswith('.ttf'):
            shutil.move(src, os.path.join(assets_dir, "fonts", f))

print("Workspace organized.")
