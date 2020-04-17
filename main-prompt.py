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
from tinydb.operations import delete
from prettytable import PrettyTable

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


command_completer = WordCompleter(
	['add_task', 'delete_task', 'end_task', 'list_pending_tasks', 'list_all_tasks', 
	'pause_task', 'pause_all_tasks', 'restart_task', 'update_project_name', 'exit'], 
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

		click.echo(f'Task: "{task_name}" successfully started. Time: {start_time}')

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
			click.echo(f'Task: "{task_to_end}" successfully completed. Time: {task_end_time}')
		else:
			click.echo('That Task does not exist, please try again.')
	
	elif user_input == 'delete_task':
		task_list = select_column(task_table.all(), 'task_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()

		task_to_delete = task_session.prompt(
			'Select Started Task to Delete: ',
			completer = task_command_completer,
		)

		confirm =  task_session.prompt(
			f'Are you sure you want to delete "{task_to_delete}" (y/n): ',
		)

		if confirm == 'y':
			task_end_time = get_timestamp()

			diff = 0
		
			try:
				current_task_project = select_column(task_table.search(where('task_name') == task_to_delete), 'project_name')[0]
			except:
				pass

			if task_to_delete in task_list:
				task_table.remove((where('task_name') == task_to_delete) & (where('project_name') == current_task_project) )
				click.echo(f'Task: "{task_to_delete}" successfully deleted.')
			else:
				click.echo('That Task does not exist, please try again.')
		elif confirm == 'n':
			click.echo('Deletion cancelled.')
		else:
			click.echo('Did not understand answer to confirmation. Please try again.')
	
	elif user_input == 'list_pending_tasks':
		pending_tasks =  task_table.search(where('end_date') == '')

		click.echo('\n')
		x = PrettyTable(["Task Name", "Project Name", "Start Date", "End Date", "Duration"])
		for task in pending_tasks:
			x.add_row(task.values())
		click.echo(x)
	
	elif user_input == 'list_all_tasks':
		all_tasks =  task_table.all()

		click.echo('\n')
		x = PrettyTable(["Task Name", "Project Name", "Start Date", "End Date", "Duration"])
		for task in all_tasks:
			x.add_row(task.values())
		click.echo(x)

	elif user_input == 'restart_task':
		pass

	elif user_input == 'pause_task':
		pass

	elif user_input == 'pause_all_tasks':
		pass
	
	else:
		click.echo('Not a valid command. Press TAB to view list of possible commands. \n')




# task_table.purge()
project_table.purge()