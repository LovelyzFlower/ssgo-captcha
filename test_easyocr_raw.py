import easyocr
import base64
import time
import numpy as np
import cv2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re

TARGET_URL = "https://ssgo.scourt.go.kr/ssgo/index.on"
CAPTCHA_ID = "mf_ssgoTopMainTab_contents_content1_body_img_captcha"

def solve_captcha(reader, driver):
    try:
        driver.get(TARGET_URL)
        wait = WebDriverWait(driver, 10)
        captcha_element = wait.until(EC.presence_of_element_located((By.ID, CAPTCHA_ID)))
        
        image_base64 = captcha_element.screenshot_as_base64
        image_bytes = base64.b64decode(image_base64)
        
        # Raw bytes OCR
        results = reader.readtext(image_bytes, allowlist='0123456789')
        extracted_text = "".join([res[1] for res in results])
        numbers_only = re.sub(r'[^0-9]', '', extracted_text)
        print(f"인식 결과 (Raw): {extracted_text} -> {numbers_only} (길이: {len(numbers_only)})")
        
        # Grayscale OCR
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        results2 = reader.readtext(gray, allowlist='0123456789')
        extracted_text2 = "".join([res[1] for res in results2])
        numbers_only2 = re.sub(r'[^0-9]', '', extracted_text2)
        print(f"인식 결과 (Gray): {extracted_text2} -> {numbers_only2} (길이: {len(numbers_only2)})")
            
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    reader = easyocr.Reader(['en'], gpu=False)
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    for i in range(5):
        solve_captcha(reader, driver)
        time.sleep(0.5)
        
    driver.quit()
