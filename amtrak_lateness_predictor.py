import datetime
import logging
import re

import lxml.html
import requests


# logging.basicConfig(level=logging.DEBUG)
PERCENTAGE_TO_ANALYZE = 33

TODAY = datetime.date.today()
ONE_YEAR_AGO = TODAY - datetime.timedelta(days=365)
DATE_FORMAT = "%m/%d/%Y"
VERY_LARGE_NUMBER = 1000000


def get_chart_url(train_number, station):
    ''' Build the URL for a chart that provides auxilary information '''

    parameters = {
        'train_num': train_number,
        'station': station,
        'date_start': ONE_YEAR_AGO.strftime(DATE_FORMAT),
        'date_end': TODAY.strftime(DATE_FORMAT),
        'sort': 'd_dp',
        'chartsize': '2',
        'smooth': '0'
    }
    built_url = requests.Request(
        url='http://juckins.net/amtrak_status/archive/html/historychart.php',
        params=parameters
    ).prepare().url
    return built_url


def get_response(train_number):
    '''Retrieve the HTML response, or display any errors'''

    parameters = {
        "train_num": train_number,
        "station": "",
        "date_start": ONE_YEAR_AGO.strftime(DATE_FORMAT),
        "date_end": TODAY.strftime(DATE_FORMAT),
        "sort": "d_dp",
        "sort_dir": "DESC",
        "limit": VERY_LARGE_NUMBER,
        "co": "gt"
    }
    response = requests.get(
        'http://juckins.net/amtrak_status/archive/html/history.php',
        params=parameters
    )
    logging.debug("URL accessed: {}".format(response.request.url))

    # Make sure that the response was successful
    response.raise_for_status()
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
    assert table[1].xpath('th/text()')[2] == "Sch DP"
    assert table[1].xpath('th/text()')[3] == "Act DP"
    assert table[1].xpath('th/text()')[4] == "Comments"
    assert table[1].xpath('th/text()')[5] == "DP Delay (mins)"
    assert table[1].xpath('th/text()')[6] == "Service Disruption"
    assert table[1].xpath('th/text()')[7] == "Cancellations"
    assert len(table[-1].xpath('td')) == 1

    table = table[2:-3]

    # Convert to native data types
    response_table = []
    for row in table:
        response_table_row = {}

        response_table_row['station'] = row.xpath('td[2]/text()')[0]
        response_table_row['delay'] = datetime.timedelta(seconds=int(row.xpath('td[6]//text()')[0]) * 60)
        response_table_row['origin'] = datetime.datetime.strptime(
            re.sub(r'\s\([A-Z][a-z]\)', '', row.xpath('td[1]/a/text()')[0]),
            '%m/%d/%Y').date()
        response_table_row['scheduled'] = datetime.datetime.strptime(
            re.sub(r'\s\([A-Z][a-z]\)', '', row.xpath('td[3]/text()')[0]),
            '%m/%d/%Y %I:%M %p')
        response_table_row['service_disruption'] = bool(row.xpath('td[7]//text()'))
        response_table_row['cancellation'] = bool(row.xpath('td[8]//text()'))

        response_table.append(response_table_row)
    logging.debug('{} rows in response table'.format(len(response_table)))
    return response_table


def filter_table(full_table, destination):
    ''' Filter the full delay table down to just relevant records '''

    # Collect all information on the current train
    current_train = None
    newest_train_seen = datetime.datetime(2000, 1, 1)
    for row in full_table:
        if row['scheduled'] > newest_train_seen:
            logging.debug('Found a train ({}) newer than before ({})'.format(
                row['scheduled'], newest_train_seen))
            newest_train_seen = row['scheduled']
            current_train = row
    logging.debug("Most current status: {}".format(current_train))

    filtered_table = full_table
    filtered_table = [x for x in filtered_table if not x['cancellation']]
    filtered_table = [x for x in filtered_table if x['service_disruption'] == current_train['service_disruption']]
    filtered_table = [x for x in filtered_table if x['origin'].weekday() == current_train['origin'].weekday()]
    logging.debug("{} rows in filtered table".format(len(filtered_table)))

    for row in filtered_table:
        if row['station'] == current_train['station']:
            # Calculate how similar this route is to the current train's performance
            row['difference_from_current_delay'] = abs(current_train['delay'] - row['delay'])
            for other_row in filtered_table:
                # Copy this similarity value to the whole of that route
                if other_row['origin'] == row['origin']:
                    other_row['difference_from_current_delay'] = row['difference_from_current_delay']
    filtered_table = [x for x in filtered_table if 'difference_from_current_delay' in x]
    filtered_table = sorted(filtered_table, key=lambda k: k['difference_from_current_delay'])

    table_to_analyze = []
    for row in filtered_table:
        # Only observe timeliness at the desired destination
        if row['station'] == destination:
            table_to_analyze.append(row)

    rows_to_analyze = len(table_to_analyze) * PERCENTAGE_TO_ANALYZE / 100
    table_to_analyze = table_to_analyze[:rows_to_analyze]
    logging.debug('{} rows in table to analyze'.format(len(table_to_analyze)))

    return table_to_analyze


def get_mean_delay(table):
    ''' Calculate the average delay from a table including delays '''

    delays = [row['delay'] for row in table]
    mean_delay = sum(delays, datetime.timedelta()) / len(delays)
    assert type(mean_delay) == type(datetime.timedelta())
    mean_delay = mean_delay.seconds / 60
    return mean_delay


def get_prediction_for_train(train_number, destination):
    '''Main function of the module, to perform the prediction'''

    chart_url = get_chart_url(train_number, destination)
    response_text = get_response(train_number)
    cleaned_table = clean_response(response_text)
    filtered_table = filter_table(cleaned_table, destination)
    mean_delay = get_mean_delay(filtered_table)

    print("Mean delay for train {0} going to station {1}: {2} minutes".format(
        train_number, destination, mean_delay))
    print("Chart and historical data: {}".format(chart_url))

# Test example while developing
if __name__ == "__main__":
    get_prediction_for_train(
        train_number="350",
        destination="ARB"
    )
