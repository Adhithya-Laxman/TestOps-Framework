import random
import time
from selenium.webdriver.remote.webdriver import WebDriver

from typing import Dict



def add_rand_ele(driver: WebDriver, grid_xpath: str = "//input[@type='text']") -> Dict[str, str]:

    try:

        child_xpath = grid_xpath.rstrip("/") + "/div"

        child_divs = driver.find_elements("xpath", child_xpath)

        if not child_divs:

            return {"status": "error", "message": "No child divs found"}



        random_index = random.randint(0, len(child_divs) - 1)

        selected_div = child_divs[random_index]



        selected_div.click()


        return {"status": "success", "message": f"Clicked div at index {{random_index + 1}} out of {{len(child_divs)}}", "interacted_elements": [child_xpath + f"[{random_index + 1}]"]}
    except Exception as e:
        return {"status": "error", "message": str(e), "interacted_elements": []}

