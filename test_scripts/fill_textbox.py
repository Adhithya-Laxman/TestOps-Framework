from selenium.webdriver.common.by import By

def fill_textbox(driver, xpath, value):
    element = driver.find_element(By.XPATH, xpath)
    element.send_keys(value)
    return {"status": "success", "message": f"Filled textbox at xpath: {xpath} with value: {value}"}