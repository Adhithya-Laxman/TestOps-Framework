# from selenium.webdriver.remote.webdriver import WebDriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from urllib.parse import urlparse, parse_qs
# from typing import Dict
# import time

# def test_links_in_div(driver: WebDriver, div_xpath: str = "//div[contains(@class, 'flex items-center justify-between mt-4')]") -> Dict[str, str]:
#     """
#     Tests all links within a specified div by clicking each one and verifying the resulting URL.

#     Args:
#         driver: Selenium WebDriver instance
#         div_xpath: XPath for the div containing the links (default provided)

#     Returns:
#         Dict[str, str]: Status and message indicating if all links worked or which ones failed
#     """
#     try:
#         # Locate the div using the provided XPath
#         child_xpath = div_xpath.rstrip("/") + "/a"
#         child_links = driver.find_elements("xpath", child_xpath)

#         for link in child_links:
#             href = link.get_attribute("href")
#             driver.execute_script(f"window.open('{href}', '_blank');")
#             time.sleep(1.5)  # Wait for the new tab to open


#     except Exception as e:
#         return {"status": "error", "message": str(e)}


from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict
import time

def get_xpath(driver, element):
    """Generate an XPath for a given element."""
    return driver.execute_script(
        "function getPathTo(element) {"
        "    if (element.id!=='') return 'id(\"'+element.id+'\")';"
        "    if (element===document.body) return element.tagName;"
        "    var ix= 0;"
        "    var siblings= element.parentNode.childNodes;"
        "    for (var i= 0; i<siblings.length; i++) {"
        "        var sibling= siblings[i];"
        "        if (sibling===element) return getPathTo(element.parentNode)+'/'+element.tagName+'['+(ix+1)+']';"
        "        if (sibling.nodeType===1 && sibling.tagName===element.tagName) ix++;"
        "    }"
        "}"
        "return getPathTo(arguments[0]);", element)

def test_links_in_div(driver: WebDriver, div_xpath: str = "//div[contains(@class, 'flex items-center justify-between mt-4')]") -> Dict[str, any]:
    """
    Tests all links within a specified div by opening each in a new tab and verifying the resulting URL.

    Args:
        driver: Selenium WebDriver instance
        div_xpath: XPath for the div containing the links (default provided)

    Returns:
        Dict[str, any]: Status, message, list of interacted elements (XPaths), and detailed results for each link
    """
    try:
        # Locate the div using the provided XPath
        div = driver.find_element(By.XPATH, div_xpath)
        child_links = div.find_elements(By.TAG_NAME, "a")
        
        original_window = driver.current_window_handle
        tested_elements = []
        results = []
        
        for link in child_links:
            href = link.get_attribute("href")
            if not href:
                continue
            link_xpath = get_xpath(driver, link)
            tested_elements.append(link_xpath)
            
            # Open the link in a new tab
            driver.execute_script(f"window.open('{href}', '_blank');")
            time.sleep(1)  # Brief wait for the new tab to open
            
            # Switch to the new tab
            new_window = [window for window in driver.window_handles if window != original_window][0]
            driver.switch_to.window(new_window)
            
            # Wait for the page to load and verify it
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                current_url = driver.current_url
                # Check if the page loaded successfully by comparing URLs
                if current_url == href or current_url.startswith(href.rstrip("/")):
                    status = "passed"
                    details = "Page loaded successfully, URL matches href"
                else:
                    status = "failed"
                    details = f"URL mismatch: expected {href}, got {current_url}"
            except Exception as e:
                status = "failed"
                details = f"Page failed to load: {str(e)}"
            
            results.append({"href": href, "status": status, "details": details})
            
            # Close the new tab and switch back to the original window
            driver.close()
            driver.switch_to.window(original_window)
        print(tested_elements)
        # Return the summary with interacted elements and results
        return {
            "status": "success",
            "message": "All links tested",
            "interacted_elements": tested_elements,
            "results": results
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Script failed: {str(e)}", "interacted_elements": []}