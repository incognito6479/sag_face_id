from faceapp.models import Employee, Attendance, CalendarWorkingDays, EmployeeVacation, CsvImporter, \
    EmployeeBusinessTrip
from system.settings import SERVER_TIME_DIFFERENCE
import csv
import pytz
from datetime import datetime
from calendar import monthrange, monthcalendar

utc = pytz.UTC


def get_statistics_employee_attendance():
    employees = Employee.objects.select_related('working_hours').filter(status=True)
    employee_percentage_id = {}
    for employee in employees:
        working_hours = employee.working_hours.end_time.hour - employee.working_hours.start_time.hour
        res = get_attendance_percentage_employee(employee.id)
        days_must_work = res['hours_needed_to_work'][datetime.now().month]
        overall_percentage = days_must_work // working_hours
        attendances = res['attendances'].filter(time__month=datetime.now().month)
        if str(res['employee_id']) == str(employee.id):
            overall_percentage -= overall_percentage - \
                                  (res['employee_worked_hours'][datetime.now().month] // working_hours)
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


def save_importer_csv_to_attendance(request):
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
    return
