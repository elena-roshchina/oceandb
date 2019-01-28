from netCDF4 import Dataset
from datetime import datetime, date, time, timedelta, timezone


class Meta:

    def __init__(self, our_dataset, profile, file):
        """Constructor"""
        reference_jd_date = read_datetime_with_full_value(our_dataset, 'REFERENCE_DATE_TIME')
        self.n_prof = profile
        self.platform_number = read_strings_with_full_value(our_dataset, 'PLATFORM_NUMBER')[profile]
        self.source_file = file
        self.cycle_number = our_dataset.variables['CYCLE_NUMBER'][profile].data
        self.direction = read_char_with_full_value(our_dataset, 'DIRECTION')[profile]
        self.data_mode = read_char_with_full_value(our_dataset, 'DATA_MODE')[profile]
        self.scheme = read_strings_with_full_value(our_dataset, 'VERTICAL_SAMPLING_SCHEME')[profile].strip()
        self.juld = reference_jd_date + timedelta(seconds=int(our_dataset.variables['JULD'][profile].data * 24 * 3600))
        self.juld_qc = read_char_with_full_value(our_dataset, 'JULD_QC')[profile]
        self.juld_loc = reference_jd_date + timedelta(
            seconds=int(our_dataset.variables['JULD_LOCATION'][profile].data * 24 * 3600))
        self.latitude = our_dataset.variables['LATITUDE'][profile]
        self.longitude = our_dataset.variables['LONGITUDE'][profile]
        self.position_qc = read_char_with_full_value(our_dataset, 'POSITION_QC')[profile]

    def print_meta_one_line(self):
        print('n_prof = ', self.n_prof,
              'platform number = ', self.platform_number,
              'source file', self.source_file,
              'cycle_number', self.cycle_number,
              'direction', self.direction,
              'data mode = ', self.data_mode,
              'scheme = ', self.scheme,
              'juld = ', self.juld,
              'juld qc = ', self.juld_qc,
              'juld loc = ', self.juld_loc,
              'latitude = ', self.latitude,
              'longitude = ', self.longitude,
              'position qc = ', self.position_qc)
        return 0

    def print_meta_multiy_line(self):
        print('n_prof = ', self.n_prof)
        print('platform number = ', self.platform_number)
        print('source file', self.source_file)
        print('cycle_number', self.cycle_number)
        print('direction', self.direction)
        print('data mode = ', self.data_mode)
        print('scheme = ', self.scheme)
        print('juld = ', self.juld)
        print('juld qc = ', self.juld_qc)
        print('juld loc = ', self.juld_loc)
        print('latitude = ', self.latitude)
        print('longitude = ', self.longitude)
        print('position qc = ', self.position_qc)
        return 0

    @staticmethod
    def print_meta_header(separator):
        print('n_prof' + separator,
              'platform number' + separator,
              'source file' + separator,
              'cycle_number' + separator,
              'direction' + separator,
              'data mode' + separator,
              'scheme' + separator,
              'juld' + separator,
              'juld qc' + separator,
              'juld loc' + separator,
              'latitude' + separator,
              'longitude' + separator,
              'position qc' + separator)
        return 0

    def print_data_one_line(self, separator):
        print(self.n_prof, separator,
              self.platform_number, separator,
              self.source_file, separator,
              self.cycle_number, separator,
              self.direction, separator,
              self.data_mode, separator,
              self.scheme, separator,
              self.juld, separator,
              self.juld_qc, separator,
              self.juld_loc, separator,
              self.latitude, separator,
              self.longitude, separator,
              self.position_qc,  separator,)
        return 0



def read_var(data, key, fill_value):
    if str(fill_value) != "b' '":
        return "Wrong fill value"
    else:
        result = ""
        for item in data.variables[key][:]:
            s = str(item)[2:3]
            if len(s) == 0:
                s = ' '
            result += s
    return result


def read_strings_with_full_value(data, key):
    if 'N_PROF' in dataset.variables[keyvar].dimensions:
        result = []
        n = data.dimensions['N_PROF'].size
        for i in range(0, n):
            res = ''
            for item in data.variables[key][i][:]:
                s = str(item)[2:3]
                if len(s) == 0:
                    s = ' '
                res += s
            result.append(res)
    else:
        result =''
        for item in data.variables[key][:]:
            s = str(item)[2:3]
            if len(s) == 0:
                s = ' '
            result += s
    return result


def read_datatype_with_full_value(data, key):
    result = ''
    for item in data.variables[key][:]:
        s = str(item)[2:3]
        if len(s) == 0:
            s = ' '
        result += s

    return result


def read_datetime_with_full_value(data, key):
    result = ''
    for item in data.variables[key][:]:
        s = str(item)[2:3]
        result += s
    d = datetime(int(result[0:4]), int(result[4:6]), int(result[6:8]),
                 hour=int(result[8:10]), minute=int(result[10:12]), second=int(result[12:]),
                 tzinfo=timezone.utc)
    return d


def read_char_with_full_value(data, key):
    result = []
    n = data.dimensions['N_PROF'].size
    for i in range(0, n):
        s = str(data.variables[key][i])[2:3]
        result.append(s)
    return result


# read_var(dataset, key, i, dataset.variables[key]._FillValue)


# dataset = Dataset('C:\\ncdf4files\\atlantic_ocean\\1997\\12\\19971231_prof.nc')
nc_file = 'D20190101_prof_0.nc'
dataset = Dataset('C:\\ncdf4files\\latest_data\\' + nc_file)


fill_value_b = dataset.variables['PLATFORM_NUMBER']._FillValue


# print(dataset)

numberOfVar = 1

# keyvar = 'PLATFORM_NUMBER'
# keyvar = 'VERTICAL_SAMPLING_SCHEME'
# keyvar = 'DIRECTION'
# keyvar = 'REFERENCE_DATE_TIME'
keyvar = 'PRES_ADJUSTED'
print('DATA_TYPE',read_datatype_with_full_value(dataset, 'DATA_TYPE'))
reference_jd_date = read_datetime_with_full_value(dataset, 'REFERENCE_DATE_TIME')

print('N_PROF',dataset.dimensions['N_PROF'].size)
print('N_LEVELS',dataset.dimensions['N_LEVELS'].size)
print(dataset.variables[keyvar]._FillValue)


print(dataset.variables[keyvar].long_name)
t_diff = []
metadata = []

if 'N_PROF' in dataset.variables[keyvar].dimensions:
    Meta.print_meta_header(';')
    for i in range(0, 1):
    # for i in range(0, dataset.dimensions['N_PROF'].size):
        metadata.append(Meta(our_dataset=dataset,profile=i,file=nc_file))
        Meta.print_data_one_line(metadata[i],';')
        if 'N_LEVELS' in dataset.variables[keyvar].dimensions:

            # for j in range(0, dataset.dimensions['N_LEVELS'].size):
            print('level;',
                  'press [', dataset.variables['PRES_ADJUSTED'].units, ']; qc; err; ',
                  'temp [', dataset.variables['TEMP_ADJUSTED'].units,']; qc; err; ',
                  'sal [', dataset.variables['PSAL_ADJUSTED'].units,']; qc; err; ')
            for j in range(0, dataset.dimensions['N_LEVELS'].size):
                if dataset.variables['PRES_ADJUSTED'][i].data[j] != dataset.variables['PRES_ADJUSTED']._FillValue:
                    print(j,
                          dataset.variables['PRES_ADJUSTED'][i].data[j], ';',
                          str(dataset.variables['PRES_ADJUSTED_QC'][i][j])[2:3], ';',
                          dataset.variables['PRES_ADJUSTED_ERROR'][i].data[j], ';',
                          dataset.variables['TEMP_ADJUSTED'][i].data[j], ';',
                          str(dataset.variables['TEMP_ADJUSTED_QC'][i][j])[2:3], ';',
                          dataset.variables['TEMP_ADJUSTED_ERROR'][i].data[j], ';',
                          dataset.variables['PSAL_ADJUSTED'][i].data[j], ';',
                          str(dataset.variables['PSAL_ADJUSTED_QC'][i][j])[2:3], ';',
                          dataset.variables['PSAL_ADJUSTED_ERROR'][i].data[j])
                    # dataset.variables[keyvar][i].data[j],
                    # dataset.variables[keyvar][i].data[j] == dataset.variables[keyvar]._FillValue)
        else:
            if dataset.variables[keyvar]._FillValue == fill_value_b:
                if len(str(dataset.variables[keyvar][i])) == 4:
                    print(' one char ', str(dataset.variables[keyvar][i])[2:3])
                    print(' one char2 ', read_char_with_full_value(dataset, keyvar)[i])
                else:
                    print(read_strings_with_full_value(dataset, keyvar)[i])
                    print('origin data 1', dataset.variables[keyvar][i].data)
                    print('lenght ', len(str(dataset.variables[keyvar][i])))
            else:
                print('origin data 2', dataset.variables[keyvar][i])
                juld = dataset.variables[keyvar][i].data
                sec = int(juld * 24 * 3600)
                td = timedelta(seconds=sec)
                t_diff.append(td)
                print('timedelta = ', t_diff[i], ' - ', reference_jd_date + t_diff[i])

else:
    if dataset.variables[keyvar]._FillValue == fill_value_b:

        for j in range(0, 14):
            # print('origin data 3', dataset.variables[keyvar][j])
            pass
        if 'DATE_TIME' in dataset.variables[keyvar].dimensions:
            print(read_datetime_with_full_value(dataset, keyvar))
        else:
            print(read_strings_with_full_value(dataset, keyvar))
            print(read_strings_with_full_value(dataset, keyvar).find('Argo profile'))

    else:
        print('origin data 3 ', dataset.variables[keyvar][0])





"""
for key in dataset.variables:
    n = len(dataset.variables[key].dimensions)
    if n == 1:
        print('------------------------------------')
        print(numberOfVar, '.', dataset.variables[key].name,
              dataset.variables[key].long_name)
        print("dimensions = ", n)
        count = 0
        for dim in dataset.variables[key].dimensions[:]:
            print(count, dim, "(", dataset.dimensions[dim].size, ")")
            count += 1

        if dataset.variables[key].dimensions[0] == "DATE_TIME" or dataset.variables[key].dimensions[0].find("STRING") != -1:
            print(read_var(dataset, key, dataset.variables[key]._FillValue))
        else:
            if dataset.variables[key].dimensions[0] == "N_PROF":
                for i in range(dataset.dimensions["N_PROF"].size):
                    if str(dataset.variables[key]._FillValue).find("b' '") != -1:
                        print("i = ", i, ", ", dataset.variables[key][i])
                    else:
                        print("i = ", i, ", ", dataset.variables[key][i])
        print("Attributes:")
        for attr in dataset.variables[key].ncattrs():
            print("        ", attr, ' = ', getattr(dataset.variables[key], attr))

    if n == 2:
        if dataset.variables[key].name.find("PRES") != -1 or dataset.variables[key].name.find("TEMP") != -1 or dataset.variables[key].name.find("PSAL") != -1:
            if "N_PROF" in dataset.variables[key].dimensions and "N_LEVELS" in dataset.variables[key].dimensions:
                print('------------------------------------')
                print(numberOfVar, '.', dataset.variables[key].name,
                    dataset.variables[key].long_name)
                print("dimensions = ", n)
                count = 0
                for dim in dataset.variables[key].dimensions[:]:
                    print(count, dim, "(", dataset.dimensions[dim].size, ")")
                count += 1

                for i in range(dataset.dimensions["N_PROF"].size):
                    print("number of profile = ", i, ",", dataset.variables[key][i])

                print("Attributes:")
                for attr in dataset.variables[key].ncattrs():
                    print("        ", attr, ' = ', getattr(dataset.variables[key], attr))



    numberOfVar += 1
"""
"""
for key in dataset.variables:
    attributes = ""
    for attr in dataset.variables[key].ncattrs():
        attributes += attr
        attributes += ": "
        attributes += str(getattr(dataset.variables[key], attr))
        attributes += "! "
    print(numberOfVar, '!', dataset.variables[key].name, '!', dataset.variables[key].dimensions, '!', attributes)

    numberOfVar += 1
"""

"""
levels = dataset.dimensions[dataset.variables['PSAL'].dimensions[1]].size
prof = dataset.dimensions[dataset.variables['PSAL'].dimensions[0]].size


print('LATITUDE =', dataset.variables['LATITUDE'][0], dataset.variables['LATITUDE'][1])
print('LONGITUDE =', dataset.variables['LONGITUDE'][0], dataset.variables['LONGITUDE'][1])

for i in range(levels):
    print(i, 'sal = ', dataset.variables['PSAL'][0].data[i],
          't = ', dataset.variables['TEMP'][0].data[i],
          's = ', dataset.variables['PSAL'][1].data[i],
          't = ', dataset.variables['TEMP'][1].data[i])
"""
dataset.close()