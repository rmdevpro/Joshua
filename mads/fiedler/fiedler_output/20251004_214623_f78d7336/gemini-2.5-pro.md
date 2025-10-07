Of course. Here is a simple, production-ready Python web scraper module that includes all the requested components.

This module is self-contained in a single file (`simple_scraper.py`) and demonstrates best practices like using a `requests.Session`, handling exceptions gracefully, and providing clear documentation.

---

### `simple_scraper.py`

```python
# simple_scraper.py
#
# A simple, production-ready web scraper module.
#
# Dependencies:
# pip install requests beautifulsoup4

import csv
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# --- Setup logging ---
# It's better to configure logging in the application that uses the module,
# but for a self-contained example, we'll configure it here.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Constants ---
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)


class WebScraper:
    """
    A simple web scraper with retry logic, rate limiting, and session management.

    This class handles the complexities of making robust HTTP requests,
    allowing the user to focus on parsing the retrieved HTML.

    Attributes:
        session (requests.Session): The session object used for making requests.
        rate_limit_seconds (float): The delay to wait between successful requests.
    """

    def __init__(
        self,
        rate_limit_seconds: float = 1.0,
        retries: int = 3,
        backoff_factor: float = 0.5,
        status_forcelist: tuple = (500, 502, 503, 504),
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Initializes the WebScraper.

        Args:
            rate_limit_seconds (float): Seconds to wait between each request to be polite.
            retries (int): The number of times to retry a failed request.
            backoff_factor (float): A backoff factor to apply between attempts after the second try.
                                  e.g., {backoff factor} * (2 ** ({number of total retries} - 1))
            status_forcelist (tuple): A set of HTTP status codes that we should force a retry on.
            headers (Optional[Dict[str, str]]): Custom headers to use for requests.
                                                A default User-Agent is provided if None.
        """
        self.rate_limit_seconds = rate_limit_seconds
        self._last_request_time = 0.0

        # --- Setup retry logic ---
        retry_strategy = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)

        # --- Setup session ---
        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # --- Set headers ---
        if headers:
            self.session.headers.update(headers)
        else:
            self.session.headers.update({"User-Agent": DEFAULT_USER_AGENT})

    def fetch_page(self, url: str, timeout: int = 15) -> Optional[BeautifulSoup]:
        """
        Fetches a single URL and returns its content as a BeautifulSoup object.

        This method incorporates the rate limiting delay before making a request.

        Args:
            url (str): The URL to fetch.
            timeout (int): The request timeout in seconds.

        Returns:
            Optional[BeautifulSoup]: A BeautifulSoup object if the request is successful,
                                     otherwise None.
        """
        # --- Apply rate limiting ---
        elapsed_time = time.monotonic() - self._last_request_time
        if elapsed_time < self.rate_limit_seconds:
            sleep_time = self.rate_limit_seconds - elapsed_time
            logging.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds.")
            time.sleep(sleep_time)

        self._last_request_time = time.monotonic()
        
        logging.info(f"Fetching URL: {url}")
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            # --- Parse HTML ---
            soup = BeautifulSoup(response.text, "lxml") # lxml is generally faster
            return soup

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch {url} after all retries. Error: {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred while fetching {url}: {e}")
            return None


def save_to_json(data: List[Dict[str, Any]], filename: str, output_dir: Path) -> None:
    """
    Saves a list of dictionaries to a JSON file.

    Args:
        data (List[Dict[str, Any]]): The data to save.
        filename (str): The name of the output file (e.g., 'data.json').
        output_dir (Path): The directory to save the file in.
    """
    if not data:
        logging.warning("No data provided to save_to_json. Skipping file creation.")
        return

    filepath = output_dir / filename
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Successfully saved {len(data)} records to {filepath}")
    except IOError as e:
        logging.error(f"Error writing to JSON file {filepath}: {e}")


def save_to_csv(data: List[Dict[str, Any]], filename: str, output_dir: Path) -> None:
    """
    Saves a list of dictionaries to a CSV file.

    Args:
        data (List[Dict[str, Any]]): The data to save.
        filename (str): The name of the output file (e.g., 'data.csv').
        output_dir (Path): The directory to save the file in.
    """
    if not data:
        logging.warning("No data provided to save_to_csv. Skipping file creation.")
        return

    filepath = output_dir / filename
    # Use the keys from the first dictionary as the header
    headers = data[0].keys()

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)
        logging.info(f"Successfully saved {len(data)} records to {filepath}")
    except IOError as e:
        logging.error(f"Error writing to CSV file {filepath}: {e}")


def main():
    """
    Example usage of the WebScraper module.

    This function demonstrates how to:
    1. Instantiate the scraper.
    2. Fetch a web page.
    3. Parse the HTML to extract data.
    4. Save the extracted data to CSV and JSON formats.
    """
    # --- 1. Setup ---
    # A website designed for scraping practice
    target_url = "http://quotes.toscrape.com/"
    output_directory = Path("output")
    output_directory.mkdir(exist_ok=True) # Create output directory if it doesn't exist

    # --- 2. Initialize the scraper ---
    # Be polite: wait 2 seconds between requests
    scraper = WebScraper(rate_limit_seconds=2)

    # --- 3. Fetch the page ---
    soup = scraper.fetch_page(target_url)

    if not soup:
        logging.error("Could not retrieve the webpage. Exiting.")
        return

    # --- 4. Parse the data ---
    quotes_data = []
    quotes = soup.find_all('div', class_='quote')

    if not quotes:
        logging.warning("No quotes found on the page.")
        return

    logging.info(f"Found {len(quotes)} quotes on the page.")

    for quote in quotes:
        text_element = quote.find('span', class_='text')
        author_element = quote.find('small', class_='author')
        tags_elements = quote.find_all('a', class_='tag')

        # Gracefully handle missing elements
        text = text_element.get_text(strip=True) if text_element else "N/A"
        author = author_element.get_text(strip=True) if author_element else "N/A"
        tags = [tag.get_text(strip=True) for tag in tags_elements]

        quotes_data.append({
            'text': text,
            'author': author,
            'tags': ', '.join(tags) # Join tags for easier CSV display
        })

    # --- 5. Export the data ---
    if quotes_data:
        save_to_json(quotes_data, "quotes.json", output_directory)
        save_to_csv(quotes_data, "quotes.csv", output_directory)
    else:
        logging.info("No data was scraped to save.")


if __name__ == "__main__":
    # To run this example, ensure you have the required packages:
    # pip install requests beautifulsoup4 lxml
    main()
```

### How to Run the Example

1.  **Save the code:** Save the code above as a Python file named `simple_scraper.py`.
2.  **Install dependencies:** Open your terminal or command prompt and install the necessary libraries. `lxml` is recommended for its speed, though `html.parser` (built-in) also works.
    ```bash
    pip install requests beautifulsoup4 lxml
    ```
3.  **Execute the script:**
    ```bash
    python simple_scraper.py
    ```

### Output

After running the script, you will see log messages in your terminal:

```
2023-10-27 11:30:00,123 - INFO - Fetching URL: http://quotes.toscrape.com/
2023-10-27 11:30:01,456 - INFO - Found 10 quotes on the page.
2023-10-27 11:30:01,457 - INFO - Successfully saved 10 records to output/quotes.json
2023-10-27 11:30:01,458 - INFO - Successfully saved 10 records to output/quotes.csv
```

A new directory named `output` will be created in the same location as your script, containing two files:

1.  **`quotes.json`**: A JSON file with the scraped data.
2.  **`quotes.csv`**: A CSV file with the same data, formatted for spreadsheets.
