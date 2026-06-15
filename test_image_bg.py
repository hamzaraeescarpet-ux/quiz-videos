import asyncio
import os
import sys

# Add path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from video_generator import create_video_from_row

test_rows = [
    {
        "id": 101,
        "question": "Which country is famous for the Eiffel Tower?",
        "option1": "France",
        "option2": "Germany",
        "option3": "Spain",
        "option4": "Italy",
        "answer": "France"
    },
    {
        "id": 102,
        "question": "Which company created the Windows operating system?",
        "option1": "Apple",
        "option2": "Microsoft",
        "option3": "Google",
        "option4": "Meta",
        "answer": "Microsoft"
    }
]

output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output")
os.makedirs(output_dir, exist_ok=True)

for row in test_rows:
    try:
        print(f"\n--- Running video generator for Question ID {row['id']} ---")
        result = create_video_from_row(row, "Contextual Images 🖼️", None, output_dir)
        print("Successfully generated video:", result)
    except Exception as e:
        import traceback
        traceback.print_exc()
