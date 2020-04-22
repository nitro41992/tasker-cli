import os
from tinydb import Query, TinyDB, where
from tinydb.operations import delete

dirname = os.path.dirname(__file__)
datafile = os.path.join(dirname, 'db.json')
db = TinyDB(datafile)
task_table = db.table('tasks')

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
	# print(clauses)
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
		# print(total_query)
		return(eval(total_query))


# clauses = {'end_date': ('==', ''), 'paused': ('==', False)}
# print(get_table_values('task_table', clauses, 'column', 'task_name', 'project_name'))
# # select_column(task_table.search((where('end_date') == '') & (where('paused') == False)), 'task_name', 'project_name')

# task_to_end = 'Test 3'
# current_task_project = 'Test'
# clauses = {'task_name': ('==', task_to_end), 'project_name': ('==', current_task_project)}
# print(get_table_values('task_table', clauses, 'value', 'duration'))
# # current_duration = select_column(task_table.search((where('task_name') == task_to_end) & (where('project_name') == current_task_project)), 'duration')[0]

# clauses = {'end_date': ('!=', '')}
# print(get_table_values('task_table', clauses, 'rows'))
# # completed_tasks =  task_table.search(where('end_date') != '')


# print(get_table_values('task_table', None, 'column', 'task_name'))
# # task_list = select_column(task_table.all(), 'task_name')

# clauses = {'end_date': ('==', '')}
# print(get_table_values('task_table', clauses, 'column', 'task_name'))
# # task_list = select_column(task_table.search(where('end_date') == ''), 'task_name')

# task_project = 'Test'
# project_clause = {'project_name': ('==', task_project)}
# existing_task_names = get_table_values('task_table', project_clause, 'column', 'task_name')


task_to_end = 'New Running Test'
current_task_project = 'Test'
unique_clause = {'task_name': ('==', task_to_end), 'project_name': ('==', current_task_project)}
current_duration = get_table_values('task_table', unique_clause, 'value', 'duration')
print(current_duration)


running_tasks_by_project = {'end_date': ('==', ''), 'project_name': ('==', current_task_project)}
paused_tasks = get_table_values('task_table', running_tasks_by_project, 'column', 'task_name')
print(paused_tasks)