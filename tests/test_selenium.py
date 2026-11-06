
"""
Selenium browser test using a remote Chrome container.
"""
import os
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By


@pytest.mark.selenium
@pytest.mark.skipif(
    os.getenv("RUN_SELENIUM") != "1",
    reason="Set RUN_SELENIUM=1 to run browser tests"
)
def test_homepage_title():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    selenium_url = os.getenv("SELENIUM_REMOTE_URL")

    if selenium_url:
        driver = webdriver.Remote(
            command_executor=selenium_url,
            options=options
        )
    else:
        driver = webdriver.Chrome(options=options)

    try:
        app_url = os.getenv(
            "APP_URL",
            "http://127.0.0.1:5000"
        )

        driver.get(app_url)

        assert "Online Library" in driver.title
        assert driver.find_element(By.TAG_NAME, "h1").is_displayed()

    finally:
        driver.quit()
