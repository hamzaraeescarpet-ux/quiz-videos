import asyncio
import os
import sys

# Add path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from video_generator import create_video_from_row

test_row = {
    "id": 999,
    "question": "What is the capital of France?",
    "option1": "Paris",
    "option2": "London",
    "option3": "Berlin",
    "option4": "Madrid",
    "answer": "Paris"
}

output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output")
os.makedirs(output_dir, exist_ok=True)

try:
    print("Running video generator...")
    result = create_video_from_row(test_row, "Minecraft", None, output_dir)
    print("Result:", result)
except Exception as e:
    import traceback
    traceback.print_exc()
