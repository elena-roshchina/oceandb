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


class DataTypeSelection(forms.Form):
    CHOICES = (('1', 'ARGO',), ('2', 'другой',))
    choice_field = forms.ChoiceField(widget=forms.RadioSelect, choices=CHOICES, label='')