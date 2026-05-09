import os
import sys
import subprocess

def main():
    print("Starting AI Speaking Agent...", flush=True)
    
    # main.py 파일과 동일한 디렉토리에 있는 app.py의 경로를 찾습니다.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, "app.py")
    
    try:
        # 현재 파이썬 실행 환경에서 streamlit을 모듈로 실행하여 app.py를 호출합니다.
        subprocess.run([sys.executable, "-m", "streamlit", "run", app_path], check=True)
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()
