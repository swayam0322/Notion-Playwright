# Notion-Playwright: User Data Extraction and Management

## Requirements 
Make sure you have python3 installed. You can check using 
```bash
python3 --verison
```

## Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/Notion-Playwright.git
    ```

2.  **Navigate to the project directory:**

    ```bash
    cd Notion-Playwright
    ```

3.  **Setup a virtual environment**
    
    ```bash
    python -m venv .venv
    #Activate virtual env 
    source .venv/bin/activate #UNIX-like OS
    .venv/Scripts/activate #Windows
    ```
4. **Intall Playwright and its browsers:**

    ```bash
    pip install pytest-playwright
    playwright install
    ```

4.  **Run the script:**

    ```bash
    python3 script.py (--add | --write)
    ```

    *Script Arguments:*
        The script accepts two arguments:
            - `--add`: Specifies the count of users to add. Defaults to `1`.
            - `--write`: Specifies the filename to write the user data. Defaults to `users.json`.

    ```bash
        python3 script.py --add 5 --write custom_users.json
    ```

## Workflow

1.  **Session Check:**
    * The script checks for the existence and validity of a saved session (cookies).
2.  **Authentication (if needed):**
    * If no valid session is found, the script prompts the user for their Notion email and password.
    * Playwright automates the login process.
3.  **Workspace ID Retrieval:**
    * The script retrieves the workspace ID from the Notion API endpoint: `https://www.notion.so/api/v3/getSpaces`.
4.  **User ID Retrieval:**
    * The script fetches the list of user IDs from the Notion API endpoint: `https://www.notion.so/api/v3/getVisibleUsers`.
5.  **User Metadata Retrieval:**
    * The script retrieves detailed user metadata from the Notion API endpoint: `https://www.notion.so/api/v3/syncRecordValuesSpace`.
6.  **Data Processing:**
    * The retrieved JSON data is parsed and formatted into a structured format.
7.  **Data Export:**
    * The processed user data is written to `users.json`.



## Considerations

1. The assignment asked for implementing the requests through playwright so the python requests was not used else the cached cookies could be used with a requests without rendering a headless browser runtime to  improve performance.

