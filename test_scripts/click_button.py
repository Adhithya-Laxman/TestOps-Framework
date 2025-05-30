from selenium.webdriver.common.by import By

def click_button(driver, xpath):
    element = driver.find_element(By.XPATH, xpath)
    element.click()
    return {"status": "success", "message": f"Clicked button at xpath: {xpath}"}