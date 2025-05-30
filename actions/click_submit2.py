from selenium.webdriver.common.by import By

from selenium.webdriver.remote.webdriver import WebDriver



def click_submit2(driver : WebDriver, xpath: str):

    try:

        button = driver.find_element(By.XPATH, xpath)

        button.click()

        return {"status": "success", "message": f"Clicked button at xpath: {xpath}", "interacted_elements": [xpath]}

    except Exception as e:

        return {"status": "error", "message": str(e), "interacted_elements": []}