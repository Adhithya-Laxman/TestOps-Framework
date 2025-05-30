from selenium.webdriver.remote.webdriver import WebDriver
from typing import Dict

def fill_username(driver: WebDriver, username: str, xpath: str = "//input[@type='text']") -> Dict[str, str]:
    try:
        username_field = driver.find_element("xpath", xpath)
        username_field.clear()
        username_field.send_keys(username)
        return {"status": "success", "message": "Username field filled", "interacted_elements": [xpath]}
    except Exception as e:
        return {"status": "error", "message": str(e), "interacted_elements": []}