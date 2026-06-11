import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = r"C:\Users\ACER\.gemini\antigravity\brain\ee0d145f-13ae-434d-b8e1-c48496708331"
BASE_URL = "http://localhost:5174"

def main():
    if not os.path.exists(ARTIFACT_DIR):
        os.makedirs(ARTIFACT_DIR)
        
    print(f"Artifact directory is: {ARTIFACT_DIR}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"Console [{msg.type}]: {msg.text}"))
        page.on("pageerror", lambda err: console_messages.append(f"Page Error: {err.message}"))
        
        def take_screenshot(name, description):
            path = os.path.join(ARTIFACT_DIR, name)
            page.screenshot(path=path)
            print(f"✔ Screenshot saved: {name} - {description}")
            
        print("\n--- 1. Testing Public Pages ---")
        
        # Home Page
        try:
            print("Visiting Home Page...")
            page.goto(f"{BASE_URL}/")
            time.sleep(2)
            take_screenshot("step1_homepage.png", "Home Page")
        except Exception as e:
            print(f"❌ Home Page failed: {e}")
            
        # Jobs Page
        try:
            print("Visiting Jobs Page...")
            page.goto(f"{BASE_URL}/jobs")
            time.sleep(2)
            take_screenshot("step2_jobs.png", "Jobs List")
        except Exception as e:
            print(f"❌ Jobs Page failed: {e}")
            
        # Companies Page
        try:
            print("Visiting Companies Page...")
            page.goto(f"{BASE_URL}/companies")
            time.sleep(2)
            take_screenshot("step3_companies.png", "Companies List")
        except Exception as e:
            print(f"❌ Companies Page failed: {e}")
            
        # Salary Predictor Page
        try:
            print("Visiting Salary Predictor Page...")
            page.goto(f"{BASE_URL}/salary-predict")
            time.sleep(2)
            
            # Fill Job Title using ID selector
            if page.locator("#jobTitle").count() > 0:
                print("Filling Job Title...")
                page.locator("#jobTitle").fill("FullStack Developer")
                time.sleep(1)
                
            # Click predict button
            if page.locator(".salary-btn").count() > 0:
                print("Clicking Dự đoán lương button...")
                page.locator(".salary-btn").click()
                time.sleep(3)
                take_screenshot("step4_salary_predict_results.png", "Salary Prediction Results")
            else:
                print("Salary prediction button (.salary-btn) not found.")
                take_screenshot("step4_salary_predict_page.png", "Salary Predictor Page (No prediction)")
        except Exception as e:
            print(f"❌ Salary Predictor failed: {e}")
            
        print("\n--- 2. Testing Candidate Flow ---")
        try:
            print("Navigating to Login...")
            page.goto(f"{BASE_URL}/login")
            time.sleep(2)
            take_screenshot("step5_login_page.png", "Login Page")
            
            print("Logging in as Candidate...")
            page.locator("#email").fill("bui.anh.phong@outlook.com")
            page.locator("#password").fill("Candidate@123456")
            time.sleep(1)
            page.locator(".btn-login").click()
            
            # Wait for login and redirect
            print("Waiting for login redirect...")
            time.sleep(4)
            take_screenshot("step6_candidate_logged_in.png", "Candidate Logged In Dashboard")
            
            # Go to Profile Settings
            print("Visiting Candidate Profile...")
            page.goto(f"{BASE_URL}/candidate/profile")
            time.sleep(2)
            take_screenshot("step7_candidate_profile.png", "Candidate Profile Settings")
            
            # Go to Resume Manager
            print("Visiting Candidate Resume Manager...")
            page.goto(f"{BASE_URL}/candidate/resume")
            time.sleep(2)
            take_screenshot("step8_candidate_resume.png", "Candidate Resume Manager")
            
            # Go to Chat
            print("Visiting Candidate Chat...")
            page.goto(f"{BASE_URL}/chat")
            time.sleep(3)
            take_screenshot("step9_candidate_chat.png", "Candidate Chat Page")
            
        except Exception as e:
            print(f"❌ Candidate Flow failed: {e}")
            
        print("\n--- 3. Testing HR Flow ---")
        try:
            print("Logging out (clearing state)...")
            context.clear_cookies()
            page.evaluate("localStorage.clear()")
            
            print("Navigating to Login for HR...")
            page.goto(f"{BASE_URL}/login")
            time.sleep(2)
            
            print("Logging in as HR...")
            page.locator("#email").fill("hr.helix_innovation@jobhub.vn")
            page.locator("#password").fill("HRPassword@123456")
            time.sleep(1)
            page.locator(".btn-login").click()
            
            # Wait for login and redirect
            print("Waiting for HR login redirect...")
            time.sleep(4)
            take_screenshot("step10_hr_logged_in.png", "HR Logged In Dashboard")
            
            # Go to HR Jobs
            print("Visiting HR Job Management...")
            page.goto(f"{BASE_URL}/hr/jobs")
            time.sleep(2)
            take_screenshot("step11_hr_jobs.png", "HR Jobs Page")
            
            # Go to HR Hire Agent
            print("Visiting HR Hire Agent...")
            page.goto(f"{BASE_URL}/hr/hire-agent")
            time.sleep(2)
            take_screenshot("step12_hr_hire_agent.png", "HR Hire Agent Page")
            
            # Go to Admin Panel
            print("Visiting Admin Dashboard...")
            page.goto(f"{BASE_URL}/admin/dashboard")
            time.sleep(3)
            take_screenshot("step13_admin_dashboard.png", "Admin Dashboard Page")
            
        except Exception as e:
            print(f"❌ HR Flow failed: {e}")
            
        # Save logs
        console_log_path = os.path.join(ARTIFACT_DIR, "console_logs.txt")
        with open(console_log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(console_messages))
        print(f"\n✔ All tests completed. Console logs saved to console_logs.txt")
        
        browser.close()

if __name__ == "__main__":
    main()
