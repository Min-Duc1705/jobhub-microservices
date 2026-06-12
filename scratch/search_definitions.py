import re

def search():
    with open('t:/TryHard_IT_Project/Final/Backend/JobHub/CVIntelligenceService/app/services/ai_assistant_service/tools/definitions.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    match = re.search(r'name\s*:\s*["\']get_applications_for_job["\'].*?\}', content, re.DOTALL)
    if match:
        print("=== get_applications_for_job ===")
        print(match.group(0))
    else:
        # Search anywhere
        pos = content.find("get_applications_for_job")
        if pos != -1:
            print("=== Found in definitions.py ===")
            print(content[pos-200:pos+800])
        else:
            print("Not found in definitions.py")

if __name__ == '__main__':
    search()
