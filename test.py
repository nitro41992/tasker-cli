from datetime import datetime

a = 'Thursday, 16 Apr 2020 06:47:42 PM'
b = 'Thursday, 16 Apr 2020 08:37:00 PM'


format_str = "%A, %d %b %Y %I:%M:%S %p"
a = datetime.strptime(a, format_str)
b = datetime.strptime(b, format_str)

print(b - a)