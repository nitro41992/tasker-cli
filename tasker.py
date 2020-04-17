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
import csv

db = TinyDB('db.json')
task_table = db.table('tasks')
project_table = db.table('projects')

number_of_concurrent_tasks = 3
project_list = []
format_str = "%A, %d %b %Y %I:%M:%S %p"
filename_format = '%Y-%m-%d %I%M-%p'
task_table_columns = ["Task Name", "Project Name", "Start Date", "End Date", "Last Restart Date", "Last Paused Date", "Paused", "Duration"]
command_list = ['add_running_task', 'add_paused_task', 'delete_task', 'end_task', 'list_pending_tasks', 'list_tasks', 
	'pause_task', 'start_paused_task', 'update_task_name', 'exit', 'export_completed_tasks', 'pause_all_tasks', 'delete_completed_tasks']
sorted_commands = sorted(command_list, key=str.lower)

def get_timestamp(format = format_str):
    result = datetime.now().strftime(format)
    return result

def select_column(input_list, column1, column2=''):
	if column2 == '':
		return [dict_row[column1] for dict_row in input_list]
	elif column2 != '':
		out = []
		for dict_row in input_list:
			c1 = dict_row[column1]
			c2 = dict_row[column2]
			row = f'{c1} - {c2}'
			out.append(row)
		return(out)

def to_csv(data_list, name):

	x = PrettyTable(task_table_columns)
	for task in data_list:
		x.add_row(task.values())
	click.echo(x)

	current_time = get_timestamp(filename_format)

	keys = data_list[0].keys()
	with open(f'{name} - Completed Tasks {current_time}.csv', 'a', newline='') as output_file:
		dict_writer = csv.DictWriter(output_file, keys)
		dict_writer.writeheader()
		dict_writer.writerows(data_list)	

command_completer = WordCompleter(
	sorted_commands, 
	ignore_case=True)

click.echo('Welcome to Tasker, press TAB to see the list of commands.')
while 1:

	user_input = prompt(
		'tasker > ',
		history=FileHistory('history.txt'),
		auto_suggest=AutoSuggestFromHistory(),
		completer=command_completer)

	if user_input == 'exit':

		if os.path.exists('history.txt'):
			os.remove('history.txt')
		
		click.echo('Goodbye.')
		break

	elif user_input == 'add_running_task':

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
		running_tasks = select_column(task_table.search((where('end_date') == '') & (where('paused') == False)), 'task_name')

		if task_name not in existing_task_names:

			if len(running_tasks) < number_of_concurrent_tasks:
				task_table.insert({'task_name': task_name, 'project_name': task_project, 'start_date': start_time, 'end_date': '',
				'last_restart_date': start_time, 'last_paused_date': '', 'paused': False, 'duration': '0 days, 0:00:00'})
				click.echo(f'Task: "{task_name}" successfully started. Time: {start_time}')

				if task_project not in project_list:
					project_table.insert({'project_name': task_project, 'created_on': start_time})

			else: 
				click.echo('You can only have a maximum of 3 running tasks at any time. Please Pause or End existing running Tasks.')
		else:
			click.echo('That Task name already exists for that project. Please choose a different Task name')

	elif user_input == 'add_paused_task':

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
			'last_restart_date': '', 'last_paused_date': start_time, 'paused': True, 'duration': '0 days, 0:00:00'})

			if task_project not in project_list:
				project_table.insert({'project_name': task_project, 'created_on': start_time})

			click.echo(f'Task: "{task_name}" successfully started. Time: {start_time}')
		else:
			click.echo('That Task name already exists for that project. Please choose a different Task name')

	elif user_input == 'end_task':

		task_list = select_column(task_table.search(where('end_date') == ''), 'task_name', 'project_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()
		task_to_end = task_session.prompt('Select Started Task to End: ', completer = task_command_completer)
		
		if task_to_end in task_list:

			current_task_project = task_to_end.split(' - ')[1]
			task_to_end = task_to_end.split(' - ')[0]

			current_time = get_timestamp()
			task_list = select_column(task_table.search(where('end_date') == ''), 'task_name')
			paused_tasks = select_column(task_table.search((where('paused') == True) & (where('project_name') == current_task_project)), 'task_name')

			current_start_time = select_column(task_table.search(where('task_name') == task_to_end), 'last_restart_date')[0]
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
			total_duration = str(dt + diff)

			if task_to_end not in paused_tasks:
				task_table.update({'duration': total_duration, 'end_date': current_time, 'paused': False}, (where('task_name') == task_to_end) & (where('project_name') == current_task_project))
				click.echo(f'Task: "{task_to_end}" successfully ended. Time: {current_time}')

			else:
				task_table.update({'end_date': current_time, 'paused': False}, (where('task_name') == task_to_end) & (where('project_name') == current_task_project))
				click.echo(f'Task: "{task_to_end}" successfully ended. Time: {current_time}')

		else:
			click.echo('That Task does not exist or has ended, please try again.')
	
	elif user_input == 'delete_task':
		task_list = select_column(task_table.all(), 'task_name', 'project_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()

		task_to_delete = task_session.prompt(
			'Select Task to Delete: ',
			completer = task_command_completer,
		)

		task_list = select_column(task_table.all(), 'task_name')
		current_task_project = task_to_delete.split(' - ')[1]
		task_to_delete = task_to_delete.split(' - ')[0]

		confirm =  task_session.prompt(f'Are you sure you want to delete "{task_to_delete}" (y/n): ')

		if confirm == 'y':
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
	
	elif user_input == 'list_tasks':
		all_tasks =  task_table.all()

		click.echo('\n')
		x = PrettyTable(task_table_columns)
		for task in all_tasks:
			x.add_row(task.values())
		click.echo(x)

	elif user_input == 'pause_task':
		
		task_list = select_column(task_table.search((where('end_date') == '') & (where('paused') == False)), 'task_name', 'project_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()

		task_to_pause = task_session.prompt(
			'Select Started Task to Pause: ',
			completer = task_command_completer,
		)

		current_time = get_timestamp()
		current_task_project = task_to_pause.split(' - ')[1]
		task_to_pause = task_to_pause.split(' - ')[0]
		task_list = select_column(task_table.search((where('end_date') == '') & (where('paused') == False)), 'task_name')

		if task_to_pause in task_list:
			current_start_time = select_column(task_table.search(where('task_name') == task_to_pause), 'last_restart_date')[0]
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
			click.echo('That Task does not exist or is already Paused, please try again.')

	elif user_input == 'start_paused_task':

		task_list = select_column(task_table.search((where('end_date') == '') & (where('paused') == True)), 'task_name', 'project_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()

		task_to_restart = task_session.prompt(
			'Select Paused Task to Restart: ',
			completer = task_command_completer,
		)

		current_task_project = task_to_restart.split(' - ')[1]
		task_to_restart = task_to_restart.split(' - ')[0]

		current_time = get_timestamp()
		task_list = select_column(task_table.search((where('end_date') == '') & (where('paused') == True)), 'task_name')
		running_tasks = select_column(task_table.search((where('end_date') == '') & (where('paused') == False)), 'task_name')

		if task_to_restart in task_list:

			is_ended = select_column(task_table.search((where('task_name') == task_to_restart) & (where('project_name') == current_task_project)), 'end_date')[0]
			if is_ended == '':
				if len(running_tasks) < number_of_concurrent_tasks:
					task_table.update({'last_restart_date': current_time, 'paused': False}, (where('task_name') == task_to_restart) & (where('project_name') == current_task_project))
					click.echo(f'Task: "{task_to_restart}" successfully restarted. Time: {current_time}')

				else: 
					click.echo('You can only have a maximum of 3 running tasks at any time. Please Pause or End existing running Tasks.')

			else:
				click.echo('The Task has ended. Please create a new Task.')
		else:
			click.echo('That Task does not exist or is not Paused, please try again.')

	elif user_input == 'update_task_name':

		task_list = select_column(task_table.all(), 'task_name', 'project_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()

		task_to_update_name = task_session.prompt(
			'Select Task to Update: ',
			completer = task_command_completer,
		)

		name_to_update_to = task_session.prompt(
			'Update the Task Name: ',
			completer = task_command_completer,
			default = task_to_update_name
		).split(' - ')[0]

		task_list = select_column(task_table.all(), 'task_name')
		current_task_project = task_to_update_name.split(' - ')[1]
		task_to_update_name = task_to_update_name.split(' - ')[0]

		if task_to_update_name in task_list:
			
			existing_task_names = select_column(task_table.search(where('project_name') == current_task_project), 'task_name')
		
			if name_to_update_to not in existing_task_names:

				task_table.update({'task_name': name_to_update_to, 'paused': False}, (where('task_name') == task_to_update_name) & (where('project_name') == current_task_project))
				click.echo(f'Task "{task_to_update_name}" has been updated to "{name_to_update_to}"')
			else:
				click.echo(f'The Task name {name_to_update_to} already exists for the project {current_task_project}. Please choose a different Task name.')			
		else:
			click.echo('That Task does not exist, please try again.')		

	elif user_input == 'export_completed_tasks':

		completed_tasks =  task_table.search(where('end_date') != '')

		task_session = PromptSession()

		name = task_session.prompt('Your Name (Please be consistent with previous exports): ')

		if len(completed_tasks) > 0:
			to_csv(completed_tasks, name)
			click.echo('Completed Tasks exported.')
		else:
			click.echo('There were not completed Tasks to export.')

	elif user_input == 'pause_all_tasks':
		
		task_list = select_column(task_table.search((where('end_date') == '') & (where('paused') == False)), 'task_name', 'project_name')

		if len(task_list) > 0:
			
			for task_to_pause in task_list:

				current_time = get_timestamp()
				current_task_project = task_to_pause.split(' - ')[1]
				task_to_pause = task_to_pause.split(' - ')[0]

				current_start_time = select_column(task_table.search(where('task_name') == task_to_pause), 'last_restart_date')[0]
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
			click.echo('There are no running Tasks to Pause.')

	elif user_input == 'delete_completed_tasks':
		
		task_list = select_column(task_table.search((where('end_date') != '') & (where('paused') == False)), 'task_name', 'project_name')
		completed_tasks =  task_table.search(where('end_date') != '')

		task_session = PromptSession()
		confirm =  task_session.prompt(f'Are you sure you want to delete all tasks? You will be forced to export before deleting. (y/n): ')

		if confirm == 'y':

			name = task_session.prompt('Your Name (Please be consistent with previous exports): ')

			if len(completed_tasks) > 0:
				to_csv(completed_tasks, name)
				click.echo('Completed Tasks exported.')
			else:
				click.echo('There were not completed Tasks to export.')


			for task_to_delete in task_list:

				current_task_project = task_to_delete.split(' - ')[1]
				task_to_delete = task_to_delete.split(' - ')[0]
		
				task_table.remove((where('task_name') == task_to_delete) & (where('project_name') == current_task_project) )
				click.echo(f'Task: "{task_to_delete}" successfully deleted.')


		elif confirm == 'n':

			click.echo('Deletion cancelled.')

		else:

			click.echo('Did not understand answer to confirmation. Please try again.')

	else:
		click.echo('Not a valid command. Press TAB to view list of possible commands. \n')


# task_table.purge()
# project_table.purge()
