import csv
import os
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from click import echo
from colorama import Fore, init
from prettytable import ALL as ALL
from prettytable import PrettyTable
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.completion import WordCompleter, FuzzyCompleter
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from tinydb import Query, TinyDB, where
from tinydb.operations import delete
from art import text2art

style = Style.from_dict({'':'gold'})
prompt_symbol = FormattedText([('gold bold', '<< tasker >> ')])

dirname = os.path.dirname(__file__)
datafile = os.path.join(dirname, 'db.json')
db = TinyDB(datafile)
task_table = db.table('tasks')
project_table = db.table('projects')
name_table = db.table('names')

number_of_concurrent_tasks = 3
max_line_length = 25
project_list = []
hcis_codes = pd.read_csv('HCIS_Codes.csv')
project_list = hcis_codes['Healthcare Division Program Name / Notes'] + ': ' + hcis_codes['(Fund/Index)      RAD Id']

format_date_str = "%A, %d %b %Y %I:%M:%S %p"
format_delta_str_hours = "%d days %H:%M:%S"
filename_format = '%Y-%m-%d %I%M-%p'
zero_delta = '0 days 0:00:00'

task_table_columns = ["Task Name", 
					"Project Name", 
					"Start Date", 
					"End Date", 
					"Last Restart Date",
					"Last Paused Date",
					"Paused", 
					"Duration"]
command_list = [
				'timesheet_report'
				]
sorted_commands = sorted(command_list, key=str.lower)

# def custom_print_green(value):
# 	return(echo(Fore.GREEN + value))

# def custom_print_blue(value):
# 	return(echo(Fore.BLUE + value))

# def custom_print_red(value):
# 	return(echo(Fore.RED + value))

# command_completer = WordCompleter(
# 	sorted_commands, 
# 	ignore_case=True)

# custom_print_blue(text2art('<< tasker >>'))
# custom_print_blue('''
# tasker is a simple tool to track your daily/weekly tasks and export them as needed.
# You can add running tasks and start tracking the time right away or add paused tasks you can start later.
# Simply add a task and what project it belongs to. tasker will add it to your task list.
# Pause a task, or all tasks, and restar them later. tasker will aggregate total duration.
# End the task completely to let tasker know you are done with the task and it is ready to be exported.

# Press TAB to and scroll through to see the list of commands.
# ''')

# while 1:
# 	user_input = prompt(prompt_symbol, completer=command_completer, wrap_lines=False, complete_while_typing=True, style=style)

# 	if user_input == 'exit':

# 		if os.path.exists('history.txt'):
# 			os.remove('history.txt')
		
# 		custom_print_green('Goodbye.')
# 		break

# 	elif user_input == 'timesheet_report':

timesheet_report = pd.DataFrame()
tasks = pd.DataFrame(task_table.all())

timesheet_report['task_name'] = tasks['task_name']
timesheet_report['project_name'] = tasks['project_name']
timesheet_report['duration'] = tasks['duration']

total_duration = pd.to_timedelta(tasks['duration']).sum()
proportions = (pd.to_timedelta(tasks['duration']) / total_duration)

timesheet_report['percentages'] = round(proportions * 100, 2)
timesheet_report['timesheet_hours'] = proportions * 35

cli_table = PrettyTable(hrules=ALL)
cli_table.field_names = ['task_name', 'project_name', 'duration', 'percentages', 'timesheet_hours']

for task in timesheet_report.T.to_dict().values():
	cli_table.add_row([
		task['task_name'], 
		task['project_name'],
		task['duration'], 
		task['percentages'], 
		task['timesheet_hours']])
echo(cli_table)


