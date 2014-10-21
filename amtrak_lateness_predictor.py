import datetime

import requests


def parse_response(response_text):
	'''Extract train time information from the Dixieland response'''

	# Split out each row containing data
	FIRST_ROW_OF_DATA = 12
	data_lines = response_text.split("\n")[FIRST_ROW_OF_DATA - 1 :]

	# Determine the number of characters in each field
	max_line_length = 0
	for line in data_lines:
		line_length = len(line)
		if line_length > max_line_length:
			max_line_length = line_length

	field_widths = [2, 5, 3, 6, 3, 6, 6, 6]
	comment_field_length = max_line_length - sum(field_widths)
	field_widths.append(comment_field_length)

	# Parse each row of data
	FIELD_NAMES = [
			"have_data",
			"station_code",
			"scheduled_arrival_day",
			"scheduled_arrival_time",
			"scheduled_departure_day",
			"scheduled_departure_time",
			"actual_arrival_time",
			"actual_departure_time",
			"comments"
			]

	for line in data_lines:
		values = []

		for field_number in range(len(field_widths)):
			first_character = sum(field_widths[:field_number])
			last_character = first_character + field_widths[field_number]

			value = {
					FIELD_NAMES[field_number]:
					line[first_character:last_character]
					}
			values.append(value)

		


# Determine current date and comparable weekdays
today = datetime.date.today()
ONE_WEEK = datetime.timedelta(days=7)
WEEKS_IN_A_YEAR = 52

days_to_compare = []
for weeks_ago in range(1, WEEKS_IN_A_YEAR + 1):
	day_to_compare = today - ONE_WEEK * weeks_ago
	days_to_compare.append(day_to_compare)


