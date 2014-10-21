import datetime
import itertools

from bs4 import BeautifulSoup
import dateutil
import requests


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
	'''Remove useless columns and convert to proper data types'''

	cleaned_table = []
	for row in table:
		
		drop_this_row = False
		
		for key in row.keys():
			if key.startswith("Sch ") or key.startswith("Act "):
		
				# Throw out the row if the time data do not exist
				if row[key].isspace():
					drop_this_row = True

				# Convert the plain text values to Python data types
				row[key] = dateutil.parser.parse(row[key])
		row["Origin Date"] = dateutil.parser.parse(row["Origin Date"]).date()

		if drop_this_row == False:
			cleaned_table.append(row)

	return cleaned_table


# Determine current date and comparable weekdays
today = datetime.date.today()
ONE_WEEK = datetime.timedelta(days=7)
WEEKS_IN_A_YEAR = 52

days_to_compare = []
# for weeks_ago in range(1, WEEKS_IN_A_YEAR + 1):
# 	day_to_compare = today - ONE_WEEK * weeks_ago
# 	days_to_compare.append(day_to_compare)


