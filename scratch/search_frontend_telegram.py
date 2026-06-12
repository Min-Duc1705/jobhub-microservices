import os

frontend_src = "t:/TryHard_IT_Project/Final/Frontend/JobHubFrontend/src"

def search():
    matches = []
    for root, dirs, files in os.walk(frontend_src):
        for f in files:
            if f.endswith(('.ts', '.tsx', '.js', '.jsx', '.json')):
                p = os.path.join(root, f)
                try:
                    content = open(p, encoding='utf-8').read()
                    if 't.me' in content or 'telegram' in content.lower():
                        matches.append(p)
                except Exception:
                    pass
    print(f"Found {len(matches)} files matching 't.me' or 'telegram':")
    for m in matches[:20]:
        print(f"  {m}")

if __name__ == '__main__':
    search()
