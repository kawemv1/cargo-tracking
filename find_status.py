# find_Track_creation.py  
with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

print("=== Все места создания Track() ===")
in_track_creation = False
track_lines = []

for i, line in enumerate(lines, 1):
    if 'Track(' in line:
        in_track_creation = True
        track_lines = [(i, line)]
    elif in_track_creation:
        track_lines.append((i, line))
        if ')' in line and '(' not in line:
            in_track_creation = False
            print("\n" + "-"*50)
            for num, text in track_lines:
                print(f"{num}: {text}")
            track_lines = []
