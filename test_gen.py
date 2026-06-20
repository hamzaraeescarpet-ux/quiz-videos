import sys
import os
from video_generator import create_video_from_row

row = {
    "id": 1,
    "question": "What is 2 + 2?",
    "option1": "3",
    "option2": "4",
    "option3": "5",
    "option4": "6",
    "answer": "4"
}

output_dir = "test_output"
os.makedirs(output_dir, exist_ok=True)

try:
    print("Starting video generation test...")
    out = create_video_from_row(row, "Space", None, output_dir)
    print("Success! Output video path:", out)
except Exception as e:
    import traceback
    print("FAILED with error:")
    print(e)
    traceback.print_exc()
