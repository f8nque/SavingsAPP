from .models import Chart,Allocate,Transact,Transfer
from django import forms
from django.utils import timezone as tz
class ChartForm(forms.ModelForm):
    class Meta:
        model = Chart
        fields = ['chart_date','chart_name', 'status', 'priority', 'perc']
        widgets = {
            'chart_date': forms.TextInput(attrs={'type': 'date', 'value': tz.now().date(), 'class': 'form-group form-control'}),
            'chart_name': forms.TextInput(attrs={'class': 'form-group form-control'}),
            'status': forms.Select(attrs={'class': 'form-group form-control'}),
            'perc': forms.NumberInput(attrs={'class': 'form-group form-control'}),
            'priority': forms.NumberInput(attrs={'class': 'form-group form-control'}),
        }

class AllocateForm(forms.ModelForm):
    class Meta:
        model = Allocate
        fields =['allocate_date','allocate_amount','comment']
        widgets = {
            'allocate_date': forms.TextInput(
                attrs={'type': 'date', 'value': tz.now().date(), 'class': 'form-group form-control'}),
            'allocate_amount': forms.NumberInput(attrs={'class': 'form-group form-control'}),
            'comment': forms.TextInput(attrs={'class': 'form-group form-control'}),
        }


class TransactForm(forms.ModelForm):
    class Meta:
        model = Transact
        fields =['transact_date','chart_id','allocated_amount']
        widgets = {
            'transact_date': forms.TextInput(
                attrs={'type': 'date', 'value': tz.now().date(), 'class': 'form-group form-control'}),
            'chart_id': forms.Select(attrs={'class': 'form-group form-control'}),
            'allocated_amount': forms.NumberInput(attrs={'class': 'form-group form-control'}),
        }


class TransferForm(forms.ModelForm):
    class Meta:
        model = Transfer
        fields =['transfer_date','transfer_amount','comment']
        widgets = {
            'transfer_date': forms.TextInput(
                attrs={'type': 'date', 'value': tz.now().date(), 'class': 'form-group form-control','onchange':'validate_date()'}),
            'transfer_amount': forms.NumberInput(attrs={'class': 'form-group form-control'}),
            'comment': forms.TextInput(attrs={'class': 'form-group form-control'}),
        }