import os

def malicious(driver):
    os.system("echo Malicious")
    return {"status": "success"}