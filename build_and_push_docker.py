import os
import re
import sys
import subprocess

def run_command(command, cwd=None):
    print(f"\n> Running: {command} (in {cwd or 'current dir'})")
    process = subprocess.Popen(command, shell=True, cwd=cwd)
    process.communicate()
    if process.returncode != 0:
        print(f"Error: Command failed with exit code {process.returncode}")
        return False
    return True

def generate_deploy_compose(username):
    # 1. Backend docker-compose.deploy.yml
    backend_path = r"t:\TryHard_IT_Project\Final\Backend\docker-compose.yml"
    backend_deploy_path = r"t:\TryHard_IT_Project\Final\Backend\docker-compose.deploy.yml"
    
    if os.path.exists(backend_path):
        with open(backend_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Remove build: blocks
        # This matches 'build:' followed by indented lines (context, dockerfile)
        cleaned = re.sub(r'[ \t]*build:\s*\n([ \t]+[^\n]*\n)*', '', content)
        
        # Replace image names: jobhub-xxx -> username/jobhub-xxx
        replaced = re.sub(r'image:\s*jobhub-([a-zA-Z0-9\-_]+)(:latest)?', f'image: {username}/jobhub-\\1:latest', cleaned)
        
        with open(backend_deploy_path, "w", encoding="utf-8") as f:
            f.write(replaced)
        print(f"Created backend deploy file: {backend_deploy_path}")
        
    # 2. Frontend docker-compose.deploy.yml
    frontend_path = r"t:\TryHard_IT_Project\Final\Frontend\JobHubFrontend\docker-compose.yml"
    frontend_deploy_path = r"t:\TryHard_IT_Project\Final\Frontend\JobHubFrontend\docker-compose.deploy.yml"
    
    if os.path.exists(frontend_path):
        with open(frontend_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        cleaned = re.sub(r'[ \t]*build:\s*\n([ \t]+[^\n]*\n)*', '', content)
        replaced = re.sub(r'image:\s*jobhub-frontend(:latest)?', f'image: {username}/jobhub-frontend:latest', cleaned)
        
        with open(frontend_deploy_path, "w", encoding="utf-8") as f:
            f.write(replaced)
        print(f"Created frontend deploy file: {frontend_deploy_path}")

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    print("==================================================")
    print("      DOCKER HUB BUILD & PUSH AUTOMATION SCRIPT   ")
    print("==================================================")
    
    username = input("Nhập Docker Hub Username của bạn: ").strip()
    if not username:
        print("Lỗi: Username không được để trống.")
        return

    # Check docker connection
    if not run_command("docker ps"):
        print("Lỗi: Không kết nối được với Docker daemon. Vui lòng mở Docker Desktop trước.")
        return

    # 1. Option to build from source code
    build_opt = input("Bạn có muốn build lại các image từ source code trước khi push không? (y/n): ").strip().lower()
    if build_opt == 'y':
        print("\n--- 1. Building Backend Images ---")
        if not run_command("docker compose build", cwd=r"t:\TryHard_IT_Project\Final\Backend"):
            print("Lỗi build Backend.")
            return
            
        print("\n--- 2. Building Frontend Image ---")
        if not run_command("docker compose build", cwd=r"t:\TryHard_IT_Project\Final\Frontend\JobHubFrontend"):
            print("Lỗi build Frontend.")
            return

    # 2. Tag and Push images
    backend_images = [
        "jobhub-authservice",
        "jobhub-jobservice",
        "jobhub-companyservice",
        "jobhub-profileservice",
        "jobhub-resumeservice",
        "jobhub-notificationservice",
        "jobhub-apigateway",
        "jobhub-cvintelligenceservice",
        "jobhub-dataanalyticsservice"
    ]
    
    print("\n--- 3. Tagging and Pushing Backend Images ---")
    for img in backend_images:
        local_tag = f"{img}:latest"
        hub_tag = f"{username}/{img}:latest"
        
        print(f"\n>> Tagging {local_tag} -> {hub_tag}")
        if not run_command(f"docker tag {local_tag} {hub_tag}"):
            continue
            
        print(f">> Pushing {hub_tag}")
        run_command(f"docker push {hub_tag}")

    print("\n--- 4. Tagging and Pushing Frontend Image ---")
    local_tag = "jobhub-frontend:latest"
    hub_tag = f"{username}/jobhub-frontend:latest"
    print(f"\n>> Tagging {local_tag} -> {hub_tag}")
    if run_command(f"docker tag {local_tag} {hub_tag}"):
        print(f">> Pushing {hub_tag}")
        run_command(f"docker push {hub_tag}")

    # 3. Generate deployment docker-compose files
    print("\n--- 5. Generating deployment docker-compose files ---")
    generate_deploy_compose(username)
    
    print("\n==================================================")
    print("                   HOÀN TẤT!                      ")
    print("==================================================")
    print("Mọi image đã được đẩy lên Docker Hub.")
    print("Bạn chỉ cần copy 2 file sau sang máy thầy cô để chạy:")
    print(r"1. Backend: Backend\docker-compose.deploy.yml")
    print(r"2. Frontend: Frontend\JobHubFrontend\docker-compose.deploy.yml")
    print("Lệnh chạy: docker compose -f docker-compose.deploy.yml up -d")
    print("==================================================")

if __name__ == "__main__":
    main()
