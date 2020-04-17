from datetime import datetime, timedelta

format_str = "%A, %d %b %Y %I:%M:%S %p"

def get_timestamp():
    result = datetime.now().strftime(format_str)
    return result

a = 'Thursday, 13 Apr 2020 06:47:42 PM'
b = get_timestamp()

a = datetime.strptime(a, format_str)
b = datetime.strptime(b, format_str)

stringdate = "0 days, 0:00:00"
days_v_hms = stringdate.split('days,')
hms = days_v_hms[1].split(':')
dt = timedelta(hours=int(hms[0]), minutes=int(hms[1]), seconds=float(hms[2]))

c = b - a
print(c)
d = c + dt
print(d)

