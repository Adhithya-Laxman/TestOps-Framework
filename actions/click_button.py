from selenium.webdriver.remote.webdriver import WebDriver
from typing import Dict
import time


def click_button(driver: WebDriver, xpath: str) -> Dict[str, str]:
    try:
        button = driver.find_element("xpath", xpath)
        button.click()
        time.sleep(10)
        return {"status": "success", "message": "Button clicked", "interacted_elements": [xpath]}
    except Exception as e:
        return {"status": "error", "message": str(e), "interacted_elements": []}
