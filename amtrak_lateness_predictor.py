import datetime
import re

import pandas as pd
import requests


def get_response(train_number):
    '''Retrieve the HTML response, or display any errors'''

    URL = "http://juckins.net/amtrak_status/archive/html/history.php"
    VERY_LARGE_NUMBER = 1000000

    today = datetime.date.today()
    one_year_ago = today - datetime.timedelta(days=365)
    DATE_FORMAT = "%m/%d/%Y"

    parameters = {
            "train_num": train_number,
            "station": "",
            "date_start": one_year_ago.strftime(DATE_FORMAT),
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


def clean_response(response_text):
    '''
    Extract train time information from the juckins.net response, and
    clean it by removing useless columns and converting data types
    '''

    # Parse the HTML table into a usable object, ignoring the empty top row
    # There is only one table in the HTML text, so extract that
    df = pd.io.html.read_html(
            io=response_text,
            header=1
            )[0]

    # Throw out the row if no time information exists
    df.filter(regex="Sch [A-Z]{2}")[0]

    # Fix data types for the date columns
    df["departure_date"] = pd.to_datetime(df["Origin Date"])
    df["scheduled"] = pd.to_datetime(df.filter(regex="Sch [A-Z]{2}")[0])

    # Determine the difference between scheduled and actual times
    # In almost no cases is this difference more than 24 hours, so
    # assume that the two are within one day of each other
    df["delay"] = pd.to_timedelta(
            arg=(
            df["Comments"].extract("\D+: (\d*{0,2})\D+\d{0,2}\D*") * 60 +
            df["Comments"].extract("\D+: \d*{0,2}\D+\(d{0,2})\D*")
            ),
            unit="m"
            )

    # Identify departure day and station name as composite keys
    df = df.rename(columns={"Station": "station"})
    df = df.set_index(["departure_date", "station"])

    # Return only the columns useful to prediction
    df = df[["departure_date", "station", "scheduled", "delay"]]
    return df


def get_prediction_for_train(train_number, destination_station):
    '''Main function of the module, to perform the prediction'''

    # Get and clean all train data from route for last year
    response_text = get_response(train_number)
    cleaned_table = clean_response(response_text)

    # Filter the data for only the given station, and for applicable weekdays
    cleaned_table = [
            row for row in cleaned_table if
            row["Station"] == destination_station and
            row["Sch DP"].date().weekday() == datetime.date.today().weekday()
            ]

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
