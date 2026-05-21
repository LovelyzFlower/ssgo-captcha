import os
import sys
import time
import base64
import re
import threading
import cv2
import numpy as np
import ddddocr
from PIL import Image, ImageTk
import customtkinter as ctk

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

TARGET_URL = "https://ssgo.scourt.go.kr/ssgo/index.on"
CAPTCHA_ID = "mf_ssgoTopMainTab_contents_content1_body_img_captcha"

# GUI 테마 설정
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class RedirectText:
    def __init__(self, textbox):
        self.textbox = textbox

    def write(self, string):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", string)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def flush(self):
        pass

class CaptchaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("대법원 전자소송 CAPTCHA 솔버")
        self.geometry("900x500")
        
        # Grid 레이아웃 설정
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 왼쪽 프레임 (로그 출력)
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        self.log_label = ctk.CTkLabel(self.log_frame, text="작업 로그", font=("Arial", 16, "bold"))
        self.log_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")

        self.log_textbox = ctk.CTkTextbox(self.log_frame, font=("Consolas", 12))
        self.log_textbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.log_textbox.configure(state="disabled")
        
        # stdout을 Textbox로 리디렉션
        sys.stdout = RedirectText(self.log_textbox)

        # 오른쪽 프레임 (상태, 결과, 캡챠 이미지, 버튼)
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.control_frame.grid_columnconfigure(0, weight=1)
        
        self.img_label = ctk.CTkLabel(self.control_frame, text="이미지 대기 중...", width=200, height=80, fg_color="gray20", corner_radius=8)
        self.img_label.grid(row=0, column=0, padx=20, pady=20)
        
        self.result_title = ctk.CTkLabel(self.control_frame, text="인식 결과", font=("Arial", 14))
        self.result_title.grid(row=1, column=0, padx=20, pady=(10, 0))
        
        self.result_label = ctk.CTkLabel(self.control_frame, text="-", font=("Arial", 40, "bold"), text_color="#00FF00")
        self.result_label.grid(row=2, column=0, padx=20, pady=(0, 20))

        self.start_btn = ctk.CTkButton(self.control_frame, text="자동화 시작", command=self.start_automation, font=("Arial", 15, "bold"), height=40)
        self.start_btn.grid(row=3, column=0, padx=20, pady=10)
        
        self.ocr_model = None

    def start_automation(self):
        self.start_btn.configure(state="disabled", text="실행 중...")
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")
        self.result_label.configure(text="-", text_color="white")
        
        # 백그라운드 스레드에서 실행
        threading.Thread(target=self.run_bot, daemon=True).start()

    def update_image(self, img_bytes):
        # 캡챠 이미지를 UI에 업데이트
        try:
            image = Image.frombytes("RGB", (0, 0), img_bytes) # This is a placeholder, below is correct parsing
            
            nparr = np.frombuffer(img_bytes, np.uint8)
            cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(cv_img)
            
            # ctk.CTkImage 사용
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(200, 80))
            self.img_label.configure(image=ctk_img, text="")
        except Exception as e:
            print(f"이미지 업데이트 오류: {e}")

    def run_bot(self):
        if self.ocr_model is None:
            print("OCR 모델(ddddocr) 로딩 중...")
            self.ocr_model = ddddocr.DdddOcr(old=True, show_ad=False)
            print("모델 로딩 완료.\n")
            
        print("웹 브라우저를 시작합니다...")
        options = webdriver.ChromeOptions()
        # headless=False로 설정하여 웹페이지 동작 과정을 사용자가 직접 볼 수 있게 합니다.
        options.add_argument("--window-size=1024,768")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        max_retries = 10
        success = False
        
        try:
            for attempt in range(1, max_retries + 1):
                print(f"\n[시도 {attempt}/{max_retries}] 법원 페이지 접속 및 캡챠 이미지 스캔 중...")
                driver.get(TARGET_URL)
                wait = WebDriverWait(driver, 10)
                
                captcha_element = wait.until(EC.visibility_of_element_located((By.ID, CAPTCHA_ID)))
                
                # 이미지가 완전히 화면에 그려질 때까지 잠시 대기
                time.sleep(1.5)
                image_base64 = captcha_element.screenshot_as_base64
                image_bytes = base64.b64decode(image_base64)
                
                # UI에 이미지 표시
                self.after(0, self.update_image, image_bytes)
                
                # 크기 2배 전처리
                nparr = np.frombuffer(image_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                resized = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                _, encoded_img = cv2.imencode('.png', resized)
                
                # 텍스트 추출
                extracted_text = self.ocr_model.classification(encoded_img.tobytes())
                numbers_only = re.sub(r'[^0-9]', '', extracted_text)
                
                print(f"-> 추출 결과: {extracted_text} (숫자만: {numbers_only})")
                
                if len(numbers_only) == 6:
                    print("\n==================================================")
                    print(f"🎉 성공! 정확한 6자리 숫자를 찾았습니다: [ {numbers_only} ]")
                    print("==================================================\n")
                    self.result_label.configure(text=numbers_only, text_color="#00FF00")
                    success = True
                    break
                else:
                    self.result_label.configure(text="재시도 중...", text_color="orange")
                    print("⚠️ 6자리가 아니므로 즉시 다른 이미지로 재시도합니다.")
                    
            if not success:
                print("최대 재시도 횟수를 초과했습니다.")
                self.result_label.configure(text="실패", text_color="red")
                
        except Exception as e:
            print(f"오류 발생: {e}")
            self.result_label.configure(text="오류", text_color="red")
        finally:
            print("작업이 종료되었습니다. (브라우저는 5초 후 자동으로 닫힙니다)")
            time.sleep(5)
            driver.quit()
            self.start_btn.configure(state="normal", text="자동화 시작")

if __name__ == "__main__":
    app = CaptchaApp()
    app.mainloop()
