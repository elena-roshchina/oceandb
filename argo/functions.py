# Рассчеты параметров морской воды по
# ГСССД 76-84 Таблицы стандартных справочных данных. Морская вода.
# Плотность в диапазонах температур -2...40 °C, давлений 0...1000 бар и соленостей 0...42
import datetime
from datetime import datetime, date, time, timedelta
from fractions import Fraction
import numpy as np
import math
import os

from netCDF4._netCDF4 import Dataset

from argo.models import Sessions, Drifters, SysLog, Measurements, Storage
from argo.argo_convertor import read_strings_with_full_value, read_char_with_full_value, read_datetime_with_full_value
from oceandb.settings import ARGO_ARCHIEVE

DRIFTERS_COUNT = 'DRIFTERS'
SESSIONS_COUNT = 'SESSIONS'
MEASUREMENTS_COUNT = 'MEASUREMENTS'
FIRST_DATE = 'FIRST_DATE'
LAST_DATE = 'LAST_DATE'


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


def density_w(t):
    # Расчет плотности среднеокеанической чистой воды rho_w в зависимости от температуры
    a_coeff = np.array([999.842594, 6.793952E-2, -9.095290E-3,
                        1.001685E-4, -1.120083E-6, 6.536332E-9], float)
    t_deg = np.array([t**x for x in range(6)], float)
    pw = np.dot(a_coeff, t_deg)
    return pw


def bulk_modulus(sal, t, press):
    # средний модуль упругости K(S, t, p)
    # векторы сост. из степеней p и t
    t_degr = np.array([t ** x for x in range(5)], float)
    p_degr = np.array([t ** x for x in range(3)], float)

    # вычисление коэффициента упругости чистой среднеокеанической воды K_w на поверхности
    coeff_e = np.array([19652.21, 148.4206, -2.327105, 1.360477E-2, -5.155288E-5], float)
    coeff_f = np.array([54.6746, -0.603459, 1.09987E-2, -6.1670E-5, 0.00000000000], float) * sal
    coeff_g = np.array([7.944E-2, 1.6483E-2, -5.3009E-4, 0.00000000000, 0.000000000], float) * (sal ** Fraction(3,2))

    k_s_t_02 = np.dot(coeff_e + coeff_f + coeff_g, t_degr)

    # вычисление коэффициента А
    coeff_i = np.array([2.2838E-3, -1.0981E-5, -1.6078E-6, 0.0, 0.0], float) * sal
    coeff_h = np.array([3.239908, 1.43713E-3, 1.16092E-4, -5.77905E-7, 0.0], float)
    coeff_j = 1.91075E-4
    aa = np.dot(coeff_h + coeff_i, t_degr) + coeff_j * (sal ** Fraction(3,2))
    # вычисление коэффициента B

    coeff_k = np.array([8.50935E-5, -6.12293E-6, 5.2787E-8, 0.0, 0.0], float)
    coeff_m = np.array([-9.9348E-7, 2.0816E-8, 9.1697E-10, 0.0, 0.0], float) * sal
    bb = np.dot(coeff_k + coeff_m, t_degr)

    # вычисление СРЕДНЕГО модуля упругости чистой среднеокеанической воды K
    coefficients = np.array([k_s_t_02, aa, bb])

    return np.dot(coefficients, p_degr)


def density(sal, temp, pressure):
    # pressure unit = decibar, salinity = psu, temperatures in degree C
    # scale pressure to bars
    pressure /= 10
    t_degr = np.array([temp ** x for x in range(5)], float)
    b = np.array([8.24493E-1, -4.0899E-3, 7.6438E-5, -8.2467E-7, 5.3875E-9]) * sal
    c = np.array([-5.72466E-3, 1.0227E-4, -1.6546E-6, 0.0, 0.0]) * (sal ** Fraction(3,2))
    d0 = 4.8314E-4
    dens_s_t_0 = density_w(t=temp) + np.dot(b + c,t_degr) + d0 * (sal ** 2)
    return dens_s_t_0 / (1 - pressure / bulk_modulus(sal=sal, t=temp, press=pressure))


def vilson_sound_velocity(sal, temp, pressure):
    # Sound velocity general formulae
    # c = c0 + delta_c_temp + delta_c_sal + delta_c_press + delta_c_tsp
    # pressure unit = decibar, salinity = psu, temperatures in degree C
    # scale pressure to bars
    pressure /= 10
    sal0 = 35.0
    sal -= sal0
    c = 1449.14
    c_temp = [4.5721, -4.4532E-2, -2.6045E-4, 7.9851E-6]
    for i in range(len(c_temp)):
        c += c_temp[i] * (temp ** (i+1))

    c_sal = [1.39799, 1.69202E-3]
    for i in range(len(c_sal)):
        c += c_sal[i] * (sal ** (i+1))

    c_press = [1.60272E-1, 1.0268E-5, 3.5216E-9, -3.3603E-12]
    for i in range(len(c_press)):
        c += c_press[i] * (pressure ** (i + 1))

    a = [-1.1244E-2, 7.7711E-7, 7.7016E-5,
             -1.2943E-7, 3.1580E-8, 1.5790E-9,
             -1.8607E-4, 7.4812E-6, 4.5283E-8,
             -2.5294E-7, 1.8563E-9, -1.9646E-10]

    t2 = temp ** 2
    p2 = pressure ** 2
    pt = pressure * temp
    pt2 = pt * temp
    pt3 = pt2 * temp
    p2t = pt * pressure
    p3t = p2t * pressure
    p2t2 = pt * pt

    param = [sal * temp, sal * t2, sal * pressure, sal * p2, sal * pt, sal * pt2,
             pt, pt2, pt3, p2t, p2t2, p3t]

    for i in range(len(a)):
        c += a[i] * param[i]
    return c


def unesco_sound_velosity(sal, temp, pressure):
    # Sound velocity UNESCO formulae
    # Fofonov, 1983
    # sound_vel = c_w + AS + B (S ** 3/2) + D * (S ** 2)
    # pressure unit = decibar, salinity = psu, temperatures in degree C

    # scale pressure to bars
    pressure /= 10
    p2 = pressure ** 2
    p3 = pressure ** 3
    c_coeff = [[1402.388, 5.03711, -5.80852E-2, 3.3420E-4, -1.47800E-6, 3.1464E-9],
         [0.153563, 6.8982E-4, -8.1788E-6, 1.3621E-7, -6.1185E-10],
         [3.1260E-5, -1.7107E-6, 2.5974E-8, -2.5335E-10, 1.0405E-12],
         [-9.7729E-9, 3.8504E-10, -2.3643E-12]]
    c_w = 0.0
    for i in range(len(c_coeff)):
        for j in range(len(c_coeff[i])):
            c_w += c_coeff[i][j] * (temp ** j) * (pressure ** i)
    a_coeff = [[1.389, -1.262E-2, 7.164E-5, 2.006E-6, -3.21E-8],
         [9.4742E-5, -1.2580E-5, -6.4885E-8, 1.0507E-8, -2.0122E-10],
         [-3.9064E-7, 9.1041E-9, -1.6002E-10, 7.988E-12],
         [1.100E-10, 6.649E-12, -3.389E-13]]
    a = 0.0
    for i in range(len(a_coeff)):
        for j in range(len(a_coeff[i])):
            a += a_coeff[i][j] * (temp ** j) * (pressure ** i)
    b_coeff = [[-1.922E-2, -4.42E-5],
               [7.3637E-5, 1.7945E-7]]
    b = 0.0
    for i in range(len(b_coeff)):
        for j in range(len(b_coeff[i])):
            b += b_coeff[i][j] * (temp ** j) * (pressure ** i)
    d = 1.727E-3 - 7.9836E-6 * pressure
    return c_w + a * sal + b * (sal ** Fraction(3,2)) + d * (sal ** 2)


def calculate_depth(latitude, pressure):
    # Глубина погружения зависит от гидростатического давления
    # и широты местоположения системы измерения
    # где H - глубина в метрах;
    # pressure, дБар - единицы входного значения)
    # p - гидростатическое давление МПа (=100 дБар
    # географическая широта в угловых градусах
    # источник  П.А.Калашников Гидрометиздат 1985 с 47, 80, 113

    phi = abs(latitude)
    p = pressure / 100
    a = [99.404, 4.983E-4, -2.06E-4, 1.492E-6]
    h = 0.0
    for i in range(len(a)):
        h += a[i] * (phi ** i)
    h -= 2.204E-2 * p
    return h * p


salinity = [0, 35, 40]
temperature = [0, 5, 10, 30, 40]
pr = [0, 10, 100, 10000]
lat = [0.0, 25.0, 50.0, 70.0]
"""
# Depth calculation test
print(' p  , depth ')
for i in range(len(pr)):
    for j in range(len(lat)):
        print('latitude', lat[i], 'p = ', "%6d" % pr[j], calculate_depth(lat[i], pr[j]) )
"""

"""
# Sound velocity calculation test
print(' sal ,  t  ,  p  , sound velocity ')
for i in range(len(salinity)):
    for j in range(len(temperature)):
        for k in range(len(pr)):
            delta = vilson_sound_velocity(salinity[i], temperature[j], pr[k]) - unesco_sound_velosity(salinity[i], temperature[j], pressure[k])

            print("%3d" % salinity[i],
                  "%5d" % temperature[j],
                  "%6d" % pr[k],
                  "%9.3f" % vilson_sound_velocity(salinity[i], temperature[j], pr[k]),
                  "%9.3f" % unesco_sound_velosity(salinity[i], temperature[j], pr[k]))
"""


"""
# Density calculation test
print(' sal ,  t  ,  p  , density ')
for i in range(2):
    for j in range(2):
        for k in range(2):
            print("%3d" % salinity[i],
                  "%5d" % temperature[j],
                  "%6d" % pressure[k],
                  "%9.3f" % density(salinity[i], temperature[j], pressure[k]))
"""





