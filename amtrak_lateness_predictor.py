import datetime
import re

import lxml.html
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

    # Load the table into the parsing engine, and check its contents
    doc = lxml.html.fromstring(response_text)
    table = doc.xpath('//table/tr')

    assert len(table[0].xpath('th')) == 1
    assert table[1].xpath('th/text()')[0] == "Origin Date"
    assert table[1].xpath('th/text()')[1] == "Station"
    assert table[1].xpath('th/text()')[2].startswith("Sch ")
    assert table[1].xpath('th/text()')[3].startswith("Act ")
    assert table[1].xpath('th/text()')[4] == "Comments"
    assert table[1].xpath('th/text()')[5] == "Service Disruption"
    assert table[1].xpath('th/text()')[6] == "Cancellations"
    assert len(table[-1].xpath('td')) == 1

    table = table[2:-1]

    # Convert to native data types
    DELAY_RE = r'^(?:Departed|Arrived):\s*' \
            r'(?:(?P<hours>\d{1,2}) hours?(?:,| and)?)?\s*' \
            r'(?:(?P<minutes>\d{1,2}) minutes?)?\s*' \
            r'late\.$'
    df = []
    for row in table:
        df_row = {}

        df_row['station'] = row.xpath('td[2]/text()')[0]

        try:
            delay = row.xpath('td[5]//text()')[0]
        except IndexError:
            print("No delay information found for {}".format(df_row['station']))
            continue
        if re.match(DELAY_RE, delay):
            try:
                df_row['delay'] = datetime.timedelta(seconds=
                        int(re.search(DELAY_RE, delay).group("minutes")) * 60)
            except TypeError:
                df_row['delay'] = 0
            try:
                df_row['delay'] += datetime.timedelta(seconds=
                        int(re.search(DELAY_RE, delay).group("hours")) * 60 * 60)
            except TypeError:
                pass
        elif delay.endswith("n time."):
            df_row['delay'] = datetime.timedelta(0)
        else:
            print(
                    "Unparseable delay information found: '{}'".format(delay))
            continue

        df_row['origin_date'] = datetime.datetime.strptime(row.xpath(
                'td[1]/a/text()')[0], '%m/%d/%Y').date()
        df_row['service_disruption'] = bool(row.xpath('td[6]//text()'))
        df_row['cancellation'] = bool(row.xpath('td[7]//text()'))
        
        df.append(df_row)

    return df


def get_prediction_for_train(train_number, destination):
    '''Main function of the module, to perform the prediction'''

    # Get and clean all train data from route for last year
    response_text = get_response(train_number)
    cleaned_table = clean_response(response_text)

    # Filter the data for only the given station, and for applicable weekdays
    filtered_table = [
            row for row in cleaned_table if
            row["station"] == destination and
            row["origin_date"].weekday() == datetime.date.today().weekday()
            ]

    # Determine the average delay for the given station
    delays = [row['delay'] for row in filtered_table]
    average_delay = sum(delays, datetime.timedelta(0)) / len(delays)

    print("Average delay for train {0} going to station {1}: "
            "{2}".format(train_number, destination, average_delay))

# Test example while ddelayeveloping
if __name__ == "__main__":
    get_prediction_for_train(
            train_number=353,
            destination="HMI"
            )
