from selenium.webdriver.remote.webdriver import WebDriver
from typing import Dict

def fill_password2(driver: WebDriver, password: str, xpath: str = "//input[@type='password']") -> Dict[str, str]:
    try:
        password_field = driver.find_element("xpath", xpath)
        password_field.clear()
        password_field.send_keys(password)
        return {"status": "success", "message": "Password field filled"}
    except Exception as e:
        return {"status": "error", "message": str(e)}