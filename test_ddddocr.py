import ddddocr
import base64
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re

TARGET_URL = "https://ssgo.scourt.go.kr/ssgo/index.on"
CAPTCHA_ID = "mf_ssgoTopMainTab_contents_content1_body_img_captcha"

def solve_captcha(ocr, driver):
    try:
        driver.get(TARGET_URL)
        wait = WebDriverWait(driver, 10)
        captcha_element = wait.until(EC.presence_of_element_located((By.ID, CAPTCHA_ID)))
        
        image_base64 = captcha_element.screenshot_as_base64
        image_bytes = base64.b64decode(image_base64)
        
        extracted_text = ocr.classification(image_bytes)
        # 숫자만 추출
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
    
    print("10회 테스트 시작...")
    for i in range(10):
        solve_captcha(ocr_old, driver)
        time.sleep(0.5)
    
    driver.quit()
