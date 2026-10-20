# Notion-Playwright

An async [Playwright](https://playwright.dev/python/) script that automates a Notion workspace. It can:

- **log in once and reuse the session**, so later runs skip the login
- **invite test members** to the workspace through the Settings → People UI
- **export workspace users** (name, email, role, join time) to a JSON file

The UI steps are driven by Playwright. The data export calls the same internal web endpoints the Notion app uses, through the browser context's authenticated `request` client.

## Requirements

- Python 3.10 or newer. This repo does not pin a version. A plain `pip install playwright` currently installs Playwright 1.64.0, which declares `Requires-Python: >=3.10`.
- Chromium for Playwright. If `chromium.launch()` fails, the script runs `playwright install` (every Playwright browser, not only Chromium) and tries the launch once more.

## Setup

```bash
git clone https://github.com/swayam0322/Notion-Playwright.git
cd Notion-Playwright

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install playwright
playwright install chromium
```

`script.py` imports `playwright.async_api`. It does not read environment variables: email and the login code are typed at the prompt, and the only options are the CLI flags below.

## Usage

Both flags are optional. With neither, the script still opens Chromium, logs in or reuses `cookies.json`, and saves storage state on exit. It does not invite anyone or write an export unless you pass the matching flag.

```bash
# Invite N randomly generated test members.
# `--add` with no number invites 1.
python3 script.py --add 3

# Export workspace users.
# `--write` with no filename writes user.json.
python3 script.py --write users.json

# Invites first, then the export
python3 script.py --add 1 --write users.json
```

When `cookies.json` is missing, or the saved session is rejected, the script asks for your Notion email with `Enter your email: `, then for the login code Notion sends you. The code prompt is the `placeholder` of `input#notion-password-input-2`, followed by `: `.

Example output (`--write`). `json.dump` writes this with `indent=4`:

```json
[
    {
        "name": "test",
        "email": "someone@example.com",
        "role": "editor",
        "created_at": 1742277092019
    }
]
```

`created_at` is Notion's `firstJoinedSpaceTime` in epoch milliseconds. A missing name, email, role, or join time is written as `null`.

## How it works

1. **Session reuse.** If `cookies.json` exists, the script opens a new browser context with `storage_state="cookies.json"` and loads `https://notion.so`. It treats the session as valid if `div.notion-ai-button` appears within 10 seconds. If not, it prints `Session expired or invalid. Logging in again...`, closes that context, and logs in again.
2. **Login.** It opens `https://notion.so/login`, fills `input#notion-email-input-1`, presses Enter, and waits up to 10 seconds for `input#notion-password-input-2`. It asks you for the code, fills that input, and presses Enter. It then waits up to 15 seconds for `div.notion-ai-button`. After that button appears it saves the context's storage state (cookies and local storage) to `cookies.json`. A `finally` block saves storage state again on exit whenever a browser context is still open. If the AI button does not appear, the script prints `Login failed: ...`, returns no page, and skips invites and export. A timeout waiting for the code input is not caught.
3. **Workspace ID.** `POST https://www.notion.so/api/v3/getSpaces` with no body. The script uses the first key under `space` on the first object in the response.
4. **Users.** `POST https://www.notion.so/api/v3/getVisibleUsers` with `spaceId` and `supportsEdgeCache: true`. Each returned user supplies `userId`, `role`, and `firstJoinedSpaceTime`.
5. **Metadata.** One batched `POST https://www.notion.so/api/v3/syncRecordValuesSpace`. Each entry is a `notion_user` pointer with `version: -1`. The script reads `recordMap.notion_user` for name and email.
6. **Export.** It merges role, join time, and metadata into one list and writes that list with `json.dump(..., indent=4)`, creating or overwriting the file. Passing `--write` with no filename uses `user.json` (the argparse default). `write_json`'s own default argument is `users.json`, which the CLI does not use unless you pass that name.
7. **Invites (`--add`).** Clicks Settings, the People tab, then Add members. For each invite it waits 1 second, types a 10-character local part at random on `@example.com`, `@test.com`, or `@demo.com`, presses comma and Enter, and clicks Send invite. The comma and Enter are there to dismiss a popup.

Design note: the brief asked for everything to go through Playwright. Since the saved cookies are enough for authentication, the export could use plain `requests` and skip the browser for better performance. This script does not do that. Export goes through Playwright's API request context.

## Files

- `script.py`: all of the logic (login and session reuse, API calls, invites, CLI)
- `cookies.json`: created at runtime. **Contains your session; never commit it.**
- `user.json`: written when you pass `--write` with no filename
- `users.json`: only written if you pass that filename (or call `write_json` without one)

`cookies.json`, `users.json`, `user.json`, and `*.json` are gitignored, so a session file or an export stays out of git. An earlier revision also wrote `screenshot.png`; that file is gitignored too. The current script does not take screenshots.

## Responsible use

- Only run this against workspaces you own or are authorised to administer.
- `/api/v3/*` are undocumented internal Notion endpoints. They can change without notice and may be covered by Notion's terms. For production work, use the official [Notion API](https://developers.notion.com/).
- `--add` sends real invites. Use it only in a test workspace.
- The export contains personal data (names, emails). Store it securely and don't publish it.

## Limitations

- Selectors (`div.notion-ai-button`, `input#notion-email-input-1`, `input#notion-password-input-2`, and the Settings, People, Add members, and Send invite labels, including the placeholder `Search names or emails`) are tied to Notion's current UI and may break.
- Only the first workspace returned by `getSpaces` is used.
- `getSpaces`, `getVisibleUsers`, and `syncRecordValuesSpace` catch errors, print them, and return empty data. The post-login wait for the AI button does the same and skips invites and export. Invite clicks and the wait for the code input are not caught. Nothing is retried, except one second browser launch after `playwright install`.
