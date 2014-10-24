import datetime
import itertools

from bs4 import BeautifulSoup
# Straight import of <dateutil> and use of parse function does not work
from dateutil.parser import parse as datetime_parse
import requests


def get_response(train_number):
    '''Retrieve the HTML response, or display any errors'''

    URL = "http://juckins.net/amtrak_status/archive/html/history.php"
    VERY_LARGE_NUMBER = 1000000

    today = datetime.date.today()
    last_year = today - datetime.timedelta(days=365)
    DATE_FORMAT = "%m/%d/%Y"

    parameters = {
            "train_num": train_number,
            "station": "",
            "date_start": last_year.strftime(DATE_FORMAT),
            "date_end": today.strftime(DATE_FORMAT),
            "sort": "schDp",
            "sort_dir": "DESC",
            "limit": VERY_LARGE_NUMBER,
            "co": "gt"
            }
    response = requests.get(URL, params=parameters)

    # Make sure that the response was successful
    response.raise_for_status()

    # Return the returned HTML text
    return response.text


def parse_response(response_text):
    '''Extract train time information from the juckins.net response'''

    # Create a table parser
    table_parser = BeautifulSoup(response_text)
    table = table_parser.find("table")
    rows = iter(table.findAll("tr"))

    # Determine the names of each field
    _table_title = next(rows)
    field_names = [header.text for header in next(rows)]

    # Extract the values from each row
    all_values = []
    for row in rows:
        values = [cell.text for cell in row]
        values_labeled = dict(itertools.izip(field_names, values))
        all_values.append(values_labeled)

    return all_values


def clean_table(table):
    '''Remove useless columns and convert text to proper data types'''

    cleaned_table = []
    for row in table:
        
        drop_this_row = False
        
        for key in row.keys():
            if key.startswith("Sch ") or key.startswith("Act "):
        
                # Throw out the row if the time data do not exist
                if row[key].isspace():
                    drop_this_row = True

                # Convert the plain text values to Python data types
                row[key] = datetime_parse(row[key])
        row["Origin Date"] = datetime_parse(row["Origin Date"]).date()

        if drop_this_row == False:
            cleaned_table.append(row)

    return cleaned_table


def get_prediction_for_train(train_number, destination_station):
    '''Main function of the module, to perform the prediction'''

    # Get and clean all train data from route for last year
    response_text = get_response(train_number)
    raw_table = parse_response(response_text)
    cleaned_table = clean_table(raw_table)

    # Filter the data for only the given station, and for applicable weekdays
    cleaned_table = [
            row for row in cleaned_table if
            row["Station"] == destination_station and
            row["Sch DP"].date().weekday() == datetime.date.today().weekday()
            ]

    # Calculate the delay, based on scheduled and actual times
    for row in cleaned_table:
        row["delay"] = row["Sch DP"] - row["Act DP"]

    # Determine the average delay for the given station
    delays = [row["delay"] for row in cleaned_table]
    average_delay = sum(delays, datetime.timedelta(0)) / len(delays)

    print(average_delay)


# Test example while developing
if __name__ == "__main__":
    get_prediction_for_train(
            train_number=353,
            destination_station="HMI"
            )
