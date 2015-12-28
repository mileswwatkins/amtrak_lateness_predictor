import datetime
import re

import lxml.html
import requests


def get_response(train_number):
    '''Retrieve the HTML response, or display any errors'''

    URL = "http://juckins.net/amtrak_status/archive/html/history.php"
    VERY_LARGE_NUMBER = 1000000

    TODAY = datetime.date.today()
    ONE_YEAR_AGO = TODAY - datetime.timedelta(days=365)
    DB_STARTS_GIVING_ARR_DEP_SEPARATELY = datetime.date(2015, 5, 21)
    if ONE_YEAR_AGO > DB_STARTS_GIVING_ARR_DEP_SEPARATELY:
        start_date = ONE_YEAR_AGO
    else:
        start_date = DB_STARTS_GIVING_ARR_DEP_SEPARATELY
    DATE_FORMAT = "%m/%d/%Y"


    parameters = {
        "train_num": train_number,
        "station": "",
        "date_start": start_date.strftime(DATE_FORMAT),
        "date_end": TODAY.strftime(DATE_FORMAT),
        "sort": "schAr",
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
    DELAY_RE = (
        r'^(Arr|Dep):\s+'
        r'(?:(?P<hours>\d{1,2}) hr(?:,)?)?\s*'
        r'(?:(?P<minutes>\d{1,2}) min)?\s*'
        r'(early|late)\.?$'
    )

    df = []
    for row in table:
        df_row = {}

        if 'Average' in row.text_content() or 'Median' in row.text_content():
            continue

        df_row['station'] = row.xpath('td[2]/text()')[0]

        try:
            delay = row.xpath('td[5]//text()')[0].strip()
            # Keep only arrival information if both arrival and departure exist
            delay = re.sub(r'\s\|\sDep:\s.*', '', delay)
        except IndexError:
            print("No delay information found for station {}".format(
                df_row['station']))
            continue

        if 'On time' in delay:
            df_row['delay'] = datetime.timedelta(0)
        elif re.match(r'^[ECMP][SD]?T$', delay):
            # Time zone placeholders indicate that there is no actual time data
            continue
        elif re.match(DELAY_RE, delay):
            minutes_off = 0
            if re.search(DELAY_RE, delay).group("hours"):
                minutes_off += int(re.search(DELAY_RE, delay).group("hours")) * 60
            if re.search(DELAY_RE, delay).group("minutes"):
                minutes_off += int(re.search(DELAY_RE, delay).group("minutes"))
            if 'early' in delay:
                minutes_off *= -1
            df_row['delay'] = datetime.timedelta(seconds=minutes_off * 60)
        else:
            print("Unparseable delay information found: '{}'".format(delay))
            continue

        df_row['scheduled_date'] = datetime.datetime.strptime(
            re.sub(r'\s\([A-Z][a-z]\)', '', row.xpath('td[3]/text()')[0]),
            '%m/%d/%Y %I:%M %p').date()
        df_row['service_disruption'] = bool(row.xpath('td[6]//text()'))
        df_row['cancellation'] = bool(row.xpath('td[7]//text()'))

        df.append(df_row)

    return df


def filter_table(full_table, desintation, same_weekday=True):
    ''' Filter the full delay table down to just relevant records '''
    filtered_table = []
    for row in full_table:
        # Only observe timeliness at the desired desintation
        if row['station'] != desintation:
            continue

        # Throwing out cancelled trains seems reasonable
        if row['cancellation']:
            continue

        if same_weekday:
            if row['scheduled_date'].weekday() != datetime.date.today().weekday():
                continue

        filtered_table.append(row)

    return filtered_table


def get_mean_delay(table):
    ''' Calculate the average delay from a table including delays '''
    delays = [row['delay'] for row in table]
    mean_delay = sum(delays, datetime.timedelta(0)) / len(delays)
    assert type(mean_delay) == type(datetime.timedelta())
    mean_delay = mean_delay.seconds / 60
    return mean_delay


def get_prediction_for_train(train_number, destination):
    '''Main function of the module, to perform the prediction'''

    response_text = get_response(train_number)
    cleaned_table = clean_response(response_text)
    filtered_table = filter_table(cleaned_table, destination)
    mean_delay = get_mean_delay(filtered_table)

    print("Mean delay for train {0} going to station {1}: {2} minutes".format(
        train_number, destination, mean_delay))

# Test example while ddelayeveloping
if __name__ == "__main__":
    get_prediction_for_train(
        train_number=2,
        destination="NOL"
    )
