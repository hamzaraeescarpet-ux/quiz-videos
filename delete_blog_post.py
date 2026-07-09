import os
import re
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BLOG_POSTS_FILE = os.path.join(SCRIPT_DIR, "frontend", "src", "data", "blogPosts.js")

def parse_posts_blocks(file_content):
    # Find the array content inside export const blogPosts = [ ... ];
    match = re.search(r"export const blogPosts = \[(.*)\];\s*$", file_content, re.DOTALL)
    if not match:
        return []
    array_content = match.group(1).strip()
    
    blocks = []
    current_block = []
    depth = 0
    in_string = False
    quote_char = None
    escaped = False
    
    for char in array_content:
        current_block.append(char)
        if escaped:
            escaped = False
            continue
        if char == '\\':
            escaped = True
            continue
        if in_string:
            if char == quote_char:
                in_string = False
            continue
        if char in ('"', "'", '`'):
            in_string = True
            quote_char = char
            continue
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                block_str = "".join(current_block).strip()
                if block_str.endswith(","):
                    block_str = block_str[:-1].strip()
                block_str = block_str.lstrip(",").strip()
                blocks.append(block_str)
                current_block = []
                
    return blocks

def get_property(block_str, key):
    pattern = rf'\b{key}:\s*(["\'`])'
    match = re.search(pattern, block_str)
    if not match:
        return None
    start_idx = match.end()
    quote_char = match.group(1)
    
    val_chars = []
    escaped = False
    for char in block_str[start_idx:]:
        if escaped:
            val_chars.append(char)
            escaped = False
            continue
        if char == '\\':
            val_chars.append(char)
            escaped = True
            continue
        if char == quote_char:
            break
        val_chars.append(char)
    return "".join(val_chars)

def git_push_changes(title):
    print("Staging and pushing changes to GitHub and Hugging Face...")
    try:
        # Push to GitHub
        subprocess.run(["git", "add", "."], cwd=SCRIPT_DIR, check=True)
        subprocess.run(["git", "commit", "-m", f"chore(blog): delete blog post: {title}"], cwd=SCRIPT_DIR, check=True)
        print("Pushing to GitHub...")
        subprocess.run(["git", "push", "github", "main"], cwd=SCRIPT_DIR, check=True)
        subprocess.run(["git", "push", "github", "main:master"], cwd=SCRIPT_DIR, check=True)
        
        # Push to Hugging Face
        try:
            print("Pushing to Hugging Face Space...")
            subprocess.run(["git", "push", "origin", "main"], cwd=SCRIPT_DIR, check=True)
        except Exception as he:
            print(f"Warning: Push to Hugging Face (origin) failed or was skipped: {he}.")
            print("This is normal as Hugging Face space rejects non-LFS images. Your GitHub/Vercel changes are still safe!")
        print("Git Push Completed! Deployments triggered.")
    except Exception as e:
        print(f"Git push failed: {e}")

def main():
    if not os.path.exists(BLOG_POSTS_FILE):
        print(f"Error: {BLOG_POSTS_FILE} not found.")
        return
        
    with open(BLOG_POSTS_FILE, "r", encoding="utf-8") as f:
        file_content = f.read()
        
    blocks = parse_posts_blocks(file_content)
    if not blocks:
        print("No blog posts found in the file.")
        return
        
    print("\n================ AVAILABLE BLOG POSTS ================")
    for idx, block in enumerate(blocks):
        title = get_property(block, "title") or "Untitled"
        date = get_property(block, "date") or "Unknown Date"
        print(f"[{idx + 1}] {title} ({date})")
    print("======================================================\n")
    
    try:
        user_input = input("Enter the number of the blog post you want to delete (or 'q' to quit): ").strip()
        if user_input.lower() == 'q':
            print("Operation cancelled.")
            return
            
        choice = int(user_input)
        if choice < 1 or choice > len(blocks):
            print("Invalid number.")
            return
            
        selected_block = blocks[choice - 1]
        selected_title = get_property(selected_block, "title") or "Untitled"
        
        confirm = input(f"\nAre you sure you want to delete: '{selected_title}'? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Operation cancelled.")
            return
            
        # Remove the selected block
        blocks.pop(choice - 1)
        
        # Reconstruct the file content
        new_array_content = ",\n  ".join(blocks)
        new_file_content = f"export const blogPosts = [\n  {new_array_content}\n];\n"
        
        with open(BLOG_POSTS_FILE, "w", encoding="utf-8") as f:
            f.write(new_file_content)
            
        print(f"\nSuccessfully deleted '{selected_title}' from blogPosts.js!")
        
        # Run local build validation
        print("Running build verification...")
        build_res = subprocess.run(["npm", "run", "build"], cwd=os.path.join(SCRIPT_DIR, "frontend"), shell=True)
        if build_res.returncode == 0:
            git_push_changes(selected_title)
        else:
            print("Local build check failed! Aborting Git Push to avoid breaking production.")
            
    except ValueError:
        print("Please enter a valid number.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
