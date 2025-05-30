from selenium.webdriver.common.by import By

def fill_textbox(driver, xpath: str, value: str):
    try:
        textbox = driver.find_element(By.XPATH, xpath)
        textbox.clear()
        textbox.send_keys(value)
        return {"status": "success", "message": f"Filled textbox at xpath: {xpath} with value: {value}", "interacted_elements": [xpath]}
    except Exception as e:
        return {"status": "error", "message": str(e), "interacted_elements": []}