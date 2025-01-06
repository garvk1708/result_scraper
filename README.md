# Roll Number Result Scraper

This Python script is designed to fetch student results from NITH's online result portal based on roll numbers.
The results are parsed and saved in a structured JSON format. The script also allows the generation of roll numbers for different departments and years.

## Features
- Generate roll numbers based on the year and department codes.
- Scrape student results from the official university results portal.
- Parse student information such as name, father’s name, subjects, grades, SGPI, and CGPI.
- Save scraped data into JSON files and CSV format for easy access.
- Customizable input for years and departments.
- Built-in retry logic and random delay between requests for better reliability and to avoid overloading the server.
- Use of proxy rotation (via a proxy API) and random user-agents to simulate real users.

## Requirements

- Python 3.x
- Libraries:
  - `requests`
  - `beautifulsoup4`
  - `fake_useragent`
  - `urllib3`
  
You can install the required libraries using the following command:

```bash
pip install requests beautifulsoup4 fake_useragent urllib3

##Disclaimer
This script is intended for educational purposes only. It should not be used for malicious activities, scraping sensitive data, or violating any terms of service of websites. Always ensure that you have permission to scrape and interact with websites you target.
