import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import requests
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
import csv
import os
import tkinterdnd2

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

def bfs_scrape_links(seed_url, max_levels, save_folder):
    seed_domain = urlparse(seed_url).netloc
    visited = set()
    queue = [(seed_url, 0)]

    links = set()

    while queue:
        current_url, current_level = queue.pop(0)

        if current_level > max_levels:
            break

        if current_url not in visited and is_same_domain(current_url, seed_domain):
            print(f"Scraping level {current_level}: {current_url}")
            visited.add(current_url)

            try:
                response = requests.get(current_url)
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract links
                page_links = set(urljoin(current_url, link['href']) for link in soup.find_all('a', href=True))
                links.update(page_links)

                # Enqueue next level links
                queue.extend((link, current_level + 1) for link in page_links)

            except Exception as e:
                print(f"Error scraping {current_url}: {e}")

    return list(links)

def generate_file_name(seed_url, save_folder):
    second_level_domain = get_second_level_domain(seed_url)
    base_name = os.path.join(save_folder, second_level_domain)
    count = 1

    while os.path.exists(f"{base_name}_{count}.csv"):
        count += 1

    return f"{base_name}_{count}.csv"

def on_submit():
    main_link = entry_main_link.get()
    levels = int(combobox_levels.get())
    destination_folder = filedialog.askdirectory()

    links = bfs_scrape_links(main_link, levels, destination_folder)

    file_name = generate_file_name(main_link, destination_folder)
    csv_path = os.path.join(destination_folder, file_name)

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
    unique_links = [link for link in links if link not in existing_links]

    # Append new links to the CSV file
    with open(csv_path, 'a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerows([[link] for link in unique_links])

    status_label.config(text=f"Unique links saved to {csv_path}")


def set_main_link_from_clipboard():
    clipboard_content = window.clipboard_get()
    if clipboard_content.startswith("http"):
        entry_main_link.delete(0, tk.END)
        entry_main_link.insert(0, clipboard_content)

# Create GUI window
window = tk.Tk()
window.title("Web Link Hierarchy Scraper to CSV")

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
combobox_levels.set(3)  # Default value

# Destination folder button
button_browse = ttk.Button(window, text="Browse", command=on_submit)
button_browse.grid(row=2, column=0, columnspan=2, pady=10)

# Status label
status_label = ttk.Label(window, text="")
status_label.grid(row=3, column=0, columnspan=2)

# Clipboard button
button_clipboard = ttk.Button(window, text="Set from Clipboard", command=set_main_link_from_clipboard)
button_clipboard.grid(row=4, column=0, columnspan=2, pady=10)

# Start GUI loop
window.mainloop()
