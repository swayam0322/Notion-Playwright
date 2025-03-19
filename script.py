import os
import asyncio
import time
from playwright.async_api import async_playwright
import random
import string


def _check_for_cookies():
    return os.path.exists("cookies.json")


def _random_email():
    domains = ["example.com", "test.com", "demo.com"]
    username = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = random.choice(domains)
    return f"{username}@{domain}"


async def login(browser):
    email = input("Enter your email: ")

    page = await browser.new_page()
    await page.goto("https://notion.so/login")
    await page.fill('input[id="notion-email-input-1"]', email)
    await page.keyboard.press("Enter")

    await page.wait_for_selector('input[id="notion-password-input-2"]')
    placeholder = await page.get_attribute(
        'input[id="notion-password-input-2"]', "placeholder"
    )

    code = input(f"{placeholder}")
    await page.fill('input[id="notion-password-input-2"]', code)
    await page.keyboard.press("Enter")

    await page.wait_for_selector("div.notion-ai-button")
    await browser.contexts[0].storage_state(path="cookies.json")
    return page


async def invite_members(page, count=1):
    await page.get_by_text("Settings").click()
    await page.get_by_role("tab", name="People").click()

    for _ in range(count):
        await page.get_by_text("Add members", exact= True).click()
        await page.get_by_placeholder("Search names or emails").fill(_random_email())
        await page.keyboard.press(',')
        await page.get_by_role("button", name="Send invite").click()
        await page.wait_for_load_state("networkidle")
        time.sleep(2)

async def main():
    async with async_playwright() as playwright:
        browser = await playwright.firefox.launch(headless=False)
        try:
            if _check_for_cookies():
                context = await browser.new_context(storage_state="cookies.json")
                page = await context.new_page()
                await page.goto("https://notion.so")
                await page.wait_for_selector("div.notion-ai-button")
            else:
                print("No cookies found. Please login.")
                page = await login(browser)
                await page.wait_for_selector("div.notion-ai-button")

        except Exception as e:
            print(e.args)

        finally:
            await browser.contexts[0].storage_state(path="cookies.json")
            await page.screenshot(path="screenshot.png")
            await browser.close()


asyncio.run(main())
