from django import forms
from .models import Task,TaskItem,Interval
from django.utils import timezone as tz

# class IntervalForm(forms.ModelForm):
#     class Meta:
#         model = Interval
#         fields = ['interval_name','interval_description']
#         widgets = {
#             'interval_name': forms.TextInput(attrs={'class': 'form-group form-control'}),
#             'interval_description': forms.TextInput(attrs={'class': 'form-group form-control'}),
#         }

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['interval','task_name','task_date','task_description','start_date','end_date','times','priority']
        widgets = {
            'interval': forms.Select(attrs={'class': 'form-group form-control'}),
            'task_name': forms.TextInput(attrs={'class': 'form-group form-control'}),
            'task_date': forms.TextInput(attrs={'type': 'date', 'value': tz.now().date(),'class': 'form-group form-control'}),
            'task_description': forms.TextInput(attrs={'class': 'form-group form-control'}),
            'start_date': forms.TextInput(attrs={'type': 'date', 'value': tz.now().date(), 'class': 'form-group form-control'}),
            'end_date': forms.TextInput(attrs={'type': 'date', 'value': tz.now().date(),'class': 'form-group form-control'}),
            'times': forms.NumberInput(attrs={'class': 'form-group form-control'}),
            'priority': forms.NumberInput(attrs={'class': 'form-group form-control'})
        }

class UpdateTaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['interval','task_name','task_date','task_description','start_date','end_date','times','priority','active']
        widgets = {
            'interval': forms.Select(attrs={'class': 'form-group form-control'}),
            'task_name': forms.TextInput(attrs={'class': 'form-group form-control'}),
            'task_date': forms.TextInput(attrs={'type': 'date', 'value': tz.now().date(),'class': 'form-group form-control'}),
            'task_description': forms.TextInput(attrs={'class': 'form-group form-control'}),
            'start_date': forms.TextInput(attrs={'type': 'date', 'value': tz.now().date(), 'class': 'form-group form-control'}),
            'end_date': forms.TextInput(attrs={'type': 'date', 'value': tz.now().date(),'class': 'form-group form-control'}),
            'times': forms.NumberInput(attrs={'class': 'form-group form-control'}),
            'priority': forms.NumberInput(attrs={'class': 'form-group form-control'}),
            'active': forms.Select(attrs={'class': 'form-group form-control'}),
        }

class TaskItemForm(forms.ModelForm):
    class Meta:
        model = TaskItem
        fields = ['task_item_date','task','task_item_number','task_item_description']
        widgets = {
            'task_item_date': forms.TextInput(attrs={'type': 'date', 'value': tz.now().date(),'class': 'form-group form-control'}),
            'task': forms.TextInput(attrs={'class': 'form-group form-control'}),
            'task_item_number': forms.NumberInput(attrs={'class': 'form-group form-control'}),
            'task_item_description': forms.TextInput(attrs={'class': 'form-group form-control'})
        }
