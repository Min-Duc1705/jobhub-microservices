import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')
BASE_URL = "http://localhost:5174"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"Navigating to {BASE_URL}/login...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_timeout(3000)
        
        print(f"Current URL: {page.url}")
        print(f"Page Title: {page.title()}")
        
        # Check if there are inputs
        inputs = page.locator("input")
        print(f"Input elements count: {inputs.count()}")
        for i in range(inputs.count()):
            input_el = inputs.nth(i)
            print(f"  Input {i}: id={input_el.get_attribute('id')}, type={input_el.get_attribute('type')}, placeholder={input_el.get_attribute('placeholder')}")
            
        buttons = page.locator("button")
        print(f"Button elements count: {buttons.count()}")
        for i in range(buttons.count()):
            btn = buttons.nth(i)
            print(f"  Button {i}: text='{btn.inner_text()}', class='{btn.get_attribute('class')}'")
            
        print("\nPage body text (first 500 chars):")
        print(page.locator("body").inner_text()[:500])
        
        browser.close()

if __name__ == "__main__":
    main()
