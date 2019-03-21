from django import forms


class UploadFileForm(forms.Form):
    file = forms.FileField()


class CalculateDensity(forms.Form):
    salinity = forms.FloatField(min_value=0.0, max_value=42.0)
    temperature = forms.FloatField(min_value=-2.0, max_value=40.0)
    pressure = forms.FloatField(min_value=0.0, max_value=10000.0)


class CalculateSoundVelocity(forms.Form):
    salinity = forms.FloatField(min_value=0.0, max_value=42.0)
    temperature = forms.FloatField(min_value=-2.0, max_value=40.0)
    pressure = forms.FloatField(min_value=0.0, max_value=10000.0)


class CalculateDepth(forms.Form):
    latitude = forms.FloatField(min_value=-90.0, max_value=90.0)
    pressure = forms.FloatField(min_value=0.0, max_value=10000.0)


SEASON_CHOICES = (
    ('0', 'Все'),
    ('1', 'зима'),
    ('2', 'весна'),
    ('3', 'лето'),
    ('4', 'осень'),
)


class DataTypeSelection(forms.Form):
    CHOICES = (('1', 'ARGO original', ), ('2', 'другие',))
    choice_field = forms.ChoiceField(widget=forms.RadioSelect, choices=CHOICES, label='')

    enter_latitude = forms.FloatField(min_value=-88.9, max_value=88.9)
    enter_longitude = forms.FloatField(min_value=-179.99999999, max_value=179.99999999)
    radius = forms.FloatField(min_value=10.0, max_value=600.0)

    moment_start = forms.DateField()
    moment_end = forms.DateField()

    seasons = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=SEASON_CHOICES,
    )

    horizon_minor = forms.IntegerField(min_value=0, max_value=7999)
    horizon_major = forms.IntegerField(min_value=1, max_value=8000)

    stand_horizons = forms.ChoiceField(widget=forms.CheckboxInput, required=False)