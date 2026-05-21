import cv2
import numpy as np
import base64
import time
import ddddocr
from scipy.ndimage import median_filter
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re

TARGET_URL = "https://ssgo.scourt.go.kr/ssgo/index.on"
CAPTCHA_ID = "mf_ssgoTopMainTab_contents_content1_body_img_captcha"

def preprocess_median(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    # 세로 방향으로만 중간값 필터 적용 (가로선 지우기 특효)
    # 가로선 두께보다 큰 사이즈로 필터를 주면, 가로선이 사라지고 주변 배경/글씨로 채워집니다.
    filtered = median_filter(img, size=(5, 1))
    
    # 한 번 더 필터링하여 깔끔하게 만듦
    filtered = median_filter(filtered, size=(3, 1))
    
    # 이진화
    _, thresh = cv2.threshold(filtered, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return thresh

def solve_captcha(ocr, driver):
    try:
        driver.get(TARGET_URL)
        wait = WebDriverWait(driver, 10)
        captcha_element = wait.until(EC.presence_of_element_located((By.ID, CAPTCHA_ID)))
        
        image_base64 = captcha_element.screenshot_as_base64
        image_bytes = base64.b64decode(image_base64)
        
        processed_img = preprocess_median(image_bytes)
        cv2.imwrite("test_median.png", processed_img)
        
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
