"""NITH Result Scraper - A tool to fetch and process student results."""

import csv
import json
import random
import time

import requests
from bs4 import BeautifulSoup
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

def generate_roll_numbers(year, department_code):
    """Generate roll numbers for a specific year and department."""
    return [f'"{year}{department_code}{i:03d}"' for i in range(1, 151)]

all_departments = [
    'BEC', 'BCS', 'DCS', 'DEC', 'BPH', 'BME', 'BCH', 'BMA', 'BMS', 'BCE', 'BEE', 'BAR'
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/89.0.4389.82",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:85.0) Firefox/85.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/91.0.864.54",
]

def create_session():
    """Create a session with retry mechanism."""
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def fetch_results(roll_number):
    """Fetch result page HTML for a roll number."""
    session = create_session()
    year = roll_number[:2]
    base_url = f"http://results.nith.ac.in/scheme{year}/studentresult/"
    submit_url = f"{base_url}result.asp"

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/html,application/xhtml+xml",
        "Referer": base_url
    }

    try:
        response = session.post(
            submit_url, 
            data={"RollNumber": roll_number, "x_vSemID": "1"},
            headers=headers,
            timeout=15
        )
        return response.text if response.status_code == 200 else None
    except requests.RequestException as err:
        print(f"Error fetching results for {roll_number}: {err}")
        return None

# Parse result HTML and extract student data
def parse_results(html_content):
    if not html_content:
        print("Empty response received")
        return None
        
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table")
    
    if not tables or len(tables) < 2:
        print("Invalid response structure")
        return None

    try:
        # Get student info
        info_table = tables[1]
        student_info = {
            "roll_number": info_table.find("p", string=lambda x: "ROLL NUMBER" in str(x)).find_next("p").text.strip(),
            "student_name": info_table.find("p", string=lambda x: "STUDENT NAME" in str(x)).find_next("p").text.strip(),
            "father_name": info_table.find("p", string=lambda x: "FATHER NAME" in str(x)).find_next("p").text.strip()
        }
    except Exception as e:
        print(f"Error parsing student info: {e}")
        return None

    semesters = []
    current_sem = None

    for table in tables[2:]:
        try:
            # Process semester header
            sem_header = table.find("tr", class_="info")
            if sem_header:
                if current_sem:
                    semesters.append(current_sem)
                current_sem = {
                    "semester": sem_header.text.strip().split(":")[-1].strip(),
                    "subjects": [],
                    "summary": {}
                }

            # Process subject table
            if table.find("tr", class_="thcolor"):
                rows = table.find_all("tr")[1:]
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) >= 6:
                        subject = {
                            "sno": cells[0].text.strip(),
                            "subject_name": cells[1].text.strip(),
                            "subject_code": cells[2].text.strip(),
                            "credits": cells[3].text.strip(),
                            "grade": cells[4].text.strip(),
                            "grade_points": cells[5].text.strip()
                        }
                        if current_sem:
                            current_sem["subjects"].append(subject)

            # Process summary
            if "background-color: #d99900" in str(table):
                cells = table.find_all("td")
                if len(cells) >= 5 and current_sem:
                    current_sem["summary"] = {
                        "sgpi": cells[1].find_all("p")[1].text.strip(),
                        "sgpi_total": cells[2].find_all("p")[1].text.strip(),
                        "cgpi": cells[3].find_all("p")[1].text.strip(),
                        "cgpi_total": cells[4].find_all("p")[1].text.strip()
                    }
        except Exception as e:
            print(f"Error processing table: {e}")
            continue

    if current_sem:
        semesters.append(current_sem)

    result = {**student_info, "semesters": semesters}
    return result if semesters else None

# Save results to a JSON file
def save_results(results, filename="results.json"):
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

# Generate roll numbers and scrape results
def generate_roll_numbers_and_scrape():
    year_input = input("Enter the year (21/22/23/24): ").strip()
    if year_input not in ['21', '22', '23', '24']:
        print("Invalid year.")
        return

    department_input = input("Enter department codes or 'all' for all: ").upper()
    roll_numbers_all = []

    if department_input == 'ALL':
        for department_code in all_departments:
            roll_numbers_all.extend(generate_roll_numbers(year_input, department_code))
    else:
        for department_code in department_input.split(','):
            roll_numbers_all.extend(generate_roll_numbers(year_input, department_code.strip()))

    results = []
    for roll in roll_numbers_all:
        print(f"Fetching {roll}...")
        html = fetch_results(roll.strip('"'))
        if html:
            data = parse_results(html)
            results.append(data)
        time.sleep(1)

    save_results(results)

    with open('roll_numbers.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(roll_numbers_all)

    print("Saved roll numbers and results.")

# Process all batches based on user choice
def process_all_batches():
    print("\n=== NITH Result Scraper ===")
    print("\n1. Single student")
    print("2. Full batch")
    print("3. Full year")
    print("4. All years")
    
    choice = input("\n👉 Select mode (1-4): ").strip()
    
    if choice == '1':
        process_single_student()
    else:
        years = ['21', '22', '23', '24']
        print("Options:\n1. All years, all departments\n2. Specific year, all departments\n3. Specific year, specific department")
        choice = input("Enter choice (1-3): ").strip()

        if choice == '1':
            for year in years:
                for dept in all_departments:
                    process_batch(generate_roll_numbers(year, dept), f"{year}{dept}")
        elif choice == '2':
            year = input("Enter year (21/22/23/24): ").strip()
            if year in years:
                for dept in all_departments:
                    process_batch(generate_roll_numbers(year, dept), f"{year}{dept}")
        elif choice == '3':
            year = input("Enter year (21/22/23/24): ").strip()
            dept = input("Enter department code: ").strip().upper()
            if year in years and dept in all_departments:
                process_batch(generate_roll_numbers(year, dept), f"{year}{dept}")
        else:
            print("Invalid choice")

# Process a batch of roll numbers
def process_batch(roll_numbers, batch_id):
    results = []
    total = len(roll_numbers)
    for i, roll_no in enumerate(roll_numbers, 1):
        print(f"Processing {i}/{total}: {roll_no}")
        html = fetch_results(roll_no.strip('"'))
        if html:
            results.append(parse_results(html))
        time.sleep(random.uniform(1, 3))

    with open(f'results_{batch_id}.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved results for batch {batch_id}")

def process_single_student():
    roll_no = input("\nEnter roll number (e.g. 21BEC001): ").strip().upper()
    
    if not validate_roll_number(roll_no):
        print("❌ Invalid roll number format")
        return
        
    print(f"\n🔄 Fetching results for {roll_no}")
    html = fetch_results(roll_no)
    
    if html:
        result = parse_results(html)
        if result:
            filename = f'{roll_no}_result.json'
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"✅ Results saved to {filename}")
        else:
            print("❌ No results found")
    else:
        print("❌ Failed to fetch results")

def validate_roll_number(roll_no):
    if len(roll_no) != 8:
        return False
    year = roll_no[:2]
    dept = roll_no[2:5]
    number = roll_no[5:]
    return (year in ['21','22','23','24'] and 
            dept in all_departments and 
            number.isdigit() and 
            1 <= int(number) <= 150)

# Main entry point
def main():
    process_all_batches()

if __name__ == "__main__":
    main()
