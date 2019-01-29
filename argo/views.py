from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from netCDF4 import Dataset
import datetime
import os

from argo.argo_convertor import read_strings_with_full_value, read_char_with_full_value, read_datetime_with_full_value
from oceandb.settings import ARGO_ARCHIEVE, STATIC_URL
from .forms import UploadFileForm, CalculateDensity
from .models import Drifters, Sessions, Measurements, SysLog, Storage
from .functions import density
from datetime import datetime, date, time, timedelta


DRIFTERS_COUNT = 'DRIFTERS'
SESSIONS_COUNT = 'SESSIONS'
MEASUREMENTS_COUNT = 'MEASUREMENTS'
FIRST_DATE = 'FIRST_DATE'
LAST_DATE = 'LAST_DATE'


def index(request):
    return render(request, "index.html")


def methods(request):

    form_density = CalculateDensity()
    msg = 'none'
    data = {"density_form": form_density, "msg": msg}

    return render(request, "argo/methods.html", context=data)


def calc_density(request):

    s = float(request.GET.get("salinity"))
    t = float(request.GET.get("temperature"))
    p = float(request.GET.get("pressure"))

    d = density(s, t, p)

    form_density = CalculateDensity()
    data = {"density_form": form_density, "msg": str(d)}
    return render(request, "argo/methods.html", context=data)


def description(request):
    drifters_in_db = Storage.objects.filter(comment=DRIFTERS_COUNT).first()
    sessions_in_db = Storage.objects.filter(comment=SESSIONS_COUNT).first()
    measurements_in_db = Storage.objects.filter(comment=MEASUREMENTS_COUNT).first()
    first = Storage.objects.filter(comment=FIRST_DATE).first()
    last = Storage.objects.filter(comment=LAST_DATE).first()

    data = {"drifter_count": drifters_in_db.value,
            "session_count": sessions_in_db.value,
            "measurements_count": measurements_in_db.value,
            "first": first.value, "last": last.value}
    return render(request, "argo/description.html", context=data)


def argo_upload(request):
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
        data = {"filename": name, "message": msg, "form": form, "log": log_history}
        return render(request, "argo/main.html", context=data)
    else:
        form = UploadFileForm()
        data = {"form": form, "log": log_history}
        return render(request, "argo/main.html", context=data)


def handle_uploaded_file(f):
    filename = str(f.name)
    log_message = ''
    if filename.split('.')[1] != "nc":
        log_message += 'it is not netCDF, '
        log_record, log_record_created = SysLog.objects.get_or_create(file_name=filename, message=log_message)
        message = "Загрузка невозможна, это не netCDF файл"
        if log_record_created:
            message += ' log record number ' + str(log_record.id) + ' created'
        return message

    save_path = ARGO_ARCHIEVE + '\\' + datetime.today().strftime("%Y%m%d") + '\\'
    time_start = datetime.now()
    message = ''

    if not os.path.exists(save_path):
        try:
            os.mkdir(save_path)
        except OSError:
            log_message += 'error occurs, a directory was not created'
            log_record, log_record_created = SysLog.objects.get_or_create(file_name=filename, message=log_message)
            message = "Создать директорию %s не удалось." % save_path
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
        dataset = Dataset(save_path + filename)

        reference_jd_date = read_datetime_with_full_value(dataset, 'REFERENCE_DATE_TIME')

        # Create or find record of Drifters table
        drifter_counter = 0
        session_counter = 0
        measurements_counter = 0

        # for i in range(0, dataset.dimensions['N_PROF'].size):
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


            # Create table with measurements
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
                                                                                  temp_adjusted_err=temp_adj_err)
                    if measure_created:
                        measurements_counter += 1

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




