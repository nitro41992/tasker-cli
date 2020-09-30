import csv
import os
import time
from datetime import datetime, timedelta
import pandas as pd

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
import asyncio
import selectors

selector = selectors.SelectSelector()
loop = asyncio.SelectorEventLoop(selector)
asyncio.set_event_loop(loop)

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


hcis_codes = {'175015' : 'Non grant related expenses',
'175038' : 'Realytics services for NJII clients',
'380D17' : 'Do not use this index',
'382F21' : '2016 and 2017 program onboarding',
'382F22' : '2017 Onboarding Milestone program',
'382F23' : 'NJIIS',
'382F24' : 'emPOLST project',
'382F25' : 'Consumer access project',
'382F26' : 'Consent management project',
'382F27' : '2016 Onboarding Milestone program',
'382F28' : 'Perinatal Risk Assessment or PRA registry proejct',
'382F29' : 'MPP program (Core index)',
'382F30' : 'MPP program (Milestone index)',
'382M01' : 'NJHIN management (please do not use this unless indicated by Jen)',
'382M02' : 'SUD program (Core index)',
'382M03' : 'SUD program (Milestone index)',
'382M04' : 'Lead registry project',
'382M05' : 'Contact tracing (CDRSS project)',
'104000' : 'HCIS non service line related index for NJII employees',
'104010' : 'MIPS index for NJII employees',
'104040' : 'DSRIP index for NJII employees',
'104050' : 'Aetna index for NJII employees',
'104060' : 'Relytics index for NJII employees'}

hcis_codes = pd.DataFrame(hcis_codes.items(), columns = ['Index', 'Description']) 
project_list = hcis_codes['Description'] + ': ' + hcis_codes['Index']
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
command_list = ['add_running_task', 
				'add_paused_task', 
				'delete_task', 
				'end_task', 
				'list_pending_tasks', 
				'list_all_tasks', 
				'pause_task', 
				'start_paused_task', 
				'update_task_name', 
				'exit', 
				'export_completed_tasks', 
				'pause_all_tasks', 
				'delete_completed_tasks',
				'complete_task_manually',
				'timesheet_report'
				# 'update_project_name'
				]
sorted_commands = sorted(command_list, key=str.lower)


def convert_to_timedelta(value):
	value = str(value)
	if 'days' in value:
		days_v_hms = value.split('days')
		hms = days_v_hms[1].split(':')
		dt = timedelta(days=int(days_v_hms[0]), hours=int(hms[0]), minutes=int(hms[1]), seconds=float(hms[2]))
	elif 'day' in value:
		days_v_hms = value.split('day')
		hms = days_v_hms[1].split(':')
		dt = timedelta(days=int(days_v_hms[0]), hours=int(hms[0]), minutes=int(hms[1]), seconds=float(hms[2]))
	else:	
		hms = value.split(':')
		dt = timedelta(hours=int(hms[0]), minutes=int(hms[1]), seconds=float(hms[2]))
	return(dt)

def get_running_duration(restart_datetime, current_duration, is_paused, is_ended):

	if (is_paused == False) and (is_ended.strip() == ''):
		current_time = get_timestamp()
		
		formatted_current_time = datetime.strptime(current_time, format_date_str)
		formatted_start_date = datetime.strptime(restart_datetime.strip(), format_date_str)

		dt = convert_to_timedelta(current_duration)

		diff = formatted_current_time - formatted_start_date
		paused_duration = str(dt + diff)

		return(paused_duration)

	else:

		return(current_duration)

def get_timestamp(format = format_date_str):
    result = datetime.now().strftime(format)
    return result

def check_date_format(date_to_test):
	try:
		datetime.strptime(date_to_test,format_date_str)
	except:
		return(f'{date_to_test} is not the right format. The format should be {format_date_str}')

def check_delta_format(delta_to_test):
	try:
		convert_to_timedelta(delta_to_test)
	except ValueError as error:
		return(str(error)) #f'{delta_to_test} is not the right format. The format should be {format_delta_str_hours}')

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

def get_where_clauses(clauses):
	where_clauses = ''
	for key, value in clauses.items():
		if type(value[1]) != bool:
			clause = f"(where('{key}') {value[0]} '{value[1]}')"
			where_clauses = where_clauses + clause + ' '
		else:
			clause = f"(where('{key}') {value[0]} {value[1]})"
			where_clauses = where_clauses + clause + ' '
	where_clauses = where_clauses.strip().replace(') (', ') & (')
	return(where_clauses)

def get_table_values(table, clauses, return_type, column1 = '', column2 = ''):
	if clauses != None:
		where_clauses = get_where_clauses(clauses)
	if return_type == 'column':
		if clauses != None:
			total_query = f"select_column({table}.search({where_clauses}), '{column1}', '{column2}')"
		else:
			total_query = f"select_column({table}.all(), '{column1}', '{column2}')"
		return(eval(total_query))
	elif return_type == 'value':
		total_query = f"select_column({table}.search({where_clauses}), '{column1}', '{column2}')[0]"
		return(eval(total_query))
	elif return_type == 'rows':
		total_query = f"{table}.search({where_clauses})"
		print(total_query)
		return(eval(total_query))

def to_csv(data_list, name):

	output_task_table(data_list, task_table_columns)

	current_time = get_timestamp(filename_format)

	keys = data_list[0].keys()
	with open(f'{name} - Completed Tasks {current_time} Export.csv', 'a', newline='') as output_file:
		dict_writer = csv.DictWriter(output_file, keys)
		dict_writer.writeheader()
		dict_writer.writerows(data_list)	

def format_column_value(line, max_line_length):
    ACC_length = 0
    if '\n' not in line:
        words = line.split(" ")
        formatted_line = ""
        for word in words:
            if ACC_length + (len(word) + 1) <= max_line_length:
                formatted_line = formatted_line + word + " "
                ACC_length = ACC_length + len(word) + 1
            else:
                formatted_line = formatted_line + "\n" + word + " "
                ACC_length = len(word) + 1
        return(formatted_line)
    else:
        return(line.strip())

def output_task_table(dict_list, columns):

	cli_table = PrettyTable(hrules=ALL)
	cli_table.field_names = columns

	for task in dict_list:
		for column in columns:
			column = column.lower().replace(" ", "_")
			if type(task[column]) != bool:
				task[column] = format_column_value(task[column], max_line_length).strip()
		running_duration = get_running_duration(task['last_restart_date'], task['duration'], task['paused'], task['end_date'])
		cli_table.add_row([
			task['task_name'], 
			task['project_name'],
			task['start_date'], 
			task['end_date'], 
			task['last_restart_date'], 
			task['last_paused_date'], 
			task['paused'], 
			running_duration])
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
custom_print_blue('''
tasker is a simple tool to track your daily/weekly tasks and export them as needed.
You can add running tasks and start tracking the time right away or add paused tasks you can start later.
Simply add a task and what project it belongs to. tasker will add it to your task list.
Pause a task, or all tasks, and restar them later. tasker will aggregate total duration.
End the task completely to let tasker know you are done with the task and it is ready to be exported.

Press TAB to and scroll through to see the list of commands.
''')

while 1:

	user_input = prompt(prompt_symbol, completer=command_completer, wrap_lines=False, complete_while_typing=True, style=style)

	if user_input == 'exit':

		if os.path.exists('history.txt'):
			os.remove('history.txt')
		
		custom_print_green('Goodbye.')
		break

	elif user_input == 'add_running_task':
		


		# project_list = get_table_values('project_table', None, 'column', 'project_name')
		# project_list = hcis_codes['(Fund/Index)      RAD Id']
		project_command_completer = FuzzyCompleter(WordCompleter(project_list, ignore_case=True))

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

		if task_name == '' or task_project == '':
			custom_print_red('The Task and/or Project cannot be blank.')
		else:	
			start_time = get_timestamp()

			# existing_task_names = select_column(task_table.search(where('project_name') == task_project), 'task_name')
			project_clause = {'project_name': ('==', task_project)}
			existing_task_names = get_table_values('task_table', project_clause, 'column', 'task_name')

			# running_tasks = select_column(task_table.search((where('end_date') == '') & (where('paused') == False)), 'task_name')
			running_clause = {'end_date': ('==', ''), 'paused': ('==', False)}
			running_tasks = get_table_values('task_table', running_clause, 'column', 'task_name')

			if task_name not in existing_task_names:

				if len(running_tasks) < number_of_concurrent_tasks:

					task_table.insert({
						'task_name': task_name, 
						'project_name': task_project, 
						'start_date': start_time, 
						'end_date': '',
						'last_restart_date': start_time, 
						'last_paused_date': '', 
						'paused': False, 
						'duration': zero_delta})

					custom_print_green(f'Task: "{task_name}" successfully started. Time: {start_time}')

					if task_project not in project_list:
						
						project_table.insert({
							'project_name': task_project, 
							'created_on': start_time})

				else: 
					custom_print_red('You can only have a maximum of 3 running tasks at any time. Please Pause or End existing running Tasks.')
			else:
				custom_print_red('That Task name already exists for that project. Please choose a different Task name')

	elif user_input == 'add_paused_task':
		
		# project_list = get_table_values('project_table', None, 'column', 'project_name')
		# project_list = hcis_codes['(Fund/Index)      RAD Id']
		project_command_completer = FuzzyCompleter(WordCompleter(project_list, ignore_case=True))

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

		if task_name == '' or task_project == '':
			custom_print_red('The Task and/or Project cannot be blank.')
		else:	
			start_time = get_timestamp()
			# existing_task_names = select_column(task_table.search(where('project_name') == task_project), 'task_name')
			project_clause = {'project_name': ('==', task_project)}
			existing_task_names = get_table_values('task_table', project_clause, 'column', 'task_name')

			if task_name not in existing_task_names:
				task_table.insert({'task_name': task_name, 'project_name': task_project, 'start_date': start_time, 'end_date': '',
				'last_restart_date': start_time, 'last_paused_date': start_time, 'paused': True, 'duration': zero_delta})

				if task_project not in project_list:
					project_table.insert({'project_name': task_project, 'created_on': start_time})

				custom_print_green(f'Task: "{task_name}" successfully started. Time: {start_time}')
			else:
				custom_print_red('That Task name already exists for that project. Please choose a different Task name')

	elif user_input == 'end_task':
		
		# task_list = select_column(task_table.search(where('end_date') == ''), 'task_name', 'project_name')
		running_clause = {'end_date': ('==', ''), 'paused': ('==', False)}
		task_list = get_table_values('task_table', running_clause, 'column', 'task_name', 'project_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()
		task_to_end = task_session.prompt('Select Started Task to End: ', completer = task_command_completer, wrap_lines=False,
		complete_while_typing=True)
		
		if task_to_end in task_list:
			
			current_task_project = task_to_end.split(' - ')[1]
			task_to_end = task_to_end.split(' - ')[0]

			current_time = get_timestamp()

			# paused_tasks = select_column(task_table.search((where('paused') == True) & (where('project_name') == current_task_project)), 'task_name')
			running_tasks_by_project = {'end_date': ('==', ''), 'project_name': ('==', current_task_project)}
			paused_tasks = get_table_values('task_table', running_tasks_by_project, 'column', 'task_name')

			
			# current_start_time = select_column(task_table.search(where('task_name') == task_to_end), 'last_restart_date')[0]
			# current_duration = select_column(task_table.search((where('task_name') == task_to_end) & (where('project_name') == current_task_project)), 'duration')[0]
			unique_clause = {'task_name': ('==', task_to_end), 'project_name': ('==', current_task_project)}
			current_start_time = get_table_values('task_table', unique_clause, 'value', 'last_restart_date')
			current_duration = get_table_values('task_table', unique_clause, 'value', 'duration')

			formatted_current_time = datetime.strptime(current_time, format_date_str)
			formatted_start_date = datetime.strptime(current_start_time, format_date_str)

			dt = convert_to_timedelta(current_duration)

			diff = formatted_current_time - formatted_start_date
			total_duration = str(dt + diff)

			running_duration = get_running_duration(current_start_time, current_duration, False, '')

			if task_to_end not in paused_tasks:
				task_table.update({'duration': total_duration, 'end_date': current_time, 'paused': False}, (where('task_name') == task_to_end) & (where('project_name') == current_task_project))
				custom_print_green(f'Task: "{task_to_end}" successfully ended. Time: {current_time}')
			else:
				if running_duration != zero_delta:
					task_table.update({'duration': running_duration, 'end_date': current_time, 'paused': False}, (where('task_name') == task_to_end) & (where('project_name') == current_task_project))
					custom_print_green(f'Task: "{task_to_end}" successfully ended. Time: {current_time}')
				else:
					custom_print_red('Cannot end Task because it is paused and the duration is 0 days 0:00:00')


		else:
			custom_print_red('That Task does not exist or has ended, please try again.')
	
	elif user_input == 'delete_task':
		
		# task_list = select_column(task_table.all(), 'task_name', 'project_name')
		task_list = get_table_values('task_table', None, 'column', 'task_name', 'project_name')
		task_command_completer = WordCompleter(task_list, ignore_case=True)

		task_session = PromptSession()

		task_to_delete = task_session.prompt(
			'Select Task to Delete: ',
			completer = task_command_completer,
			wrap_lines=False,
			complete_while_typing=True
		)

		if task_to_delete in task_list:

			# task_list = select_column(task_table.all(), 'task_name')
			current_task_project = task_to_delete.split(' - ')[1]
			task_to_delete = task_to_delete.split(' - ')[0]

			confirm =  task_session.prompt(f'Are you sure you want to delete "{task_to_delete}" (y/n): ')

			if confirm == 'y':
					task_table.remove((where('task_name') == task_to_delete) & (where('project_name') == current_task_project))
					custom_print_green(f'Task: "{task_to_delete}" successfully deleted.')

					# project_list = select_column(task_table.search(where('project_name') == current_task_project), 'project_name')
					any_project_clause = {'project_name': ('==', current_task_project)}
					task_list = get_table_values('task_table', any_project_clause, 'column', 'project_name')

					if len(project_list) == 0:
						project_table.remove((where('project_name') == current_task_project) )

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
	
	elif user_input == 'list_all_tasks':
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
		
		if task_to_pause in task_list:

			current_time = get_timestamp()
			current_task_project = task_to_pause.split(' - ')[1]
			task_to_pause = task_to_pause.split(' - ')[0]
			task_list = select_column(task_table.search((where('end_date') == '') & (where('paused') == False)), 'task_name')

			current_start_time = select_column(task_table.search((where('task_name') == task_to_pause) & (where('project_name') == current_task_project)), 'last_restart_date')[0]
			current_duration = select_column(task_table.search((where('task_name') == task_to_pause) & (where('project_name') == current_task_project)), 'duration')[0]

			formatted_current_time = datetime.strptime(current_time, format_date_str)
			formatted_start_date = datetime.strptime(current_start_time, format_date_str)
			
			dt = convert_to_timedelta(current_duration)

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

		if task_to_restart in task_list:

			current_task_project = task_to_restart.split(' - ')[1]
			task_to_restart = task_to_restart.split(' - ')[0]

			current_time = get_timestamp()
			task_list = select_column(task_table.search((where('end_date') == '') & (where('paused') == True)), 'task_name')
			running_tasks = select_column(task_table.search((where('end_date') == '') & (where('paused') == False)), 'task_name')


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

		if task_to_update_name in task_list:

			task_list = select_column(task_table.all(), 'task_name')
			current_task_project = task_to_update_name.split(' - ')[1]
			task_to_update_name = task_to_update_name.split(' - ')[0]

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
		name_list = select_column(name_table.all(), 'name')
		name_command_completer = WordCompleter(name_list, ignore_case=True)

		if len(completed_tasks) > 0:
			name = task_session.prompt('Your Name (Please be consistent with previous exports): ', completer=name_command_completer,)
			to_csv(completed_tasks, name)
			custom_print_green('Completed Tasks exported.')

			if name not in name_list:
				name_table.insert({'name': name, 'created_on': get_timestamp()})
			
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
				
				dt = convert_to_timedelta(current_duration)

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

				name_list = select_column(name_table.all(), 'name')
				name_command_completer = WordCompleter(name_list, ignore_case=True)

				if len(completed_tasks) > 0:
					name = task_session.prompt('Your Name (Please be consistent with previous exports): ', completer=name_command_completer,)
					to_csv(completed_tasks, name)
					custom_print_green('Completed Tasks exported.')

					if name not in name_list:
						name_table.insert({'name': name, 'created_on': get_timestamp()})
					
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

		
		if task_to_complete in task_list:

			current_time = get_timestamp()

			current_task_project = task_to_complete.split(' - ')[1]
			task_to_complete = task_to_complete.split(' - ')[0]

			start_time = select_column(task_table.search((where('task_name') == task_to_complete) & (where('project_name') == current_task_project)), 'start_date')[0]
			task_list = select_column(task_table.search(where('end_date') == ''), 'task_name')
			paused_tasks = select_column(task_table.search((where('paused') == True) & (where('project_name') == current_task_project)), 'task_name')
			current_duration = select_column(task_table.search((where('task_name') == task_to_complete) & (where('project_name') == current_task_project)), 'duration')[0]

			if task_to_complete in paused_tasks:

				start_time = task_session.prompt('Do you want to update the start time? (Press ENTER for default) ', wrap_lines=False, default=str(start_time))
				end_time = task_session.prompt('When was the Task completed? (Press ENTER for default) ', wrap_lines=False, default=str(current_time))
				task_duration = task_session.prompt('How long did it take to complete? ', wrap_lines=False, default=zero_delta)

				start_time_check = check_date_format(start_time)
				end_time_check = check_date_format(end_time)
				task_duration_check = check_delta_format(task_duration)

				if (start_time_check == None) and (end_time_check == None) and (task_duration_check == None):
					if task_duration != zero_delta:
						task_table.update({'start_date': start_time,'duration': task_duration, 'end_date': end_time, 'paused': False}, (where('task_name') == task_to_complete) & (where('project_name') == current_task_project))
						custom_print_green(f'Task: "{task_to_complete}" successfully completed. Time: {end_time}')
					else:
						custom_print_red('The duration cannot be 0 days 0:00:00.')
				else:
					if start_time_check != None:
						custom_print_red(start_time_check)
					if end_time_check != None:
						custom_print_red(end_time_check)
					if task_duration_check != None:
						custom_print_red(task_duration_check)
			else:
						custom_print_red('This Task is currently not paused. Please pause the Task first to complete manually.')
		else:
			custom_print_red('That Task does not exist or has been completed, please try again.')
	
	elif user_input == 'timesheet_report':
		
		task_session = PromptSession()
		timesheet_duration = task_session.prompt(
			'Enter number of hours for timesheet calculation: ',
			wrap_lines=False,
			complete_while_typing=True,
			default = '70'
		)

		if timesheet_duration and timesheet_duration.isnumeric():
			timesheet_report = pd.DataFrame()
			tasks = pd.DataFrame(task_table.all())

			timesheet_report['task_name'] = tasks['task_name']
			timesheet_report['project_name'] = tasks['project_name']
			timesheet_report['duration'] = tasks['duration']

			total_duration = pd.to_timedelta(tasks['duration']).sum()
			proportions = (pd.to_timedelta(tasks['duration']) / total_duration)

			timesheet_report['percentages'] = round(proportions * 100, 2)
			timesheet_report['timesheet_hours'] = round(proportions * int(timesheet_duration), 0)

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
		else:
			custom_print_red('Please enter a valid duration (in hours) for timesheet calculation.')



	# elif user_input == 'update_project_name':

	# 	# project_list = select_column(project_table.all(), 'project_name')
	# 	project_command_completer = FuzzyCompleter(WordCompleter(project_list, ignore_case=True))

	# 	task_session = PromptSession()

	# 	project_name_to_update = task_session.prompt(
	# 		'Select Project Name to Update: ',
	# 		completer = project_command_completer,
	# 		wrap_lines = False,
	# 		complete_while_typing=True
	# 	)

	# 	if project_name_to_update in project_list:

	# 		project_name_to_update_to = task_session.prompt(
	# 			'Update the Project Name: ',
	# 			completer = project_command_completer,
	# 			wrap_lines=False,
	# 			complete_while_typing=True,
	# 			default = project_name_to_update
	# 		)

	# 		task_list = select_column(task_table.search(where('project_name') == project_name_to_update), 'task_name')
		
	# 		for task in task_list:
	# 			task_table.update({'project_name': project_name_to_update_to}, (where('task_name') == task) & (where('project_name') == project_name_to_update))
	# 			project_table.update({'project_name': project_name_to_update_to}, where('project_name') == project_name_to_update)
			
	# 		custom_print_green(f'Project "{project_name_to_update}" has been successfully updated to "{project_name_to_update_to}"')		
	# 	else:
	# 		custom_print_red('That Project does not exist, please try again.')		

	else:
		custom_print_red('Not a valid command. Press TAB to view list of possible commands.')
