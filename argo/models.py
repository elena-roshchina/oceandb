import datetime

from django.db import models

# Create your models here.


class Drifters(models.Model):
    platform_number = models.CharField(max_length=8)
    platform_type = models.CharField(max_length=32)
    float_serial_no = models.CharField(max_length=32)


class Sessions(models.Model):
    drifter = models.ForeignKey(Drifters, on_delete=models.CASCADE)
    source_file = models.CharField(max_length=64)
    n_prof = models.PositiveSmallIntegerField()
    cycle_number = models.PositiveSmallIntegerField()
    direction = models.CharField(max_length=1)
    data_mode = models.CharField(max_length=1)
    vertical_sampling_scheme = models.TextField()
    juld = models.DateTimeField()
    juld_qc = models.PositiveSmallIntegerField()
    juld_location = models.DateTimeField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    position_qc = models.PositiveSmallIntegerField()
    depth = models.FloatField(null=True)
    depth_err = models.FloatField(null=True)


class Measurements(models.Model):
    session = models.ForeignKey(Sessions, on_delete=models.CASCADE)
    level_number = models.PositiveSmallIntegerField()
    psal_adjusted = models.FloatField()
    psal_adjusted_qc = models.IntegerField()
    psal_adjusted_err = models.FloatField()
    pres_adjusted = models.FloatField()
    pres_adjusted_qc = models.IntegerField()
    pres_adjusted_err = models.FloatField()
    temp_adjusted = models.FloatField()
    temp_adjusted_qc = models.IntegerField()
    temp_adjusted_err = models.FloatField()
    depth = models.FloatField(null=True)    # meter
    depth_err = models.FloatField(null=True)
    density = models.FloatField(null=True)  # kg/m**3
    density_err = models.FloatField(null=True)
    sound_vel = models.FloatField(null=True)  # m/sec
    sound_vel_err = models.FloatField(null=True)


class SysLog(models.Model):
    moment_stamp = models.DateTimeField()
    file_name = models.CharField(max_length=255)
    message = models.TextField()


class Storage(models.Model):
    value = models.CharField(max_length=255)
    comment = models.CharField(max_length=255)


class Statistic(models.Model):
    year = models.PositiveSmallIntegerField()
    drifters_count = models.PositiveIntegerField()
    sessions_count = models.PositiveIntegerField()
    measurements_count = models.PositiveIntegerField()


class WaterData(models.Model):
    session = models.ForeignKey(Sessions, on_delete=models.CASCADE)
    horizon_number = models.PositiveSmallIntegerField(null=True)
    horizon = models.PositiveSmallIntegerField()                               # meter
    pressure = models.FloatField()                                             # decibar
    pressure_err = models.FloatField(null=True)
    salinity = models.FloatField()                                             # psu
    salinity_err = models.FloatField(null=True)
    temperature = models.FloatField()                                          # tC degree
    temperature_err = models.FloatField(null=True)
    density = models.FloatField()                                              # kg/m**3
    density_err = models.FloatField(null=True)
    sound_vel = models.FloatField()                                            # m/sec
    sound_vel_err = models.FloatField(null=True)



