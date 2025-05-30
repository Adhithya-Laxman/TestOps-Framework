from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

def fill_textbox(driver, xpath, text):
    try:
        textbox = driver.find_element("xpath", xpath)
        textbox.clear()
        textbox.send_keys(text + Keys.RETURN)  # or Keys.ENTER
        return {"status": "success", "message": "Text filled and Enter key pressed", "interacted_elements": [xpath]}
    except Exception as e:
        return {"status": "error", "message": str(e), "interacted_elements": []}