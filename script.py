import os
import json
import asyncio
import random
import string
import argparse

from playwright.async_api import async_playwright


def check_for_cookies():
    """Check if cookies file exists."""
    return os.path.exists("cookies.json")


def generate_random_email():
    """Generate a random email address for testing."""
    domains = ["example.com", "test.com", "demo.com"]
    username = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = random.choice(domains)
    return f"{username}@{domain}"


async def login(browser):
    """
    Handle the login process and save session cookies.

    Args:
        browser: Playwright browser instance

    Returns:
        Page object with authenticated session
    """
    if check_for_cookies():
        logged_in_context = await browser.new_context(storage_state="cookies.json")
        page = await logged_in_context.new_page()
        await page.goto("https://notion.so")
        try:
            await page.wait_for_selector("div.notion-ai-button", timeout=10000)
            return page
        except Exception:
            print("Session expired or invalid. Logging in again...")
            # Session expired, continue with fresh login
            await logged_in_context.close()

    email = input("Enter your email: ")

    page = await browser.new_page()
    await page.goto("https://notion.so/login")
    await page.fill('input[id="notion-email-input-1"]', email)
    await page.keyboard.press("Enter")

    await page.wait_for_selector('input[id="notion-password-input-2"]', timeout=10000)
    placeholder = await page.get_attribute(
        'input[id="notion-password-input-2"]', "placeholder"
    )

    code = input(f"{placeholder}: ")
    await page.fill('input[id="notion-password-input-2"]', code)
    await page.keyboard.press("Enter")

    try:
        await page.wait_for_selector("div.notion-ai-button", timeout=15000)
        await browser.contexts[0].storage_state(path="cookies.json")
        return page
    except Exception as e:
        print(f"Login failed: {e}")
        return None


def create_request_object(user_id):
    """
    Create request object for fetching user metadata.

    Args:
        user_id: User ID to query

    Returns:
        List formatted payload
    """
    return [
        {
            "pointer": {
                "table": "notion_user",
                "id": f"{user_id}",
            },
            "version": -1,
        }
    ]


async def get_space_id(context):
    """
    Retrieve workspace ID from Notion API.

    Args:
        context: Playwright context with authentication

    Returns:
        Space ID string
    """
    try:
        space_response = await context.request.post(
            "https://www.notion.so/api/v3/getSpaces"
        )

        data = await space_response.json()
        return list(next(iter(data.values()))["space"].keys())[0]
    except Exception as e:
        print("Error fetching space id: ", e)
        return ""


async def get_users(context, space_id):
    """
    Retrieve user list from workspace.

    Args:
        context: Playwright context with authentication
        space_id: Workspace ID

    Returns:
        List of user data
    """
    try:
        resp = await context.request.post(
            "https://www.notion.so/api/v3/getVisibleUsers",
            data={
                "spaceId": space_id,
                "supportsEdgeCache": True,
            },
        )
        data = await resp.json()
        return data.get("users", [])

    except Exception as e:
        print("Error fetching user data: ", e)
        return []


async def get_user_metadata(context, user_data):
    """
    Fetch metadata for a list of users.

    Args:
        context: Playwright context with authentication
        user_data: List of user data dictionaries

    Returns:
        Dictionary containing user metadata
    """
    requests = []
    for user in user_data:
        requests.extend(create_request_object(user["userId"]))

    try:
        resp = await context.request.post(
            "https://www.notion.so/api/v3/syncRecordValuesSpace",
            data={"requests": requests},
        )
        user_meta = await resp.json()
        return user_meta["recordMap"]["notion_user"]
    except Exception as e:
        print("Error fetching user metadata: ", e)
        return {}


async def write_json(page, filename = "users.json"):
    """
    Extract user data and write to JSON file.

    Args:
        page: Authenticated page object
    """
    context = page.context
    space_id = await get_space_id(context)
    user_data = await get_users(context, space_id)
    meta = await get_user_metadata(context, user_data)

    users_list = []  

    for user in user_data:
        user_meta = meta.get(user["userId"], {}).get("value", {})

        user_info = {
            "name": user_meta.get("name", None),
            "email": user_meta.get("email", None),
            "role": user.get("role", None),
            "created_at": user.get("firstJoinedSpaceTime", None),
        }

        users_list.append(user_info)

    # Dump the entire list once
    with open(filename, "w") as f:
        json.dump(users_list, f, indent=4)
    print(f"Generate user data to {filename}")



async def invite_members(page, count=1):
    """
    Invite random members to the workspace.

    Args:
        page: Authenticated page object
        count: Number of members to invite (default: 1)

    """
    await page.get_by_text("Settings").click()
    await page.get_by_role("tab", name="People").click()

    for _ in range(count):
        await page.get_by_text("Add members", exact=True).click()

        random_email = generate_random_email()
        await asyncio.sleep(1)
        await page.get_by_placeholder("Search names or emails").fill(random_email)
        await page.keyboard.press(",")
        await page.keyboard.press("Enter") # Handle 400 popup with this
        await page.get_by_role("button", name="Send invite").click()

    print(f"Invited members to the workspace")

async def main(args):
    """Main entry point for the script."""
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.launch()
        except: 
            os.system("playwright install")
            browser = await playwright.chromium.launch()
        try:
            page = await login(browser)
            if page:  # only run if login was successful
                if args.add:
                    await invite_members(page, count=args.add)
                if args.write:
                    await write_json(page, filename=args.write)

        finally:
            if browser.contexts:
                await browser.contexts[0].storage_state(path="cookies.json")
            await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Notion Automation Script")
    parser.add_argument(
        "--add", type=int, nargs="?", const=1, help="Number of members to invite to the workspace (default: 1)"
    )
    parser.add_argument(
        "--write", type=str, nargs="?", const="user.json", help="Write user data to the specified JSON file (default: user.json)"
    )
    args = parser.parse_args()
    asyncio.run(main(args))