# Рассчеты параметров морской воды по
# ГСССД 76-84 Таблицы стандартных справочных данных. Морская вода.
# Плотность в диапазонах температур -2...40 °C, давлений 0...1000 бар и соленостей 0...42
from fractions import Fraction


def density_w(t):
    # Расчет плотности среднеокеанической чистой воды rho_w в зависимости от температуры
    a = [999.842594,
         6.793952E-2,
         -9.095290E-3,
         1.001685E-4,
         -1.120083E-6,
         6.536332E-9]
    pw = 0.0
    for i in range(6):
        pw += a[i]*(t ** i)
    return pw


def bulk_modulus(sal, t, press):
    # средний модуль упругости K(S, t, p)
    hi = [3.239908,
         1.43713E-3,
         1.16092E-4,
         -5.77905E-7]
    a_w = 0.0
    for i in range(4):
        a_w += hi[i] * (t ** i)
    ki = [8.50935E-5,
         -6.12293E-6,
         5.2787E-8]
    b_w = 0.0
    for i in range(3):
        b_w += ki[i] * (t ** i)

    ii = [2.2838E-3,
          -1.0981E-5,
          -1.6078E-6]
    a = a_w
    for i in range(3):
        a += ii[i] * (t ** i) * sal
    a += 1.91075E-4 * (sal ** Fraction(3,2))

    mi = [-9.9348E-7,
         2.0816E-8,
         9.1697E-10]
    b = b_w
    for i in range(3):
        b += mi[i] * (t ** i) * sal

    ei = [19652.21,
          148.4206,
          -2.327105,
          1.360477E-2,
          -5.155288E-5]
    k_w = 0.0
    for i in range(5):
        k_w += ei[i] * (t ** i)

    fi = [54.6746,
          -0.603459,
          1.09987E-2,
          -6.1670E-5]
    gi = [7.944E-2,
          1.6483E-2,
          -5.3009E-4,
          0.0]
    k_s_t_0 = k_w
    for i in range(4):
        k_s_t_0 += fi[i] * (t ** i) * sal + gi[i] * (t ** i) * (sal ** Fraction(3, 2))
    return k_s_t_0 + a * press + b * (press ** 2)


def density(sal, temp, pressure):
    bi = [8.24493E-1,
          -4.0899E-3,
          7.6438E-5,
          -8.2467E-7,
          5.3875E-9]
    ci = [-5.72466E-3,
          1.0227E-4,
          -1.6546E-6,
          0.0,
          0.0]
    d0 = 4.8314E-4
    density_s_t_0 = density_w(t=temp)
    for i in range(5):
        density_s_t_0 += bi[i] * (temp ** i) * sal + ci[i] * (temp ** i) * (sal ** Fraction(3,2))
    density_s_t_0 += d0 * (sal ** 2)

    return density_s_t_0 / (1 - pressure / bulk_modulus(sal=sal, t=temp, press=pressure))


salinity = [0, 35]
temperature = [5, 25]
pressure = [0, 1000]

print(' sal ,  t  ,  p  , density ')
for i in range(2):
    for j in range(2):
        for k in range(2):
            print("%3d" % salinity[i],
                  "%3d" % temperature[j],
                  "%5d" % pressure[k],
                  "%.3f" % density(salinity[i], temperature[j], pressure[k]))