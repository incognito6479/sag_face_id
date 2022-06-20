from faceapp.models import Employee, Attendance, CalendarWorkingDays, EmployeeVacation, CsvImporter, \
    EmployeeBusinessTrip, Department, DepartmentShiftTime, DepartmentStatistics, EmployeeStatisticsAttendance, \
    EmployeeStatisticsWorkingHours
from system.settings import SERVER_TIME_DIFFERENCE
import csv
import pytz
from datetime import datetime
from calendar import monthrange, monthcalendar

utc = pytz.UTC


def get_statistics_employee_attendance():
    employees = Employee.objects.select_related('working_hours').filter(status=True)
    employee_percentage_id = {}
    current_month = datetime.now().month - 1
    for employee in employees:
        working_hours = employee.working_hours.end_time.hour - employee.working_hours.start_time.hour
        res = get_attendance_percentage_employee(employee.id)
        days_must_work = res['hours_needed_to_work'][current_month]
        overall_percentage = days_must_work // working_hours
        attendances = res['attendances'].filter(time__month=current_month)
        if str(res['employee_id']) == str(employee.id):
            overall_percentage -= overall_percentage - \
                                  (res['employee_worked_hours'][current_month] // working_hours)
            for attendance in attendances:
                if attendance.check_status == "checkIn":
                    check_start_time = find_start_time_difference(working_hours, attendance)
                    if check_start_time:
                        overall_percentage -= 0.5
                else:
                    check_end_time = find_end_time_difference(working_hours, attendance)
                    if check_end_time:
                        overall_percentage -= 0.5
        employee_percentage_id[employee.id] = int((overall_percentage * 100) // (days_must_work // working_hours))
    # print(employee_percentage_id)
    return employee_percentage_id


def dry_function(objects):
    custom_dict = {}
    for i in objects:
        if i.date_from.month in custom_dict:
            if i.difference >= 7:
                i.difference = (i.difference - (i.difference % 7))
            custom_dict[i.date_from.month] += i.difference
        else:
            if i.date_from.month < i.date_to.month:
                a = monthrange(datetime.now().year, i.date_from.month)[1] - i.date_from.day
                if a >= 7:
                    a = (a - (a % 7))
                custom_dict[i.date_from.month] = a
                b = i.difference - (monthrange(datetime.now().year, i.date_from.month)[1] - i.date_from.day)
                if b >= 7:
                    b = (b - (b % 7))
                custom_dict[i.date_from.month + 1] = b
            else:
                if i.difference >= 7:
                    i.difference = (i.difference - (i.difference % 7))
                custom_dict[i.date_from.month] = i.difference
    return custom_dict


def get_number_of_holidays_in_month(holidays):
    return dry_function(holidays)


def get_number_of_vacations_in_month(vacations, employee_id):
    return dry_function(vacations.filter(employee_id=employee_id))


def get_number_of_business_trips_in_month(business_trips, employee_id):
    return dry_function(business_trips.filter(employee_id=employee_id))


def get_attendance_percentage_employee(employee_id):
    holidays = CalendarWorkingDays.objects.filter(date_from__year=datetime.now().year)
    business_trips = EmployeeBusinessTrip.objects.filter(date_from__year=datetime.now().year)
    vacations = EmployeeVacation.objects.filter(date_from__year=datetime.now().year)
    employee_obj = Employee.objects.filter(id=employee_id).select_related('working_hours').first()
    working_hours = employee_obj.working_hours.end_time.hour - employee_obj.working_hours.start_time.hour
    attendances = Attendance.objects.filter(user_id=employee_id, time__year=datetime.now().year).order_by('time')
    hours_needed_to_work_in_month = {}
    number_of_holidays_in_month = get_number_of_holidays_in_month(holidays)
    number_of_vacations_in_month = get_number_of_vacations_in_month(vacations, employee_id)
    number_of_business_trips_in_month = get_number_of_business_trips_in_month(business_trips, employee_id)
    employee_worked_hours = {}
    percent = {}
    for i in range(1, 13):
        hours_needed_to_work_in_month[i] = monthrange(datetime.now().year, i)[1] \
                                           - len([1 for i in monthcalendar(datetime.now().year, i) if i[6] != 0])
    for key, value in number_of_business_trips_in_month.items():
        hours_needed_to_work_in_month[key] -= value
    for key, value in number_of_vacations_in_month.items():
        hours_needed_to_work_in_month[key] -= value
    for key, value in number_of_holidays_in_month.items():
        hours_needed_to_work_in_month[key] -= value
    for key, value in hours_needed_to_work_in_month.items():
        hours_needed_to_work_in_month[key] = value * working_hours
    for key, value in hours_needed_to_work_in_month.items():
        if value < 0:
            hours_needed_to_work_in_month[key] = 0
    for i in range(1, 13):
        number_of_days_in_month = monthrange(datetime.now().year, i)[1]
        for day in range(1, number_of_days_in_month + 1):
            a = attendances.filter(time__month=i, time__day=day)
            check_in_hour = 0
            check_out_hour = 0
            for obj in a:
                if obj.check_status == "checkIn":
                    check_in_hour = obj.time.hour
                else:
                    check_out_hour = obj.time.hour
            if i in employee_worked_hours:
                employee_worked_hours[i] += check_out_hour - check_in_hour
            else:
                employee_worked_hours[i] = check_out_hour - check_in_hour
    for key, value in hours_needed_to_work_in_month.items():
        if value != 0:
            percent[key] = (employee_worked_hours[key] * 100) // value
        else:
            percent[key] = 0
    res = {
        'percent': percent,
        'employee_worked_hours': employee_worked_hours,
        'hours_needed_to_work': hours_needed_to_work_in_month,
        'attendances': attendances,
        'employee_id': employee_id
    }
    # print(employee_worked_hours)
    return res


def get_attendance_percentage_department(department_id):
    employee_obj = Employee.objects.filter(status=True, department_id=department_id)
    all_employee_worked_hours = {}
    all_employee_worked_hours_needed = {}
    percentage = {}
    for i in employee_obj:
        resp = get_attendance_percentage_employee(i.id)
        for key, value in resp['employee_worked_hours'].items():
            if key in all_employee_worked_hours:
                all_employee_worked_hours[key] += value
            else:
                all_employee_worked_hours[key] = value
        for key, value in resp['hours_needed_to_work'].items():
            if key in all_employee_worked_hours_needed:
                all_employee_worked_hours_needed[key] += value
            else:
                all_employee_worked_hours_needed[key] = value
    for key, value in all_employee_worked_hours_needed.items():
        percentage[key] = (all_employee_worked_hours[key] * 100) // value
    return percentage


def get_employee_detail_attendances(attendances, object):
    queryset = {}
    for attendance in attendances:
        if int(object.person_id) + attendance.time.day not in queryset:
            queryset[int(object.person_id) + attendance.time.day] = [{
                'full_name': f"{object.last_name} {object.first_name} {object.middle_name}",
                'check_status': attendance.get_check_status_display(),
                'time': attendance.time,
                'person_id': object.person_id,
                'start_time_difference': find_start_time_difference(object.working_hours.start_time.hour, attendance),
                'end_time_difference': find_end_time_difference(object.working_hours.end_time.hour, attendance)
            }]
        else:
            queryset[int(object.person_id) + attendance.time.day].append({
                'full_name': f"{object.last_name} {object.first_name} {object.middle_name}",
                'check_status': attendance.get_check_status_display(),
                'time': attendance.time,
                'person_id': object.person_id,
                'start_time_difference': find_start_time_difference(object.working_hours.start_time.hour, attendance),
                'end_time_difference': find_end_time_difference(object.working_hours.end_time.hour, attendance)
            })
    return queryset


def get_all_employees_attendances(attendances, users):
    queryset = {}
    attendance_user_id = []
    for user in users:
        for attendance in attendances:
            attendance_user_id.append(attendance.user_id) if attendance.user_id not in attendance_user_id else ""
            if attendance.user.person_id == user.person_id:
                if user.person_id not in queryset:
                    queryset[user.person_id] = [{
                        'full_name': f"{user.last_name} {user.first_name} {user.middle_name}",
                        'employee_id': user.id,
                        'check_status': attendance.get_check_status_display(),
                        'time': attendance.time,
                        'department': user.department,
                        'img': user.image,
                        'start_time_difference': find_start_time_difference(user.working_hours.start_time.hour,
                                                                            attendance),
                        'end_time_difference': find_end_time_difference(user.working_hours.end_time.hour, attendance)
                    }]
                else:
                    queryset[user.person_id].append({
                        'full_name': f"{user.last_name} {user.first_name} {user.middle_name}",
                        'employee_id': user.id,
                        'check_status': attendance.get_check_status_display(),
                        'time': attendance.time,
                        'department': user.department,
                        'img': user.image,
                        'start_time_difference': find_start_time_difference(user.working_hours.start_time.hour,
                                                                            attendance),
                        'end_time_difference': find_end_time_difference(user.working_hours.end_time.hour, attendance)
                    })
        if user.id not in attendance_user_id:
            queryset[user.person_id] = [{
                'full_name': f"{user.last_name} {user.first_name} {user.middle_name}",
                'employee_id': user.id,
                'check_status': "---",
                'time': "---",
                'department': user.department,
                'img': user.image,
                'start_time_difference': 1,
                'end_time_difference': 1,
            }]
    return queryset


def find_end_time_difference(user_working_hour, attendance_time):
    if attendance_time.time.hour + SERVER_TIME_DIFFERENCE == user_working_hour - 1 and attendance_time.time.minute >= 50:
        return 0
    if attendance_time.time.hour + SERVER_TIME_DIFFERENCE > user_working_hour:
        return 0
    difference = user_working_hour - (attendance_time.time.hour + SERVER_TIME_DIFFERENCE)
    return difference


def find_start_time_difference(user_working_hour, attendance_time):
    if user_working_hour == SERVER_TIME_DIFFERENCE + attendance_time.time.hour and attendance_time.time.minute >= 15:
        return 1
    if user_working_hour > SERVER_TIME_DIFFERENCE + attendance_time.time.hour:
        return 0
    difference = attendance_time.time.hour + SERVER_TIME_DIFFERENCE - user_working_hour
    return difference


def get_statistics_department():
    department_obj = Department.objects.all()
    shift_time_workers = DepartmentShiftTime.objects.all().values('department_id')
    shift_time_workers_ids = []
    department_id_and_percent = {}
    current_month = datetime.now().month - 1
    for i in shift_time_workers:
        shift_time_workers_ids.append(i['department_id'])
    for i in department_obj:
        if i.id not in shift_time_workers_ids:
            res = get_attendance_percentage_department(i.id)
            if len(res) == 0:
                department_id_and_percent[i.id] = 0
            else:
                department_id_and_percent[i.id] = res[current_month]
    department_id_and_percent = {k: v for k, v in sorted(department_id_and_percent.items(), key=lambda item: item[1])}
    if len(department_id_and_percent) % 2 == 0:
        department_id_and_percent[len(department_id_and_percent) // 2] = 0
    lowest = {}
    highest = {}
    middle_key = len(department_id_and_percent) // 2
    key_counter = 0
    for key, value in department_id_and_percent.items():
        if key_counter >= middle_key:
            highest[key] = value
        else:
            lowest[key] = value
        key_counter += 1
    lowest_dict = []
    highest_dict = []
    for key, value in highest.items():
        for i in department_obj:
            if int(key) == int(i.id):
                highest_dict.append({'percentage': value, 'name': i.name})
    for key, value in lowest.items():
        for i in department_obj:
            if int(key) == int(i.id):
                lowest_dict.append({'percentage': value, 'name': i.name})
    context = {
        'lowest': [lowest_dict[0], lowest_dict[1], lowest_dict[2]],
        'highest': [highest_dict[-1], highest_dict[-2], highest_dict[-3]]
    }
    department_bulk_create = []
    for i in context['lowest']:
        department_bulk_create.append(
            DepartmentStatistics(
                type="lowest",
                name=i['name'],
                percentage=i['percentage']
            )
        )
    for i in context['highest']:
        department_bulk_create.append(
            DepartmentStatistics(
                type="highest",
                name=i['name'],
                percentage=i['percentage']
            )
        )
    DepartmentStatistics.objects.all().delete()
    DepartmentStatistics.objects.bulk_create(department_bulk_create)
    return context


def get_statistics_employee_attendance_ajax():
    res = get_statistics_employee_attendance()
    res = {k: v for k, v in sorted(res.items(), key=lambda item: item[1])}
    if len(res) % 2 == 0:
        res[len(res) // 2] = 0
    lowest = {}
    highest = {}
    middle_key = len(res) // 2
    key_counter = 0
    for key, value in res.items():
        if key_counter >= middle_key:
            highest[key] = value
        else:
            lowest[key] = value
        key_counter += 1
    lowest_dict = []
    highest_dict = []
    for key, value in lowest.items():
        for i in Employee.objects.select_related('department').filter(status=True):
            if int(key) == int(i.id):
                lowest_dict.append({'percentage': value, 'full_name': i.full_name, 'department': i.department.name})
    for key, value in highest.items():
        for i in Employee.objects.select_related('department').filter(status=True):
            if int(key) == int(i.id):
                highest_dict.append({'percentage': value, 'full_name': i.full_name, 'department': i.department.name})
    highest_dict.reverse()
    context = {
        'lowest_attendance': lowest_dict[0:10],
        'highest_attendance': highest_dict[0:10]
    }
    attendance_employee_bulk_create = []
    for i in context['lowest_attendance']:
        attendance_employee_bulk_create.append(
            EmployeeStatisticsAttendance(
                type="lowest",
                name=i['full_name'],
                percentage=i['percentage'],
                department=i['department']
            )
        )
    for i in context['highest_attendance']:
        attendance_employee_bulk_create.append(
            EmployeeStatisticsAttendance(
                type="highest",
                name=i['full_name'],
                percentage=i['percentage'],
                department=i['department']
            )
        )
    EmployeeStatisticsAttendance.objects.all().delete()
    EmployeeStatisticsAttendance.objects.bulk_create(attendance_employee_bulk_create)
    return context


def get_statistics_employee_working_hours_ajax():
    employee_obj = Employee.objects.filter(status=True)
    current_month = datetime.now().month - 1
    employee_percent_dict = {}
    for i in employee_obj:
        resp = get_attendance_percentage_employee(i.id)
        employee_percent_dict[resp['employee_id']] = resp['percent'][current_month]
    employee_percent_dict = {k: v for k, v in sorted(employee_percent_dict.items(), key=lambda item: item[1])}
    if len(employee_percent_dict) % 2 == 0:
        employee_percent_dict[len(employee_percent_dict) // 2] = 0
    lowest = {}
    highest = {}
    middle_key = len(employee_percent_dict) // 2
    key_counter = 0
    for key, value in employee_percent_dict.items():
        if key_counter >= middle_key:
            highest[key] = value
        else:
            lowest[key] = value
        key_counter += 1
    lowest_dict = []
    highest_dict = []
    for key, value in lowest.items():
        for i in Employee.objects.select_related('department').filter(status=True):
            if int(key) == int(i.id):
                lowest_dict.append({'percentage': value, 'full_name': i.full_name, 'department': i.department.name})
    for key, value in highest.items():
        for i in Employee.objects.select_related('department').filter(status=True):
            if int(key) == int(i.id):
                highest_dict.append({'percentage': value, 'full_name': i.full_name, 'department': i.department.name})
    highest_dict.reverse()
    context = {
        'lowest_working_hours': lowest_dict[0:10],
        'highest_working_hours': highest_dict[0:10]
    }
    working_hours_bulk_create = []
    for i in context['lowest_working_hours']:
        working_hours_bulk_create.append(
            EmployeeStatisticsWorkingHours(
                type="lowest",
                name=i['full_name'],
                percentage=i['percentage'],
                department=i['department']
            )
        )
    for i in context['highest_working_hours']:
        working_hours_bulk_create.append(
            EmployeeStatisticsWorkingHours(
                type="highest",
                name=i['full_name'],
                percentage=i['percentage'],
                department=i['department']
            )
        )
    EmployeeStatisticsWorkingHours.objects.all().delete()
    EmployeeStatisticsWorkingHours.objects.bulk_create(working_hours_bulk_create)
    return context


def save_importer_csv_to_attendance():
    print('helpers started')
    csv_file = open('media/attendance/importer.csv')
    csv_reader = csv.reader(csv_file)
    rows = []
    for row in csv_reader:
        rows.append(row)
    card_number_from_database = {}
    person_id_from_database = {}
    for i in Employee.objects.all():
        if i.card_number is not None:
            card_number_from_database[i.id] = f'{i.card_number}'
        if i.person_id is not None:
            person_id_from_database[i.id] = f'{i.person_id}'
    card_number_person_id_need_update = []
    last_time_visit_datetime_checker = CsvImporter.objects.all().order_by('id').last()
    for row in rows:
        if row:
            if row[2] != "'" and "'" in row[2]:
                row[2] = row[2].replace("'", "")
                if row[2] in card_number_from_database.values():
                    if last_time_visit_datetime_checker:
                        if last_time_visit_datetime_checker.last_updated_time < \
                                datetime.fromisoformat(f"{row[3]} {row[4]}").replace(tzinfo=utc):
                            for key, value in card_number_from_database.items():
                                if value == row[2]:
                                    row.append(key)
                            card_number_person_id_need_update.append(row)
                    else:
                        for key, value in card_number_from_database.items():
                            if value == row[2]:
                                row.append(key)
                        card_number_person_id_need_update.append(row)
            elif row[1] != "'" and "'" in row[1]:
                row[1] = row[1].replace("'", "")
                if row[1] in person_id_from_database.values():
                    if last_time_visit_datetime_checker:
                        if last_time_visit_datetime_checker.last_updated_time < \
                                datetime.fromisoformat(f"{row[3]} {row[4]}").replace(tzinfo=utc):
                            for key, value in person_id_from_database.items():
                                if value == row[1]:
                                    row.append(key)
                            card_number_person_id_need_update.append(row)
                    else:
                        for key, value in person_id_from_database.items():
                            if value == row[1]:
                                row.append(key)
                        card_number_person_id_need_update.append(row)
    if card_number_person_id_need_update:
        CsvImporter.objects.get_or_create(last_updated_time=
                                          f"{card_number_person_id_need_update[-1][3]} {card_number_person_id_need_update[-1][4]}")
    attendance_bulk_create = []
    for row in card_number_person_id_need_update:
        try:
            attendance_bulk_create.append(
                Attendance(
                    user_id=row[-1],
                    check_status=row[9],
                    time=f"{row[3]} {row[4]}"
                )
            )
        except:
            pass
    if attendance_bulk_create:
        Attendance.objects.bulk_create(attendance_bulk_create)
    get_statistics_department()
    get_statistics_employee_attendance_ajax()
    get_statistics_employee_working_hours_ajax()
    print('helpers ended')
    return
