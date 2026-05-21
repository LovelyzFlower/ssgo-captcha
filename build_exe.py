import os
import subprocess
import sys

def get_package_path(package_name):
    try:
        import importlib.util
        spec = importlib.util.find_spec(package_name)
        if spec is not None and spec.submodule_search_locations:
            return spec.submodule_search_locations[0]
    except Exception as e:
        print(f"Error finding {package_name}: {e}")
    return None

def main():
    print("===================================================")
    print(" Windows EXE Build Script (Python) ")
    print("===================================================")

    try:
        import PyInstaller
    except ImportError:
        print("Installing pyinstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    print("\nFinding resource paths...")
    ctk_path = get_package_path("customtkinter")
    ddddocr_path = get_package_path("ddddocr")

    if not ctk_path or not ddddocr_path:
        print("Error: Could not find required packages. Please run 'pip install -r requirements.txt' first.")
        sys.exit(1)

    print(f"customtkinter path: {ctk_path}")
    print(f"ddddocr path: {ddddocr_path}")

    # Windows에서는 구분자가 ';', Mac/Linux에서는 ':' 입니다.
    sep = ';' if os.name == 'nt' else ':'

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "CaptchaSolver",
        "--add-data", f"{ctk_path}{sep}customtkinter/",
        "--add-data", f"{ddddocr_path}{sep}ddddocr/",
        "ui_app.py"
    ]

    print("\nRunning PyInstaller...")
    subprocess.check_call(cmd)

    print("\n===================================================")
    print(" Build completed successfully!")
    print(" Please check the 'dist/CaptchaSolver' folder.")
    print("===================================================")

if __name__ == "__main__":
    main()
