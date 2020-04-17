from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit import PromptSession
import click
import os
from datetime import datetime
import time
from tinydb import TinyDB, Query, where

db = TinyDB('db.json')
task_table = db.table('tasks')
project_table = db.table('projects')

project_list = []
format_str = "%A, %d %b %Y %I:%M:%S %p"

def get_timestamp():
    result = datetime.now().strftime(format_str)
    return result

def select_column(list, column):
	return [dict_row[column] for dict_row in list]


command_completer = WordCompleter(['add_task', 'delete_task', 'end_task', 'list_pending_tasks', 'list_all_tasks', 'restart_task', 'exit'], 
ignore_case=True)

while 1:

	user_input = prompt(
		'tasker > ',
		history=FileHistory('history.txt'),
		auto_suggest=AutoSuggestFromHistory(),
		completer=command_completer
	)

	if user_input == 'exit':

		if os.path.exists('history.txt'):
			os.remove('history.txt')
		
		click.echo('Goodbye.')
		break

	elif user_input == 'add_task':

		project_list = select_column(project_table.all(), 'project_name')
		project_command_completer = WordCompleter(project_list, ignore_case=True)

		task_session = PromptSession()

		task_name = task_session.prompt(
			'Name: '
		)
		
		task_project = task_session.prompt(
			'Project: ',
			completer=project_command_completer
		)

		start_time = get_timestamp()

		task_table.insert({'task_name': task_name, 'project_name': task_project,'start_date': start_time, 'end_date': '', 'duration': ''})
		
		if task_project not in project_list:
			project_table.insert({'project_name': task_project, 'created_on': start_time})

		print(f'Task: "{task_name}" successfully started. Time: {start_time}')

	elif user_input == 'end_task':

		task_list = select_column(task_table.search(where('end_date') == ''), 'task_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()

		task_to_end = task_session.prompt(
			'Select Started Task to End: ',
			completer = task_command_completer,
		)

		task_end_time = get_timestamp()

		diff = 0
	
		try:
			current_start_time = select_column(task_table.search(where('task_name') == task_to_end), 'start_date')[0]
			current_task_project = select_column(task_table.search(where('task_name') == task_to_end), 'project_name')[0]

			formatted_end_date = datetime.strptime(task_end_time, format_str)
			formatted_start_date = datetime.strptime(current_start_time, format_str)
		

			diff = str(formatted_end_date - formatted_start_date)
		except:
			pass

		if task_to_end in task_list:
			task_table.update({'end_date': task_end_time, 'duration': diff}, (where('task_name') == task_to_end) & (where('project_name') == current_task_project))
		else:
			click.echo('That Task does not exist, please try again.')
	
	else:
		click.echo('Not a valid command. Please try another command. Press TAB to view list of possible commands')




task_table.purge()
project_table.purge()