import cv2
import numpy as np
import easyocr
import base64
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

TARGET_URL = "https://ssgo.scourt.go.kr/ssgo/index.on"
CAPTCHA_ID = "mf_ssgoTopMainTab_contents_content1_body_img_captcha"

def advanced_preprocess(image_bytes):
    # 바이트 데이터를 OpenCV 이미지로 변환
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # 흑백 변환
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 이진화 (배경은 검은색, 글자와 선은 흰색으로)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 가로로 긴 선 찾기 (허프 변환 혹은 컨투어 사용)
    # 여기서는 허프 선 변환을 사용해 봅니다.
    lines = cv2.HoughLinesP(thresh, 1, np.pi/180, threshold=100, minLineLength=50, maxLineGap=10)
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # 각도가 수평에 가까운 선만 지우기 (배경색인 검은색으로 칠함)
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180.0 / np.pi)
            if angle < 20 or angle > 160:
                cv2.line(thresh, (x1, y1), (x2, y2), (0, 0, 0), 3)
                
    # 선을 지운 후 끊어진 숫자 복원 (세로 방향 Closing)
    kernel_vertical = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_vertical)
    
    # 자잘한 노이즈 제거 (Opening)
    kernel_square = np.ones((2, 2), np.uint8)
    opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_square)
    
    # OCR 엔진은 보통 흰 배경에 검은 글씨를 선호하므로 반전
    result = cv2.bitwise_not(opened)
    return result

def test_captcha():
    reader = easyocr.Reader(['en'], gpu=False)
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(TARGET_URL)
        wait = WebDriverWait(driver, 10)
        captcha_element = wait.until(EC.presence_of_element_located((By.ID, CAPTCHA_ID)))
        
        image_base64 = captcha_element.screenshot_as_base64
        image_bytes = base64.b64decode(image_base64)
        
        processed_img = advanced_preprocess(image_bytes)
        cv2.imwrite("test_advanced.png", processed_img)
        
        results = reader.readtext(processed_img, allowlist='0123456789')
        extracted_text = "".join([res[1] for res in results])
        print(f"인식 결과: {extracted_text}")
            
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_captcha()
