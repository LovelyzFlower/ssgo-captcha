import base64
import time
import ddddocr
import cv2
import numpy as np
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

TARGET_URL = "https://ssgo.scourt.go.kr/ssgo/index.on"
CAPTCHA_ID = "mf_ssgoTopMainTab_contents_content1_body_img_captcha"

def preprocess_for_ocr(image_bytes):
    """
    이미지 크기를 2배로 키워 OCR 엔진의 인식률을 높입니다.
    선 제거 등의 과도한 전처리는 글자까지 훼손시키는 경우가 많아
    ddddocr(old=True) 모델의 자체적인 특징 추출 능력을 믿고 크기만 조절합니다.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    resized = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, encoded_img = cv2.imencode('.png', resized)
    return encoded_img.tobytes(), resized

def solve_captcha():
    print("OCR 모델(ddddocr) 로딩 중...")
    # old=True 옵션: 예전 캡챠 모델이 노이즈 및 두꺼운 선이 있는 환경에서 숫자 인식률이 압도적으로 좋습니다.
    ocr = ddddocr.DdddOcr(old=True, show_ad=False)
    
    print("웹 브라우저를 시작합니다...")
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # 실제 운영 시 주석 해제하여 백그라운드 실행
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    max_retries = 10 # 최대 10회까지 재시도
    
    try:
        for attempt in range(1, max_retries + 1):
            print(f"\n[시도 {attempt}/{max_retries}] 페이지 접속 및 이미지 캡처 중...")
            driver.get(TARGET_URL)
            wait = WebDriverWait(driver, 10)
            
            captcha_element = wait.until(EC.visibility_of_element_located((By.ID, CAPTCHA_ID)))
            
            time.sleep(1.5)
            image_base64 = captcha_element.screenshot_as_base64
            image_bytes = base64.b64decode(image_base64)
            
            # 크기 2배로 전처리
            processed_bytes, processed_img = preprocess_for_ocr(image_bytes)
            
            # 텍스트 추출 및 숫자만 필터링
            extracted_text = ocr.classification(processed_bytes)
            numbers_only = re.sub(r'[^0-9]', '', extracted_text)
            
            print(f"-> 추출 결과: {extracted_text} (숫자만: {numbers_only})")
            
            # 대한민국 법원 전자소송 보안문자는 무조건 '6자리 숫자' 입니다.
            if len(numbers_only) == 6:
                # 성공 시 이미지를 저장하고 종료
                cv2.imwrite("solved_captcha.png", processed_img)
                print("\n==================================================")
                print(f"🎉 성공! 정확한 6자리 숫자를 찾았습니다: [ {numbers_only} ]")
                print("==================================================\n")
                time.sleep(2) # 결과 확인용 대기
                break
            else:
                print("⚠️ 6자리가 아니거나 인식이 불분명합니다. 즉시 페이지를 새로고침하여 다른 이미지로 재시도합니다.")
                
    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        print("작업 완료. 브라우저를 종료합니다.")
        driver.quit()

if __name__ == "__main__":
    solve_captcha()
