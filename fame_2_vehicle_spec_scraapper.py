import json

import requests
import os
from bs4 import BeautifulSoup
base_url = "https://fame2.heavyindustries.gov.in"
main_url = "ModelUnderFame.aspx"
import time

def clean_metrix_keys(column_data):
    if "range" in column_data.text.strip().lower():
        return "range"
    elif "speed" in column_data.text.strip().lower():
        return "max_speed"
    elif "consumption" in column_data.text.strip().lower():
        return "electric_energy_consumption"
    elif "technology" in column_data.text.strip().lower():
        return "battery_technology"
    elif "capacity" in column_data.text.strip().lower():
        return "battery_capacity"
    elif "density" in column_data.text.strip().lower():
        return "battery_density"
    elif "cycle" in column_data.text.strip().lower():
        return "battery_cycle"
    else:
        return None

def process_expanded_data_row(row):
    columns = row.find_all("td")
    try:
        current_key = clean_metrix_keys(columns[0])
        if current_key:
            expanded_data = {current_key.strip(): columns[1].text.strip()}
        else:
            raise IndexError
    except IndexError:
        pass
    else:
        return expanded_data



def expand_this_data(column):
    expanded_data = {}
    link = column.find("a")
    response = requests.get(os.path.join(base_url, link["href"]))
    internal_soup = BeautifulSoup(response.content, "html.parser")
    table = internal_soup.find("table", class_="table table-bordered custom_table")
    # Find all the rows in the table
    rows = table.find_all("tr")
    for row in rows[1:]:
        processed_expanded_data = process_expanded_data_row(row)
        if processed_expanded_data:
            expanded_data.update(processed_expanded_data)
    return expanded_data

def check_vehicle_type(one_row_data):
    columns = one_row_data[0].find_all("td")

    if "three" in columns[3].text.lower():
        return "3 wheeler"
    elif "four" in columns[3].text.lower():
        return "4 wheeler"
    elif "two" in columns[3].text.lower():
        return "2 wheeler"




def process_main_table(main_table, oem_name, base_document):
    rows_in_table = main_table.find_all("tr")[1:]
    vehicle_type = check_vehicle_type(rows_in_table)
    for row in rows_in_table:
        columns = row.find_all("td")
        model_name = columns[1].text.strip()
        column_data = {}
        for col in columns[1:]:
            if col.text.strip() == "View":
                expanded_data = expand_this_data(col)
                column_data.update(expanded_data)

        if column_data:
            try:
                base_document[vehicle_type][oem_name].update({model_name: column_data})
            except KeyError:
                base_document[vehicle_type].update({oem_name: {model_name: column_data}})
    return base_document

def short_oem_name(oem_text):
    return " ".join(oem_text.split(": ")[1].split(" ")[:2])



base_document = {
                 "4 wheeler": {},
                 "3 wheeler": {},
                 "2 wheeler": {}
                 }
response = requests.get(os.path.join(base_url, main_url))

# Check if the request was successful
if response.status_code == 200:
    # Create a BeautifulSoup object from the HTML content
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all the links on the page
    table = soup.find("table", class_="rifine-search_forFront")
    child_data = table.find_all("tr")
    vehicle_data = {}
    for child in child_data:
        try:
            full_oem_name = child.find("itemtemplate").text.strip()
        except AttributeError:
            continue
        else:
            oem_name = short_oem_name(full_oem_name)
            main_table = child.find("table", class_="main_table")
            base_document = process_main_table(main_table, oem_name, base_document)
            time.sleep(5)

    print(json.dumps(base_document))
