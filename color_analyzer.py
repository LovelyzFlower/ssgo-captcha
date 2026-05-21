import cv2
import numpy as np
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from collections import Counter

TARGET_URL = "https://ssgo.scourt.go.kr/ssgo/index.on"
CAPTCHA_ID = "mf_ssgoTopMainTab_contents_content1_body_img_captcha"

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
    
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Save the original image for reference if needed
    cv2.imwrite("sample_captcha.png", img)
    
    pixels = img.reshape(-1, 3)
    # Convert pixels to tuples of RGB
    pixels_tuple = [tuple(p) for p in pixels]
    counter = Counter(pixels_tuple)
    
    print("Top 10 most common colors (BGR):")
    for color, count in counter.most_common(10):
        print(f"Color: {color}, Count: {count}")

except Exception as e:
    print(f"오류: {e}")
finally:
    driver.quit()
