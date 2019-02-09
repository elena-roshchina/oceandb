import math

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render

from .forms import UploadFileForm, CalculateDensity, CalculateSoundVelocity, CalculateDepth, DataTypeSelection
from .models import Drifters, Sessions, Measurements, SysLog, Storage
from .functions import density, unesco_sound_velosity, calculate_depth, get_coordinates, handle_uploaded_file, \
    DRIFTERS_COUNT, SESSIONS_COUNT, MEASUREMENTS_COUNT, FIRST_DATE, LAST_DATE
from datetime import datetime, date, time, timedelta

EARTH_RADIUS = 6371.116


def index(request):
    form_type_select = DataTypeSelection()
    data = {"form_type_select": form_type_select, "msg": 'none', "count": 'none', "stations": 'none', "points": 'none'}
    return render(request, "index.html", context=data)


# choice_field=1&enter_latitude=11.0&enter_longitude=11.0&radius=110.0
# &moment_start=2016-12-01&moment_end=2017-12-25&seasons=0&horizon_minor=2&horizon_major=4

def selection(request):
    # выборка данных на index/html
    msg = ''
    form_data_select = DataTypeSelection()
    data_kind = str(request.GET.get('choice_field'))
    lat = float(request.GET.get('enter_latitude'))
    long = float(request.GET.get('enter_longitude'))
    coord_valid = abs(lat) < 88.9 and abs(long) < 179.999999
    if not coord_valid:
        msg = 'неверные координаты'

    if data_kind == '1' and coord_valid:
        start = request.GET.get('moment_start')
        end = str(request.GET.get('moment_end'))

        delta = float(request.GET.get('radius')) / 2 / EARTH_RADIUS * 180 / math.pi

        long_1 = long - delta * math.cos(lat / 180 * math.pi)
        long_2 = long + delta * math.cos(lat / 180 * math.pi)
        if long_1 > long_2:
            long_1, long_2 = long_2, long_1

        lat_1 = lat - delta
        lat_2 = lat + delta
        if lat_1 > lat_2:
            lat_1, lat_2 = lat_2, lat_1

        ses = Sessions.objects.raw('select * from argo_sessions'
                                   ' where latitude < %s and latitude > %s and'
                                   ' longitude < %s and longitude > %s and'
                                   ' juld between %s and %s', [lat_2, lat_1, long_2, long_1, start, end])[:]
        count = len(ses)
        stations = []
        points = []
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
                points.append([EARTH_RADIUS * (s.longitude - long) * math.pi / 180 * math.cos(lat * math.pi / 180),
                               EARTH_RADIUS * (s.latitude - lat) * math.pi / 180])

        else:
            pass
        data = {"form_type_select": form_data_select,
                "msg": str(data_kind) + ' - right choice!',
                "count": count,
                "stations": stations,
                "points": points}
    else:
        data = {"form_type_select": form_data_select,
                "msg": 'нет других данных или ' + msg,
                "count": 'none',
                "stations": 'none',
                "points": 'none'}
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






