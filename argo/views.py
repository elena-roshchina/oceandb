import math
import os

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render

from oceandb.settings import ARGO_ARCHIEVE
from .forms import UploadFileForm, CalculateDensity, CalculateSoundVelocity, CalculateDepth, DataTypeSelection
from .models import Drifters, Sessions, Measurements, SysLog, Storage
from .functions import density, unesco_sound_velosity, calculate_depth
from .argo_convertor import read_strings_with_full_value, read_char_with_full_value, read_datetime_with_full_value

from datetime import datetime, date, time, timedelta
from netCDF4 import Dataset

DRIFTERS_COUNT = 'DRIFTERS'
SESSIONS_COUNT = 'SESSIONS'
MEASUREMENTS_COUNT = 'MEASUREMENTS'
FIRST_DATE = 'FIRST_DATE'
LAST_DATE = 'LAST_DATE'
EARTH_RADIUS = 6371.116


def index(request):
    form_type_select = DataTypeSelection()
    data = {"form_type_select": form_type_select,
            "msg": 'none',
            "count": 'none',
            "stations": 'none',
            "points": 'none',
            "profiles": 'none'}
    return render(request, "index.html", context=data)


# choice_field=1&enter_latitude=11.0&enter_longitude=11.0&radius=110.0
# &moment_start=2016-12-01&moment_end=2017-12-25&seasons=0&horizon_minor=2&horizon_major=4

def selection(request):
    # выборка данных на index/html
    msg = ''
    form_data_select = DataTypeSelection()
    data_kind = str(request.GET.get('choice_field'))
    lat0 = float(request.GET.get('enter_latitude'))
    long0 = float(request.GET.get('enter_longitude'))
    # form_data_select.enter_latitude = lat0
    coord_valid = abs(lat0) < 88.9 and abs(long0) < 179.999999
    if not coord_valid:
        msg = 'неверные координаты'

    if data_kind == '1' and coord_valid:
        start = request.GET.get('moment_start')
        end = str(request.GET.get('moment_end'))

        delta = float(request.GET.get('radius')) / 2 / EARTH_RADIUS * 180 / math.pi

        long_1 = long0 - delta * math.cos(lat0 / 180 * math.pi)
        long_2 = long0 + delta * math.cos(lat0 / 180 * math.pi)
        if long_1 > long_2:
            long_1, long_2 = long_2, long_1

        lat_1 = lat0 - delta
        lat_2 = lat0 + delta
        if lat_1 > lat_2:
            lat_1, lat_2 = lat_2, lat_1

        ses = Sessions.objects.raw('select * from argo_sessions'
                                   ' where latitude < %s and latitude > %s and'
                                   ' longitude < %s and longitude > %s and'
                                   ' juld between %s and %s', [lat_2, lat_1, long_2, long_1, start, end])[:]
        count = len(ses)
        stations = []
        points = []
        profiles = []
        if count > 0:
            #  Запишем полученные по запросу сессии (станции, места измерений)  в список словарей для передачи в html
            drifters_found = Drifters.objects.in_bulk()
            for s in ses:
                stations.append({"moment": s.juld,
                                 "latitude": s.latitude,
                                 "longitude": s.longitude,
                                 "session_id": s.id,
                                 "drifter_id": s.drifter_id,
                                 "drifter_number": drifters_found[s.drifter_id].platform_number})
                """
                points.append([EARTH_RADIUS * (s.longitude - long) * math.pi / 180 * math.cos(lat * math.pi / 180),
                               EARTH_RADIUS * (s.latitude - lat) * math.pi / 180])
                               """
                points.append([s.longitude,
                               s.latitude])
                # для данный станции надо получить список измерений
                # это будет словарь с id сессии, моментом и списком точек [x,y]
                prof_points = []
                values = Measurements.objects.filter(session_id=s.id)
                for v in values:
                    if v.depth is not None:
                        prof_points.append([v.sound_vel, v.depth])
                # Сортировка списка списков по второму полю - глубине
                prof_points.sort(key=lambda i: i[1])
                profiles.append({"prof_session": s.id,
                                 "prof_date": s.juld[:10],
                                 "prof_points": prof_points})

        else:
            pass
        data = {"form_type_select": form_data_select,
                "msg": str(data_kind) + ' - right choice!',
                "count": count,
                "stations": stations,
                "points": points,
                "profiles": profiles}
    else:
        data = {"form_type_select": form_data_select,
                "msg": 'нет других данных или ' + msg,
                "count": 'none',
                "stations": 'none',
                "points": 'none',
                "profiles": 'none'}
    return render(request, "index.html", context=data)


def methods(request):
    # обработчик запроса к странице с методикой
    form_density = CalculateDensity()
    form_svel = CalculateSoundVelocity()
    form_depth = CalculateDepth()
    data = {"svel_form": form_svel, "msg_svel": 'none',
            "density_form": form_density, "msg": 'none',
            "depth_form": form_depth, "msg_depth": 'none'}
    return render(request, "argo/methods.html", context=data)


def calc_density(request):
    # обработчик формы вычисления плотности морской воды
    s = float(request.GET.get("salinity"))
    t = float(request.GET.get("temperature"))
    p = float(request.GET.get("pressure"))

    d = density(s, t, p)

    form_density = CalculateDensity()
    form_svel = CalculateSoundVelocity()
    form_depth = CalculateDepth()

    data = {"svel_form": form_svel, "msg_svel": 'none',
            "density_form": form_density, "msg": str(d),
            "depth_form": form_depth, "msg_depth": 'none'}
    return render(request, "argo/methods.html", context=data)


def calc_svel(request):
    # обработчик формы вычисления скорости звука
    s = float(request.GET.get("salinity"))
    t = float(request.GET.get("temperature"))
    p = float(request.GET.get("pressure"))

    sv = unesco_sound_velosity(s, t, p)

    form_density = CalculateDensity()
    form_svel = CalculateSoundVelocity()
    form_depth = CalculateDepth()
    data = {"svel_form": form_svel, "msg_svel": str(sv),
            "density_form": form_density, "msg": 'none',
            "depth_form": form_depth, "msg_depth": 'none'}
    return render(request, "argo/methods.html", context=data)


def calc_depth(request):
    # обработчик формы вычисления глубины
    lat = float(request.GET.get("latitude"))
    p = float(request.GET.get("pressure"))

    depth = calculate_depth(lat, p)
    form_density = CalculateDensity()
    form_svel = CalculateSoundVelocity()
    form_depth = CalculateDepth()
    data = {"svel_form": form_svel, "msg_svel": 'none',
            "density_form": form_density, "msg": 'none',
            "depth_form": form_depth, "msg_depth": str(depth)}
    return render(request, "argo/methods.html", context=data)


def description(request):
    # обработчик запроса который выводи на страницу описания данных статистику по базе
    drifters_in_db = Storage.objects.filter(comment=DRIFTERS_COUNT).first().value
    sessions_in_db = Storage.objects.filter(comment=SESSIONS_COUNT).first().value
    measurements_in_db = Storage.objects.filter(comment=MEASUREMENTS_COUNT).first().value
    first = Storage.objects.filter(comment=FIRST_DATE).first().value[:10]
    last = Storage.objects.filter(comment=LAST_DATE).first().value[:10]

    data = {"drifter_count": drifters_in_db,
            "session_count": sessions_in_db,
            "measurements_count": measurements_in_db,
            "first": first, "last": last}
    return render(request, "argo/description.html", context=data)


def drifters(request):
    # вывод данных по всем буям в БД
    drifter_numbers = []
    drifters_found = Drifters.objects.in_bulk()
    for d in drifters_found:
        drifter_numbers.append({"id": drifters_found[d].id,
                                "drifter_num": int(drifters_found[d].platform_number)})
    drifter_numbers.sort(key=lambda d: d['drifter_num'])
    data = {"count": len(drifter_numbers), "drifters": drifter_numbers}
    return render(request, "argo/drifters.html", context=data)


def drifter_info(request):
    # вывод данных по id буя
    id_no = request.GET.get("id")
    try:
        drifter = Drifters.objects.get(id=id_no)
        dr_sessions = Sessions.objects.filter(drifter=drifter)[:]
        if len(dr_sessions) != 0:
            sessions_found = []
            for s in dr_sessions:
                sessions_found.append({"id": s.id,
                                       "moment": s.juld,
                                       "latitude": s.latitude,
                                       "longitude": s.longitude})

            data = {"status": 1,
                    "drifter_id": id_no,
                    "number": drifter.platform_number,
                    "serial": drifter.float_serial_no,
                    "sessions": sessions_found}
        else:
            data = {"status": 2, "number": drifter.platform_number}  # 2 - сессий нет для этого буя
    except ObjectDoesNotExist:
        data = {"status": 0, "number": id} # буй не найден

    return render(request, "argo/drifter_info.html", context=data)


def session_info(request):
    # вывод данных по id одной станции (сессии) и ее измерений
    session_id = request.GET.get("session_id")
    drifter_id = request.GET.get("drifter_id")
    drifter_number = request.GET.get("drifter_number")
    try:
        session_this = Sessions.objects.get(id=session_id)
        measured_values = Measurements.objects.filter(session=session_this)[:]
        if len(measured_values) != 0:
            values_list = []
            for m in measured_values:
                if m.depth is not None:
                    values_list.append({"pressure": m.pres_adjusted,
                                        "pressure_qc": m.pres_adjusted_qc,
                                        "salinity": m.psal_adjusted,
                                        "salinity_qc": m.psal_adjusted_qc,
                                        "temperature": m.temp_adjusted,
                                        "temperature_qc": m.temp_adjusted_qc,
                                        "depth": m.depth,
                                        "density": m.density,
                                        "svelocity": m.sound_vel})

            values_list.sort(key=lambda d: d['depth'])
            data = {"status": 1,
                    "session": {"id": session_this.id,
                                "moment": session_this.juld,
                                "latitude": session_this.latitude,
                                "longitude": session_this.longitude,
                                "qc": session_this.position_qc,
                                "drifter_id": drifter_id,
                                "drifter_number": drifter_number},
                    "count": len(measured_values),
                    "measurements": values_list}
        else:
            data = {"status": 1,
                    "session": {"id": session_this.id,
                                "moment": session_this.juld,
                                "latitude": session_this.latitude,
                                "longitude": session_this.longitude,
                                "qc": session_this.position_qc,
                                "drifter_id": drifter_id,
                                "drifter_number": drifter_number
                                },
                    "count": 0}

    except ObjectDoesNotExist:
        data = {"status": 0, "session": {"id": session_id}}

    return render(request, "argo/session_info.html", context=data)


def sessions_all(request):
    # вывод информации по всем станциям (сессиям)
    res = get_coordinates()
    total = len(res)
    data = {"coordinates": res, "total": total}
    return render(request, "argo/sessions_all.html", context=data)


def calculation(request):
    # counter = make_calculations()
    # служебная функция для разовых вычислений в БД
    data = {"message": 'none'}
    return render(request, "argo/test.html", context=data)


def argo_upload(request):
    ####################################################################################
    # обработчик запроса загрузки данных с файла в базу данных
    # проверка файла на принадлежгность к формату netCFD, запись файла в хранилище
    # путь с архив определен в settings.py
    ####################################################################################
    log = SysLog.objects.all()
    log_count = log.count()
    log_history = log[(log_count - 5):]
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # сохранение файла
            msg = handle_uploaded_file(request.FILES['file'])
            name = request.FILES['file'].name
            form = UploadFileForm()

            if msg.find('added') != -1:
                data = {"filename": name, "message": msg, "form": form, "log": log_history}
                return render(request, "argo/main.html", context=data)
            else:
                msg += "no records added"
                data = {"filename": name, "message": msg, "form": form, "log": log_history}
                return render(request, "argo/main.html", context=data)
        form = UploadFileForm()
        msg = "form is not valid"
        name = "None"
        data = {"filename": name, "message": msg, "form": form, "log": log_history, "result": 'none'}
        return render(request, "argo/main.html", context=data)
    else:
        form = UploadFileForm()
        data = {"form": form, "log": log_history, "result": 'none'}
        return render(request, "argo/main.html", context=data)


def handle_uploaded_file(f):
    ####################################################################################
    # загрузка файла с диска
    # чтение в dataset
    # валидация данных
    # запись в таблицы DRIFTERS SESSIONS MEASUREMENTS
    # запись в таблицу SysLog о загрузке
    ####################################################################################
    filename = str(f.name)
    log_message = ''
    if filename.split('.')[1] != "nc":
        log_message += 'it is not netCDF, '
        log_record, log_record_created = SysLog.objects.get_or_create(file_name=filename, message=log_message)
        message = "Загрузка невозможна, это не netCDF файл"
        if log_record_created:
            message += ' log record number ' + str(log_record.id) + ' created'
        return message

    save_path = ARGO_ARCHIEVE
    time_start = datetime.now()
    message = ''

    if not os.path.exists(save_path):
        try:
            os.mkdir(save_path)
        except OSError:
            log_message += 'error occurs, a directory was not created'
            log_record, log_record_created = SysLog.objects.get_or_create(file_name=filename, message=log_message)
            message = "Создать директорию %s не удалось" % save_path
            if log_record_created:
                message += ' log record number ' + str(log_record.id) + ' created'
            return message

    if not os.path.isdir(save_path):
        log_message += 'a directory was not created, file name already exists'
        log_record, log_record_created = SysLog.objects.get_or_create(file_name=filename, message=log_message)
        message = "Создать директорию %s не удалось, существует файл с таким именем." % save_path
        if log_record_created:
            message += ' log record number ' + str(log_record.id) + ' created'
        return message
    else:
        with open(save_path + f.name, 'wb') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
        # Чтение всей структуры данных в NetCDF формате в объект dataset
        dataset = Dataset(save_path + filename)
        # read_datetime_with_full_value - освобождает строку от служебных символов атрибута _FillValue
        # чтение нульпункта дат
        reference_jd_date = read_datetime_with_full_value(dataset, 'REFERENCE_DATE_TIME')

        # Create or find record of Drifters table
        drifter_counter = 0
        session_counter = 0
        measurements_counter = 0

        for i in range(0, dataset.dimensions['N_PROF'].size):
            platform_num = read_strings_with_full_value(dataset, 'PLATFORM_NUMBER')[i]
            platform_ty = read_strings_with_full_value(dataset, 'PLATFORM_TYPE')[i]
            float_serial = read_strings_with_full_value(dataset, 'FLOAT_SERIAL_NO')[i]
            drifter, created = Drifters.objects.get_or_create(platform_number=platform_num,
                                                              platform_type=platform_ty,
                                                           float_serial_no=float_serial)
            if created:
                drifter_counter += 1

            # Create or find record of Sessions table
            cycle_number = dataset.variables['CYCLE_NUMBER'][i]
            direction = read_char_with_full_value(dataset, 'DIRECTION')[i]
            data_mod = read_char_with_full_value(dataset, 'DATA_MODE')[i]
            vertical_sampling_scheme = read_strings_with_full_value(dataset, 'VERTICAL_SAMPLING_SCHEME')[i]
            juld = reference_jd_date + timedelta(seconds=int(dataset.variables['JULD'][i].data * 24 * 3600))
            juld_qc = read_char_with_full_value(dataset, 'JULD_QC')[i]
            juld_location = reference_jd_date + timedelta(seconds=int(dataset.variables['JULD_LOCATION'][i].data * 24 * 3600))
            latitude = dataset.variables['LATITUDE'][i].data
            longitude = dataset.variables['LONGITUDE'][i].data
            position_qc = read_char_with_full_value(dataset, 'POSITION_QC')[i]

            session, session_created = Sessions.objects.get_or_create(drifter=drifter,
                                                                      source_file=filename,
                                                                      n_prof=i,
                                                                      cycle_number=cycle_number,
                                                                      direction=direction,
                                                                      data_mode=data_mod,
                                                                      vertical_sampling_scheme=vertical_sampling_scheme,
                                                                      juld=juld,
                                                                      juld_qc=juld_qc,
                                                                      juld_location=juld_location,
                                                                      latitude=latitude,
                                                                      longitude=longitude,
                                                                      position_qc=position_qc)
            if session_created:
                session_counter += 1

            # Record measurements
            # for j in range(0, dataset.dimensions['N_LEVELS'].size):
            for j in range(0, dataset.dimensions['N_LEVELS'].size):
                if dataset.variables['PRES_ADJUSTED'][i].data[j] != dataset.variables['PRES_ADJUSTED']._FillValue:
                    psal_adj = dataset.variables['PSAL_ADJUSTED'][i].data[j]
                    psal_adj_qc = int(str(dataset.variables['PSAL_ADJUSTED_QC'][i][j])[2:3])
                    psal_adj_err = dataset.variables['PSAL_ADJUSTED_ERROR'][i].data[j]
                    pres_adj = dataset.variables['PRES_ADJUSTED'][i].data[j]
                    pres_adj_qc = int(str(dataset.variables['PRES_ADJUSTED_QC'][i][j])[2:3])
                    pres_adj_err = dataset.variables['PRES_ADJUSTED_ERROR'][i].data[j]
                    temp_adj = dataset.variables['TEMP_ADJUSTED'][i].data[j]
                    temp_adj_qc = int(str(dataset.variables['TEMP_ADJUSTED_QC'][i][j])[2:3])
                    temp_adj_err = dataset.variables['TEMP_ADJUSTED_ERROR'][i].data[j]

                    # Data validation
                    # В ARGO поле отсутствующего значения заполняется значением атрибута _FillValue
                    # для полей нестроковых полей оно равно 99999
                    # PRES_ADJUSTED, давление, уже проверено, поэтому проверяем все остальные параметры
                    # _FillValue checking
                    no_fillvalue = psal_adj != 99999 and temp_adj != 99999

                    # Quality Control checking qc=4 or 9 should be ignored
                    # флаги 4 и 9 это плохие или отсутствующие данные
                    pres_qc_valid = pres_adj_qc != 4 and pres_adj_qc != 9
                    psal_qc_valid = psal_adj_qc != 4 and psal_adj_qc != 9
                    temp_qc_valid = temp_adj_qc != 4 and temp_adj_qc != 9

                    # проверка соответствия величин допустимым диапазонам значений
                    # согласно Международному уравнению состояния УС-80
                    # 0 < p < 10000 decibar
                    # 0 < s < 42 psu
                    # -2 < t < 40
                    # Values Control
                    values_valid_min = pres_adj > 0.0 and psal_adj > 0.0 and temp_adj > -1.9
                    values_valid_max = pres_adj < 10000.0 and psal_adj < 42.0 and temp_adj < 40.0
                    values_valid = values_valid_min and values_valid_max

                    is_valid = no_fillvalue and pres_qc_valid and psal_qc_valid and temp_qc_valid and values_valid
                    if is_valid:
                        # Вычисление глубины, плотности и скорости звука
                        depth = calculate_depth(abs(latitude), pres_adj)
                        water_density = density(psal_adj, temp_adj, pres_adj)
                        sound_vel = unesco_sound_velosity(psal_adj, temp_adj, pres_adj)

                        measure, measure_created = Measurements.objects.get_or_create(session=session,
                                                                                      level_number=j,
                                                                                      psal_adjusted=psal_adj,
                                                                                      psal_adjusted_qc=psal_adj_qc,
                                                                                      psal_adjusted_err=psal_adj_err,
                                                                                      pres_adjusted=pres_adj,
                                                                                      pres_adjusted_qc=pres_adj_qc,
                                                                                      pres_adjusted_err=pres_adj_err,
                                                                                      temp_adjusted=temp_adj,
                                                                                      temp_adjusted_qc=temp_adj_qc,
                                                                                      temp_adjusted_err=temp_adj_err,
                                                                                      depth=depth,
                                                                                      density=water_density,
                                                                                      sound_vel=sound_vel)
                        if measure_created:
                            measurements_counter += 1
        # message - вывод служебной информации на страницу загрузки
        message += ' ' + str(drifter_counter)
        message += ' - new drifters added, '
        message += str(session_counter)
        message += ' - new sessions added, '
        message += str(measurements_counter)
        message += ' - measurements added, '
        time_end = datetime.now()
        duration = time_end - time_start
        message += 'start=' + str(time_start.time()) + ' end=' + str(time_end.time()) + ' process duration=' + str(duration.seconds/60) + ' minutes.'

        log_message += 'N_PROF=' + str(dataset.dimensions['N_PROF'].size) + ', '
        log_message += 'N_LEVELS=' + str(dataset.dimensions['N_LEVELS'].size) + ', '
        log_message += str(drifter_counter) + 'drifters, ' + str(session_counter) + 'sessions, '
        log_message += str(measurements_counter) + 'measurements were successfully added '
        log_record, log_record_created = SysLog.objects.get_or_create(moment_stamp=datetime.now(),
                                                                      file_name=filename,
                                                                      message=log_message)

        if log_record_created:
            message += ' log record number ' + str(log_record.id) + ' created'

        # Update statistics
        update_general_stat()

        dataset.close()
        return message


def update_general_stat():
    ####################################################################################
    # запись статистических данных о БД в таблицу Storage
    # Принцип записи: "комментарий" -  значение
    # комментарии для хранения информации о базе:
    # DRIFTERS_COUNT, SESSIONS_COUNT, MEASUREMENTS_COUNT, FIRST_DATE, LAST_DATE
    ####################################################################################

    sessions_in_db = Sessions.objects.all()

    first = sessions_in_db.order_by('juld').first().juld
    last = sessions_in_db.order_by('juld').last().juld

    drifters_stat, drifters_stat_created = Storage.objects.get_or_create(comment=DRIFTERS_COUNT)
    drifters_stat.value = str(Drifters.objects.all().count())
    drifters_stat.save(update_fields=["value"])

    sessions_stat, sessions_stat_created = Storage.objects.get_or_create(comment=SESSIONS_COUNT)
    sessions_stat.value = str(sessions_in_db.count())
    sessions_stat.save(update_fields=["value"])

    measurements_stat, measurements_stat_created = Storage.objects.get_or_create(comment=MEASUREMENTS_COUNT)
    measurements_stat.value = str(Measurements.objects.all().count())
    measurements_stat.save(update_fields=["value"])

    dates_first_stat, dates_first_created = Storage.objects.get_or_create(comment=FIRST_DATE)
    dates_first_stat.value = str(first)
    dates_first_stat.save(update_fields=["value"])

    dates_last_stat, dates_last_created = Storage.objects.get_or_create(comment=LAST_DATE)
    dates_last_stat.value = str(last)
    dates_last_stat.save(update_fields=["value"])

    return 0


def make_calculations():
    # Служебная функция для вычисления глубины, плотности и скорости звука и
    # заполнения полей в БД начиная с номера i (здесь 393390)
    # одноразовая - в дальнейшем поля будут заполняться при начальной загрузке записей из файла
    # необходимо исправить - сначала выбирается сессия, потом по ее id - все измерения и
    # действия совершать с массивом, а то неоптимально - широта требуется в каждой записи измерений,
    # когда ее можно было получить один раз на всю серию
    counter = 0
    """
    try:
        i = 393390
        while True:
            measure = Measurements.objects.get(id=i)
            msg = str(measure.id)
            # _FillValue checking
            no_fillvalue = measure.psal_adjusted != 99999 and measure.temp_adjusted != 99999

            # Quality Control checking qc=4 should be ignored
            pres_qc_valid = measure.pres_adjusted_qc != 4 and measure.pres_adjusted_qc != 9
            psal_qc_valid = measure.psal_adjusted_qc != 4 and measure.psal_adjusted_qc != 9
            temp_qc_valid = measure.temp_adjusted_qc != 4 and measure.temp_adjusted_qc != 9

            # Values Control
            values_valid = measure.pres_adjusted > 0.0 and measure.psal_adjusted > 0.0 and measure.temp_adjusted > -1.9

            is_valid = no_fillvalue and pres_qc_valid and psal_qc_valid and temp_qc_valid and values_valid

            if is_valid:
                lat = Sessions.objects.get(id=measure.session_id).latitude
                measure.depth = calculate_depth(abs(lat), measure.pres_adjusted)
                measure.density = density(measure.psal_adjusted,
                                          measure.temp_adjusted, measure.pres_adjusted)
                measure.sound_vel = unesco_sound_velosity(measure.psal_adjusted,
                                                          measure.temp_adjusted, measure.pres_adjusted)
                measure.save()
            i += 1
            counter += 1
    except ObjectDoesNotExist:
        pass
    """
    return str(counter)


def get_coordinates():

    coord = []
    sessions = Sessions.objects.in_bulk()
    drifters = Drifters.objects.in_bulk()
    for s in sessions:

        coord.append({"moment": sessions[s].juld,
                      "latitude": sessions[s].latitude,
                      "longitude": sessions[s].longitude,
                      "session_id": sessions[s].id,
                      "drifter_id": sessions[s].drifter_id,
                      "drifter_number": drifters[sessions[s].drifter_id].platform_number})

    return coord


