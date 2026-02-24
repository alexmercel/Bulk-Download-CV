# Bulk Download CV

This project contains a Python Selenium script designed to automate the downloading of CV, Bio, and Resume files from the Acado Informatics portal.

## How to Use

1. **Install Dependencies**: Ensure you have Python installed along with `selenium` and `webdriver-manager`.
   ```bash
   pip install selenium webdriver-manager
   ```
2. **Setup Credentials**: Create or update the `config.py` file in the root directory (see section below).
3. **Run the Script**:
   ```bash
   python CV_download.py
   ```
4. The downloaded files will be saved directly to your system's default `~/Downloads` directory.

## Passing Credentials

Credentials are managed securely through a `config.py` file. You must create a `config.py` in the root of the project with the following variables:

```python
USERNAME = "your_username"
PASSWORD = "your_password"
```
The script will import these variables to log in automatically.

## Logging

The project uses a custom `Logger` class that intercepts standard system output (`sys.stdout` and `sys.stderr`). 
- All `print()` statements and errors are dual-routed.
- Output is displayed live in the terminal *and* simultaneously appended to a local `run.log` file.
- This ensures you have a persistent record of the script's execution history without needing complex log configurations.

## Error Handling

- **Element Interaction**: The script wraps clicking components (like the "First Name" header) and table parsing in `try-except` blocks. If an element cannot be found or clicked, a warning is printed and the script attempts to continue.
- **Download Retries**: When attempting to download the parsed CV files using `urllib`, the script uses a retry mechanism. It will attempt the download up to **3 times**, pausing for 2 seconds between failures. 
- If a file completely fails to download after all retries, an error message is logged for that specific individual.
