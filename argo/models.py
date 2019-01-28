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
    n_prof = models.IntegerField()
    cycle_number = models.IntegerField()
    direction = models.CharField(max_length=1)
    data_mode = models.CharField(max_length=1)
    vertical_sampling_scheme = models.CharField(max_length=256)
    juld = models.DateTimeField()
    juld_qc = models.IntegerField()
    juld_location = models.DateTimeField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    position_qc = models.IntegerField()


class Measurements(models.Model):
    session = models.ForeignKey(Sessions, on_delete=models.CASCADE)
    level_number = models.IntegerField()
    psal_adjusted = models.FloatField()
    psal_adjusted_qc = models.IntegerField()
    psal_adjusted_err = models.FloatField()
    pres_adjusted = models.FloatField()
    pres_adjusted_qc = models.IntegerField()
    pres_adjusted_err = models.FloatField()
    temp_adjusted = models.FloatField()
    temp_adjusted_qc = models.IntegerField()
    temp_adjusted_err = models.FloatField()


class SysLog(models.Model):
    moment_stamp = models.DateTimeField(default=datetime.datetime.now())
    file_name = models.CharField(max_length=255)
    message = models.TextField()