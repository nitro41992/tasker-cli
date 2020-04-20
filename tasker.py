import csv
import os
import time
from datetime import datetime, timedelta

from click import echo
from colorama import Fore, init
from prettytable import ALL as ALL
from prettytable import PrettyTable
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from pyfiglet import Figlet
from tinydb import Query, TinyDB, where
from tinydb.operations import delete
from art import text2art



prompt_symbol = FormattedText([
    ('gold bold', '<< tasker >> ')
])

dirname = os.path.dirname(__file__)
datafile = os.path.join(dirname, 'db.json')
db = TinyDB(datafile)
task_table = db.table('tasks')
project_table = db.table('projects')


number_of_concurrent_tasks = 3

max_line_length = 20

project_list = []

format_date_str = "%A, %d %b %Y %I:%M:%S %p"
format_delta_str = "%d days %H:%M:%S"
filename_format = '%Y-%m-%d %I%M-%p'

task_table_columns = ["Task Name", 
					"Project Name", 
					"Start Date", 
					"End Date", 
					"Paused", 
					"Duration"]

command_list = ['add_running_task', 
				'add_paused_task', 
				'delete_task', 
				'end_task', 
				'list_pending_tasks', 
				'list_tasks', 
				'pause_task', 
				'start_paused_task', 
				'update_task_name', 
				'exit', 
				'export_completed_tasks', 
				'pause_all_tasks', 
				'delete_completed_tasks',
				'complete_task_manually',
				'update_project_name']

sorted_commands = sorted(command_list, key=str.lower)

def get_timestamp(format = format_date_str):
    result = datetime.now().strftime(format)
    return result

def check_date_format(date_to_test):
	try:
		datetime.strptime(date_to_test,format_date_str)
	except ValueError as err:
		return(f'{date_to_test} is not the right format. The format should be {format_date_str}')

def check_delta_format(delta_to_test):
	try:
		datetime.strptime(delta_to_test,format_delta_str)
	except ValueError as err:
		return(f'{delta_to_test} is not the right format. The format should be {delta_to_test}')

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

	output_task_table(data_list, task_table_columns)

	current_time = get_timestamp(filename_format)

	keys = data_list[0].keys()
	with open(f'{name} - Completed Tasks {current_time}.csv', 'a', newline='') as output_file:
		dict_writer = csv.DictWriter(output_file, keys)
		dict_writer.writeheader()
		dict_writer.writerows(data_list)	

def format_column_value(line, max_line_length):
    ACC_length = 0
    words = line.split(" ")
    formatted_comment = ""
    for word in words:
        if ACC_length + (len(word) + 1) <= max_line_length:
            formatted_comment = formatted_comment + word + " "
            ACC_length = ACC_length + len(word) + 1
        else:

            formatted_comment = formatted_comment + "\n" + word + " "
            ACC_length = len(word) + 1
    return formatted_comment

def output_task_table(dict_list, columns):

	cli_table = PrettyTable(hrules=ALL)
	cli_table.field_names = columns

	for task in dict_list:
		for column in columns:
			column = column.lower().replace(" ", "_")
			if type(task[column]) != bool:
				task[column] = format_column_value(task[column], max_line_length)
		cli_table.add_row([task['task_name'], task['project_name'], task['start_date'], task['end_date'], task['paused'], task['duration']])
	echo(cli_table)

def custom_print_green(value):
	return(echo(Fore.GREEN + value))

def custom_print_blue(value):
	return(echo(Fore.BLUE + value))

def custom_print_red(value):
	return(echo(Fore.RED + value))

command_completer = WordCompleter(
	sorted_commands, 
	ignore_case=True)

custom_print_blue(text2art('<< tasker >>'))
custom_print_green('Press TAB to see the list of commands.')

while 1:

	user_input = prompt(prompt_symbol, completer=command_completer, wrap_lines=False, complete_while_typing=True)

	if user_input == 'exit':

		if os.path.exists('history.txt'):
			os.remove('history.txt')
		
		custom_print_green('Goodbye.')
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
			completer=project_command_completer,
			wrap_lines=False,
			complete_while_typing=True
		)

		if task_name or task_project is '':
			custom_print_red('The Task and/or Project cannot be blank.')
		else:	
			start_time = get_timestamp()
			existing_task_names = select_column(task_table.search(where('project_name') == task_project), 'task_name')
			running_tasks = select_column(task_table.search((where('end_date') == '') & (where('paused') == False)), 'task_name')

			if task_name not in existing_task_names:

				if len(running_tasks) < number_of_concurrent_tasks:
					task_table.insert({'task_name': task_name, 'project_name': task_project, 'start_date': start_time, 'end_date': '',
					'last_restart_date': start_time, 'last_paused_date': '', 'paused': False, 'duration': '0 days 0:00:00'})
					custom_print_green(f'Task: "{task_name}" successfully started. Time: {start_time}')

					if task_project not in project_list:
						project_table.insert({'project_name': task_project, 'created_on': start_time})

				else: 
					custom_print_red('You can only have a maximum of 3 running tasks at any time. Please Pause or End existing running Tasks.')
			else:
				custom_print_red('That Task name already exists for that project. Please choose a different Task name')

	elif user_input == 'add_paused_task':

		project_list = select_column(project_table.all(), 'project_name')
		project_command_completer = WordCompleter(project_list, ignore_case=True)

		task_session = PromptSession()

		task_name = task_session.prompt(
			'Name: '
		)
		
		task_project = task_session.prompt(
			'Project: ',
			completer=project_command_completer,
			wrap_lines=False,
			complete_while_typing=True
		)

		if task_name or task_project is '':
			custom_print_red('The Task and/or Project cannot be blank.')
		else:	
			start_time = get_timestamp()
			existing_task_names = select_column(task_table.search(where('project_name') == task_project), 'task_name')

			if task_name not in existing_task_names:
				task_table.insert({'task_name': task_name, 'project_name': task_project, 'start_date': start_time, 'end_date': '',
				'last_restart_date': start_time, 'last_paused_date': start_time, 'paused': True, 'duration': '0 days 0:00:00'})

				if task_project not in project_list:
					project_table.insert({'project_name': task_project, 'created_on': start_time})

				custom_print_green(f'Task: "{task_name}" successfully started. Time: {start_time}')
			else:
				custom_print_red('That Task name already exists for that project. Please choose a different Task name')

	elif user_input == 'end_task':

		task_list = select_column(task_table.search(where('end_date') == ''), 'task_name', 'project_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()
		task_to_end = task_session.prompt('Select Started Task to End: ', completer = task_command_completer, wrap_lines=False,
		complete_while_typing=True)
		
		if task_to_end in task_list:

			current_task_project = task_to_end.split(' - ')[1]
			task_to_end = task_to_end.split(' - ')[0]

			current_time = get_timestamp()
			task_list = select_column(task_table.search(where('end_date') == ''), 'task_name')
			paused_tasks = select_column(task_table.search((where('paused') == True) & (where('project_name') == current_task_project)), 'task_name')

			current_start_time = select_column(task_table.search(where('task_name') == task_to_end), 'last_restart_date')[0]
			current_duration = select_column(task_table.search((where('task_name') == task_to_complete) & (where('project_name') == current_task_project)), 'duration')[0]

			formatted_current_time = datetime.strptime(current_time, format_date_str)
			formatted_start_date = datetime.strptime(current_start_time, format_date_str)

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
				custom_print_green(f'Task: "{task_to_end}" successfully ended. Time: {current_time}')
			else:
				if current_duration != '0 days 0:00:00':
					task_table.update({'end_date': current_time, 'paused': False}, (where('task_name') == task_to_end) & (where('project_name') == current_task_project))
					custom_print_green(f'Task: "{task_to_end}" successfully ended. Time: {current_time}')
				else:
					custom_print_red('Cannot end Task because it is paused and the duration is 0 days 0:00:00')


		else:
			custom_print_red('That Task does not exist or has ended, please try again.')
	
	elif user_input == 'delete_task':
		task_list = select_column(task_table.all(), 'task_name', 'project_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()

		task_to_delete = task_session.prompt(
			'Select Task to Delete: ',
			completer = task_command_completer,
			wrap_lines=False,
			complete_while_typing=True
		)

		if task_to_delete in task_list:

			task_list = select_column(task_table.all(), 'task_name')
			current_task_project = task_to_delete.split(' - ')[1]
			task_to_delete = task_to_delete.split(' - ')[0]

			confirm =  task_session.prompt(f'Are you sure you want to delete "{task_to_delete}" (y/n): ')

			if confirm == 'y':
					task_table.remove((where('task_name') == task_to_delete) & (where('project_name') == current_task_project) )
					custom_print_green(f'Task: "{task_to_delete}" successfully deleted.')

			elif confirm == 'n':
				custom_print_green('Deletion cancelled.')
			else:
				custom_print_red('Did not understand answer to confirmation. Please try again.')
		else:
				custom_print_red('That Task does not exist, please try again.')
	
	elif user_input == 'list_pending_tasks':
		pending_tasks =  task_table.search(where('end_date') == '')

		if len(pending_tasks) > 0:
			output_task_table(pending_tasks, task_table_columns)
		else:
			custom_print_red('There are no pending Tasks.')
	
	elif user_input == 'list_tasks':
		all_tasks =  task_table.all()
		if len(all_tasks) > 0:
			output_task_table(all_tasks, task_table_columns)
		else:
			custom_print_red('No Tasks have been added yet.')

	elif user_input == 'pause_task':
		
		task_list = select_column(task_table.search((where('end_date') == '') & (where('paused') == False)), 'task_name', 'project_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()

		task_to_pause = task_session.prompt(
			'Select Started Task to Pause: ',
			completer = task_command_completer,
			wrap_lines=False,
			complete_while_typing=True
		)

		current_time = get_timestamp()
		current_task_project = task_to_pause.split(' - ')[1]
		task_to_pause = task_to_pause.split(' - ')[0]
		task_list = select_column(task_table.search((where('end_date') == '') & (where('paused') == False)), 'task_name')

		if task_to_pause in task_list:
			current_start_time = select_column(task_table.search(where('task_name') == task_to_pause), 'last_restart_date')[0]
			current_duration = select_column(task_table.search(where('task_name') == task_to_pause), 'duration')[0]

			formatted_current_time = datetime.strptime(current_time, format_date_str)
			formatted_start_date = datetime.strptime(current_start_time, format_date_str)
			
			if 'days' in current_duration:
				days_v_hms = current_duration.split('days,')
				hms = days_v_hms[1].split(':')
			else:
				hms = current_duration.split(':')

			dt = timedelta(hours=int(hms[0]), minutes=int(hms[1]), seconds=float(hms[2]))

			diff = formatted_current_time - formatted_start_date
			paused_duration = str(dt + diff)
		
			task_table.update({'duration': paused_duration, 'last_paused_date': current_time, 'paused': True}, (where('task_name') == task_to_pause) & (where('project_name') == current_task_project))
			custom_print_green(f'Task: "{task_to_pause}" successfully paused. Time: {current_time}')
		else:
			custom_print_red('That Task does not exist or is already Paused, please try again.')

	elif user_input == 'start_paused_task':

		task_list = select_column(task_table.search((where('end_date') == '') & (where('paused') == True)), 'task_name', 'project_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()

		task_to_restart = task_session.prompt(
			'Select Paused Task to Restart: ',
			completer = task_command_completer,
			wrap_lines=False,
			complete_while_typing=True
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
					custom_print_green(f'Task: "{task_to_restart}" successfully restarted. Time: {current_time}')

				else: 
					custom_print_red('You can only have a maximum of 3 running tasks at any time. Please Pause or End existing running Tasks.')

			else:
				custom_print_red('The Task has ended. Please create a new Task.')
		else:
			custom_print_red('That Task does not exist or is not Paused, please try again.')

	elif user_input == 'update_task_name':

		task_list = select_column(task_table.all(), 'task_name', 'project_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()

		task_to_update_name = task_session.prompt(
			'Select Task to Update: ',
			completer = task_command_completer,
			wrap_lines=False,
			complete_while_typing=True
		)

		name_to_update_to = task_session.prompt(
			'Update the Task Name: ',
			completer = task_command_completer,
			wrap_lines=False,
			complete_while_typing=True,
			default = task_to_update_name.split(' - ')[0]
		).split(' - ')[0]

		task_list = select_column(task_table.all(), 'task_name')
		current_task_project = task_to_update_name.split(' - ')[1]
		task_to_update_name = task_to_update_name.split(' - ')[0]

		if task_to_update_name in task_list:
			
			existing_task_names = select_column(task_table.search(where('project_name') == current_task_project), 'task_name')
		
			if name_to_update_to not in existing_task_names:

				task_table.update({'task_name': name_to_update_to}, (where('task_name') == task_to_update_name) & (where('project_name') == current_task_project))
				custom_print_green(f'Task "{task_to_update_name}" has been updated to "{name_to_update_to}"')
			else:
				custom_print_red(f'The Task name {name_to_update_to} already exists for the project {current_task_project}. Please choose a different Task name.')			
		else:
			custom_print_red('That Task does not exist, please try again.')		

	elif user_input == 'export_completed_tasks':

		completed_tasks =  task_table.search(where('end_date') != '')

		task_session = PromptSession()

		if len(completed_tasks) > 0:
			name = task_session.prompt('Your Name (Please be consistent with previous exports): ')
			to_csv(completed_tasks, name)
			custom_print_green('Completed Tasks exported.')
		else:
			custom_print_red('There were not completed Tasks to export.')

	elif user_input == 'pause_all_tasks':
		
		task_list = select_column(task_table.search((where('end_date') == '') & (where('paused') == False)), 'task_name', 'project_name')

		if len(task_list) > 0:
			
			for task_to_pause in task_list:

				current_time = get_timestamp()
				current_task_project = task_to_pause.split(' - ')[1]
				task_to_pause = task_to_pause.split(' - ')[0]

				current_start_time = select_column(task_table.search(where('task_name') == task_to_pause), 'last_restart_date')[0]
				current_duration = select_column(task_table.search(where('task_name') == task_to_pause), 'duration')[0]

				formatted_current_time = datetime.strptime(current_time, format_date_str)
				formatted_start_date = datetime.strptime(current_start_time, format_date_str)
				
				if 'days' in current_duration:
					days_v_hms = current_duration.split('days,')
					hms = days_v_hms[1].split(':')
				else:
					hms = current_duration.split(':')

				dt = timedelta(hours=int(hms[0]), minutes=int(hms[1]), seconds=float(hms[2]))

				diff = formatted_current_time - formatted_start_date
				paused_duration = str(dt + diff)
			
				task_table.update({'duration': paused_duration, 'last_paused_date': current_time, 'paused': True}, (where('task_name') == task_to_pause) & (where('project_name') == current_task_project))
				custom_print_green(f'Task: "{task_to_pause}" successfully paused. Time: {current_time}')

		else:
			custom_print_red('There are no running Tasks to Pause.')

	elif user_input == 'delete_completed_tasks':
		
		task_list = select_column(task_table.search((where('end_date') != '') & (where('paused') == False)), 'task_name', 'project_name')
		completed_tasks =  task_table.search(where('end_date') != '')

		if len(task_list) > 0:

			task_session = PromptSession()
			confirm =  task_session.prompt(f'Are you sure you want to delete all tasks? You will be forced to export before deleting. (y/n): ')

			if confirm == 'y':

				name = task_session.prompt('Your Name (Please be consistent with previous exports): ')

				if len(completed_tasks) > 0:
					to_csv(completed_tasks, name)
					custom_print_green('Completed Tasks exported.')
				else:
					custom_print_red('There were not completed Tasks to export.')


				for task_to_delete in task_list:

					current_task_project = task_to_delete.split(' - ')[1]
					task_to_delete = task_to_delete.split(' - ')[0]
			
					task_table.remove((where('task_name') == task_to_delete) & (where('project_name') == current_task_project) )
					custom_print_green(f'Task: "{task_to_delete}" successfully deleted.')


			elif confirm == 'n':

				custom_print_red('Deletion cancelled.')

			else:

				custom_print_red('Did not understand answer to confirmation. Please try again.')
		else:

			custom_print_red('There are no completed tasks to remove.')

	elif user_input == 'complete_task_manually':

		task_list = select_column(task_table.search(where('end_date') == ''), 'task_name', 'project_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()
		task_to_complete = task_session.prompt('Select Started Task to Complete: ', 
					completer = task_command_completer, 
					wrap_lines=False, 
					complete_while_typing=True)

		current_time = get_timestamp()
		
		if task_to_complete in task_list:

			current_task_project = task_to_complete.split(' - ')[1]
			task_to_complete = task_to_complete.split(' - ')[0]

			start_time = select_column(task_table.search((where('task_name') == task_to_complete) & (where('project_name') == current_task_project)), 'start_date')[0]
			task_list = select_column(task_table.search(where('end_date') == ''), 'task_name')
			paused_tasks = select_column(task_table.search((where('paused') == True) & (where('project_name') == current_task_project)), 'task_name')
			current_duration = select_column(task_table.search((where('task_name') == task_to_complete) & (where('project_name') == current_task_project)), 'duration')[0]

			if task_to_complete in paused_tasks:

				start_time = task_session.prompt('Do you want to update the start time? (Press ENTER for default) ', wrap_lines=False, default=str(start_time))
				end_time = task_session.prompt('When was the Task completed? (Press ENTER for default) ', wrap_lines=False, default=str(current_time))
				task_duration = task_session.prompt('How long did it take to complete? ', wrap_lines=False, default='0 days 0:00:00')

				start_time_check = check_date_format(start_time)
				end_time_check = check_date_format(end_time)
				task_duration_check = check_delta_format(task_duration)


				if (start_time_check or end_time_check or task_duration_check != None):
					if task_duration != '0 days 0:00:00':
						
							task_table.update({'start_date': start_time,'duration': task_duration, 'end_date': end_time, 'paused': False}, (where('task_name') == task_to_complete) & (where('project_name') == current_task_project))
							custom_print_green(f'Task: "{task_to_complete}" successfully completed. Time: {end_time}')
						
					else:
						custom_print_red('The duration cannot be 0 days 0:00:00.')
				else:
					custom_print_red(start_time_check)
					custom_print_red(end_time_check)
					custom_print_red(task_duration_check)
			else:
						custom_print_red('This Task is currently not paused. Please pause the Task first to complete manually.')
		else:
			custom_print_red('That Task does not exist or has been completed, please try again.')
	
	elif user_input == 'update_project_name':

		project_list = select_column(project_table.all(), 'project_name')
		project_command_completer = WordCompleter(project_list, ignore_case=True)

		task_session = PromptSession()

		project_name_to_update = task_session.prompt(
			'Select Project Name to Update: ',
			completer = project_command_completer,
			wrap_lines = False,
			complete_while_typing=True
		)

		if project_name_to_update in project_list:

			project_name_to_update_to = task_session.prompt(
				'Update the Project Name: ',
				completer = project_command_completer,
				wrap_lines=False,
				complete_while_typing=True,
				default = project_name_to_update
			)

			task_list = select_column(task_table.search(where('project_name') == project_name_to_update), 'task_name')
		
			for task in task_list:
				task_table.update({'project_name': project_name_to_update_to}, (where('task_name') == task) & (where('project_name') == project_name_to_update))
				project_table.update({'project_name': project_name_to_update_to}, where('project_name') == project_name_to_update)
			
			custom_print_green(f'Project "{project_name_to_update}" has been successfully updated to "{project_name_to_update_to}"')		
		else:
			custom_print_red('That Project does not exist, please try again.')		


	else:
		custom_print_red('Not a valid command. Press TAB to view list of possible commands.')
