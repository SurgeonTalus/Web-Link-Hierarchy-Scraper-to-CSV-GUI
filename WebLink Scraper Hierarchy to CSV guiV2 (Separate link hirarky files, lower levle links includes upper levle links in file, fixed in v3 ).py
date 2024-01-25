import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import csv
import os

def is_same_domain(url, seed_domain):
    parsed_url = urlparse(url)
    return parsed_url.netloc == seed_domain

def get_second_level_domain(url):
    parsed_url = urlparse(url)
    domain_parts = parsed_url.netloc.split('.')
    if len(domain_parts) >= 2:
        return f"{domain_parts[-2]}.{domain_parts[-1]}"
    else:
        return parsed_url.netloc

def bfs_scrape_links(seed_url, max_levels, save_folder, stay_on_domain=True, separate_levels=True):
    seed_domain = urlparse(seed_url).netloc
    visited = set()
    queue = [(seed_url, 0)]

    # Dictionary to store unique links for each level
    level_links_dict = {level: set() for level in range(max_levels + 1)}

    while queue:
        current_url, current_level = queue.pop(0)

        if current_level > max_levels:
            break

        if current_url not in visited:
            visited.add(current_url)

            try:
                response = requests.get(current_url)
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract links
                page_links = set(urljoin(current_url, link['href']) for link in soup.find_all('a', href=True))

                if stay_on_domain:
                    page_links = [link for link in page_links if is_same_domain(link, seed_domain)]

                level_links_dict[current_level].update(page_links)
                # Print each fetched link in the terminal
                for link in page_links:
                    print(f"Fetched link at level {current_level}: {link}")
    
                # Enqueue next level links
                queue.extend((link, current_level + 1) for link in page_links)

            except Exception as e:
                print(f"Error scraping {current_url}: {e}")

    if separate_levels:
        for level in range(max_levels + 1):
            # Skip lower-level links when creating CSV files for higher levels
            higher_level_links = set(link for l in range(level + 1) for link in level_links_dict[l])

            file_name = generate_file_name(seed_url, save_folder, level)
            csv_path = os.path.join(save_folder, file_name)

            existing_links = set()
            try:
                # Read existing links from the CSV file
                with open(csv_path, 'r') as csv_file:
                    csv_reader = csv.reader(csv_file)
                    next(csv_reader)  # Skip header row
                    existing_links = set(row[0] for row in csv_reader)
            except FileNotFoundError:
                pass

            # Filter out duplicates
            unique_links = [link for link in higher_level_links if link not in existing_links]

            # Append new links to the CSV file
            with open(csv_path, 'a', newline='') as csv_file:
                csv_writer = csv.writer(csv_file)
                if not existing_links:  # Write header if the file is empty
                    csv_writer.writerow(['Link'])
                csv_writer.writerows([[link] for link in unique_links])

    else:
        # For non-separated levels, create a single CSV file for the highest level
        highest_level = max_levels
        highest_level_links = level_links_dict[highest_level]

        file_name = generate_file_name(seed_url, save_folder, highest_level)
        csv_path = os.path.join(save_folder, file_name)

        existing_links = set()
        try:
            # Read existing links from the CSV file
            with open(csv_path, 'r') as csv_file:
                csv_reader = csv.reader(csv_file)
                next(csv_reader)  # Skip header row
                existing_links = set(row[0] for row in csv_reader)
        except FileNotFoundError:
            pass

        # Filter out duplicates
        unique_links = [link for link in highest_level_links if link not in existing_links]

        # Append new links to the CSV file
        with open(csv_path, 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            if not existing_links:  # Write header if the file is empty
                csv_writer.writerow(['Link'])
            csv_writer.writerows([[link] for link in unique_links])

    return level_links_dict

def generate_file_name(seed_url, save_folder, level):
    second_level_domain = get_second_level_domain(seed_url)
    base_name = os.path.join(save_folder, f"{second_level_domain}_Level_{level}")
    count = 1

    while os.path.exists(f"{base_name}_{count}.csv"):
        count += 1

    return f"{base_name}_{count}.csv"

def on_submit():
    global last_selected_folder
    main_link = entry_main_link.get()
    levels = int(combobox_levels.get())
    destination_folder = filedialog.askdirectory()
    stay_on_domain = check_stay_on_domain.get()
    separate_levels = check_separate_levels.get()

    links = bfs_scrape_links(main_link, levels, destination_folder, stay_on_domain, separate_levels)

    for level_links in links.values():
        for link_level, level_links in level_links.items():
            existing_links = set()
            try:
                # Read existing links from the CSV file
                with open(level_links['csv_path'], 'r') as csv_file:
                    csv_reader = csv.reader(csv_file)
                    next(csv_reader)  # Skip header row
                    existing_links = set(row[0] for row in csv_reader)
            except FileNotFoundError:
                pass

            # Filter out duplicates
            unique_links = [link for link in level_links if link not in existing_links]

            # Append new links to the CSV file
            with open(level_links['csv_path'], 'a', newline='') as csv_file:
                csv_writer = csv.writer(csv_file)
                if not existing_links:  # Write header if the file is empty
                    csv_writer.writerow(['Link'])
                csv_writer.writerows([[link] for link in unique_links])

            last_selected_folder = destination_folder  # Update last selected folder
            status_label.config(text=f"Unique links saved to {level_links['csv_path']}")

def set_main_link_from_clipboard():
    clipboard_content = window.clipboard_get()
    if clipboard_content.startswith("http"):
        entry_main_link.delete(0, tk.END)
        entry_main_link.insert(0, clipboard_content)

def process_next():
    global last_selected_folder
    main_link = entry_main_link.get()
    levels = int(combobox_levels.get())
    stay_on_domain = check_stay_on_domain.get()
    separate_levels = check_separate_levels.get()

    if last_selected_folder:
        links = bfs_scrape_links(main_link, levels, last_selected_folder, stay_on_domain, separate_levels)

        for level_links in links.values():
            for link_level, level_links in level_links.items():
                existing_links = set()
                try:
                    # Read existing links from the CSV file
                    with open(level_links['csv_path'], 'r') as csv_file:
                        csv_reader = csv.reader(csv_file)
                        next(csv_reader)  # Skip header row
                        existing_links = set(row[0] for row in csv_reader)
                except FileNotFoundError:
                    pass

                # Filter out duplicates
                unique_links = [link for link in level_links if link not in existing_links]

                # Append new links to the CSV file
                with open(level_links['csv_path'], 'a', newline='') as csv_file:
                    csv_writer = csv.writer(csv_file)
                    if not existing_links:  # Write header if the file is empty
                        csv_writer.writerow(['Link'])
                    csv_writer.writerows([[link] for link in unique_links])

                status_label.config(text=f"Unique links saved to {level_links['csv_path']}")
    else:
        status_label.config(text="Please select a folder using the 'Browse' button first.")

# Create GUI window
window = tk.Tk()
window.title("Web Link Scraper")

# Main link entry
label_main_link = ttk.Label(window, text="Main Link:")
label_main_link.grid(row=0, column=0, padx=5, pady=5)
entry_main_link = ttk.Entry(window, width=40)
entry_main_link.grid(row=0, column=1, padx=5, pady=5)

# Set default value from clipboard if a link is present
set_main_link_from_clipboard()

# Levels combobox
label_levels = ttk.Label(window, text="Levels:")
label_levels.grid(row=1, column=0, padx=5, pady=5)
combobox_levels = ttk.Combobox(window, values=[1, 2, 3, 4, 5], state="readonly")
combobox_levels.grid(row=1, column=1, padx=5, pady=5)
combobox_levels.set(1)  # Set level 1 as the default value

# Checkbox to stay on the server domain
check_stay_on_domain = tk.BooleanVar()
check_stay_on_domain.set(True)  # Default value (checked)
checkbox_stay_on_domain = ttk.Checkbutton(window, text="Stay on Server Domain", variable=check_stay_on_domain)
checkbox_stay_on_domain.grid(row=2, column=0, columnspan=2, pady=5)

# Checkbox for separating levels
check_separate_levels = tk.BooleanVar()
check_separate_levels.set(True)  # Default value (checked)
checkbox_separate_levels = ttk.Checkbutton(window, text="Separate Levels", variable=check_separate_levels)
checkbox_separate_levels.grid(row=3, column=0, columnspan=2, pady=5)

# Destination folder button
button_browse = ttk.Button(window, text="Browse", command=on_submit)
button_browse.grid(row=4, column=0, columnspan=2, pady=10)

# Process Next button
button_process_next = ttk.Button(window, text="Process Next", command=process_next)
button_process_next.grid(row=5, column=0, columnspan=2, pady=10)

# Status label
status_label = ttk.Label(window, text="")
status_label.grid(row=6, column=0, columnspan=2)

# Clipboard button
button_clipboard = ttk.Button(window, text="Set from Clipboard", command=set_main_link_from_clipboard)
button_clipboard.grid(row=7, column=0, columnspan=2, pady=10)

# Last selected folder variable
last_selected_folder = None

# Start GUI loop
window.mainloop()
