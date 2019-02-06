# Рассчеты параметров морской воды по
# ГСССД 76-84 Таблицы стандартных справочных данных. Морская вода.
# Плотность в диапазонах температур -2...40 °C, давлений 0...1000 бар и соленостей 0...42
from fractions import Fraction
import numpy as np


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