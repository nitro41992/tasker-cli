from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit import PromptSession
import click
import os
from datetime import datetime, timedelta
import time
from tinydb import TinyDB, Query, where
from tinydb.operations import delete
from prettytable import PrettyTable

db = TinyDB('db.json')
task_table = db.table('tasks')
project_table = db.table('projects')

project_list = []
format_str = "%A, %d %b %Y %I:%M:%S %p"
task_table_columns = ["Task Name", "Project Name", "Start Date", "End Date", "Last Restart Date", "Last Paused Date", "Paused", "Duration"]

def get_timestamp():
    result = datetime.now().strftime(format_str)
    return result

def select_column(list, column):
	return [dict_row[column] for dict_row in list]


command_completer = WordCompleter(
	['add_task', 'delete_task', 'end_task', 'list_pending_tasks', 'list_all_tasks', 
	'pause_task', 'restart_task', 'update_task_name', 'exported_completed_tasks', 'exit'], 
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
		existing_task_names = select_column(task_table.search(where('project_name') == task_project), 'task_name')

		if task_name not in existing_task_names:
			task_table.insert({'task_name': task_name, 'project_name': task_project, 'start_date': start_time, 'end_date': '',
			'last_restart_date': start_time, 'last_paused_date': '', 'paused': False, 'duration': '0 days, 0:00:00'})

			if task_project not in project_list:
				project_table.insert({'project_name': task_project, 'created_on': start_time})

			click.echo(f'Task: "{task_name}" successfully started. Time: {start_time}')
		else:
			click.echo('That Task name already exists for that project. Please choose a different Task name')

	elif user_input == 'end_task':
		task_list = select_column(task_table.search(where('end_date') == ''), 'task_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()

		task_to_end = task_session.prompt(
			'Select Started Task to End: ',
			completer = task_command_completer,
		)

		current_time = get_timestamp()

		if task_to_end in task_list:
			current_start_time = select_column(task_table.search(where('task_name') == task_to_end), 'last_restart_date')[0]
			current_task_project = select_column(task_table.search(where('task_name') == task_to_end), 'project_name')[0]
			current_duration = select_column(task_table.search(where('task_name') == task_to_end), 'duration')[0]

			formatted_current_time = datetime.strptime(current_time, format_str)
			formatted_start_date = datetime.strptime(current_start_time, format_str)

			if 'days' in current_duration:
				days_v_hms = current_duration.split('days,')
				hms = days_v_hms[1].split(':')
			else:
				hms = current_duration.split(':')

			dt = timedelta(hours=int(hms[0]), minutes=int(hms[1]), seconds=float(hms[2]))

			diff = formatted_current_time - formatted_start_date
			paused_duration = str(dt + diff)
		
			task_table.update({'duration': paused_duration, 'end_date': current_time}, (where('task_name') == task_to_end) & (where('project_name') == current_task_project))
			click.echo(f'Task: "{task_to_end}" successfully ended. Time: {current_time}')

		else:
			click.echo('That Task does not exist or has ended, please try again.')
	
	elif user_input == 'delete_task':
		task_list = select_column(task_table.all(), 'task_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()

		task_to_delete = task_session.prompt(
			'Select Task to Delete: ',
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
		x = PrettyTable(task_table_columns)
		for task in pending_tasks:
			x.add_row(task.values())
		click.echo(x)
	
	elif user_input == 'list_all_tasks':
		all_tasks =  task_table.all()

		click.echo('\n')
		x = PrettyTable(task_table_columns)
		for task in all_tasks:
			x.add_row(task.values())
		click.echo(x)

	elif user_input == 'pause_task':
		
		task_list = select_column(task_table.search(where('end_date') == ''), 'task_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()

		task_to_pause = task_session.prompt(
			'Select Started Task to Pause: ',
			completer = task_command_completer,
		)

		current_time = get_timestamp()

		if task_to_pause in task_list:
			current_start_time = select_column(task_table.search(where('task_name') == task_to_pause), 'last_restart_date')[0]
			current_task_project = select_column(task_table.search(where('task_name') == task_to_pause), 'project_name')[0]
			current_duration = select_column(task_table.search(where('task_name') == task_to_pause), 'duration')[0]

			formatted_current_time = datetime.strptime(current_time, format_str)
			formatted_start_date = datetime.strptime(current_start_time, format_str)
			
			if 'days' in current_duration:
				days_v_hms = current_duration.split('days,')
				hms = days_v_hms[1].split(':')
			else:
				hms = current_duration.split(':')

			dt = timedelta(hours=int(hms[0]), minutes=int(hms[1]), seconds=float(hms[2]))

			diff = formatted_current_time - formatted_start_date
			paused_duration = str(dt + diff)
		
			task_table.update({'duration': paused_duration, 'last_paused_date': current_time, 'paused': True}, (where('task_name') == task_to_pause) & (where('project_name') == current_task_project))
			click.echo(f'Task: "{task_to_pause}" successfully paused. Time: {current_time}')
		else:
			click.echo('That Task does not exist, please try again.')

	elif user_input == 'restart_task':

		task_list = select_column(task_table.search(where('end_date') == ''), 'task_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()

		task_to_restart = task_session.prompt(
			'Select Paused Task to Restart: ',
			completer = task_command_completer,
		)

		current_time = get_timestamp()

		if task_to_restart in task_list:
			is_ended = select_column(task_table.search(where('task_name') == task_to_restart), 'end_date')[0]
			if is_ended == '':
				current_task_project = select_column(task_table.search(where('task_name') == task_to_restart), 'project_name')[0]
			
				task_table.update({'last_restart_date': current_time, 'paused': False}, (where('task_name') == task_to_restart) & (where('project_name') == current_task_project))
				click.echo(f'Task: "{task_to_restart}" successfully restarted. Time: {current_time}')
			else:
				click.echo('The Task has ended. Please create a new Task.')
		else:
			click.echo('That Task does not exist, please try again.')

	elif user_input == 'update_task_name':

		task_list = select_column(task_table.all(), 'task_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()

		task_to_update_name = task_session.prompt(
			'Select Task to Update: ',
			completer = task_command_completer,
		)

		name_to_update_to = task_session.prompt(
			'Update the Task Name: ',
			completer = task_command_completer,
			default= task_to_update_name
		)

		if task_to_update_name in task_list:

			current_task_project = select_column(task_table.search(where('task_name') == task_to_update_name), 'project_name')[0]
			task_table.update({'task_name': name_to_update_to, 'paused': False}, (where('task_name') == task_to_update_name) & (where('project_name') == current_task_project))
			click.echo(f'Task "{task_to_update_name}" has been updated to "{name_to_update_to}"')	
				
		else:
			click.echo('That Task does not exist, please try again.')		

	else:
		click.echo('Not a valid command. Press TAB to view list of possible commands. \n')


# task_table.purge()
# project_table.purge()