import cv2
import numpy as np
import base64
import time
import ddddocr
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re

TARGET_URL = "https://ssgo.scourt.go.kr/ssgo/index.on"
CAPTCHA_ID = "mf_ssgoTopMainTab_contents_content1_body_img_captcha"

def color_preprocess(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # 흑백이 아닌 특정 색상(예: 0,0,0 완전 검은색)만 남기고 다 흰색으로 만들기
    # img에서 값이 30 이하인 픽셀만 검은색으로 남기고, 나머지는 흰색으로
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 임계값을 30으로 주어 어두운 선(64,64,64 등)은 모두 흰색(255)이 되도록 함
    _, thresh = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY)
    
    # 추가로 노이즈가 있다면 가벼운 Opening 적용
    kernel = np.ones((2, 2), np.uint8)
    opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    return opened

def solve_captcha(ocr, driver):
    try:
        driver.get(TARGET_URL)
        wait = WebDriverWait(driver, 10)
        captcha_element = wait.until(EC.presence_of_element_located((By.ID, CAPTCHA_ID)))
        
        image_base64 = captcha_element.screenshot_as_base64
        image_bytes = base64.b64decode(image_base64)
        
        processed_img = color_preprocess(image_bytes)
        cv2.imwrite("test_color_thresh.png", processed_img)
        
        # ddddocr을 위해 다시 바이트로 변환
        _, encoded_img = cv2.imencode('.png', processed_img)
        
        extracted_text = ocr.classification(encoded_img.tobytes())
        numbers_only = re.sub(r'[^0-9]', '', extracted_text)
        print(f"인식 결과 (원본): {extracted_text} -> (숫자 필터): {numbers_only} (길이: {len(numbers_only)})")
            
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    ocr_old = ddddocr.DdddOcr(old=True, show_ad=False)
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    for i in range(5):
        solve_captcha(ocr_old, driver)
        time.sleep(0.5)
        
    driver.quit()
