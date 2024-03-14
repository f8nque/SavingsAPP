from django import forms
from .models import CategoryItem,ShoppingItem,BoughtItem
from django.utils import timezone as tz
class CategoryForm(forms.ModelForm):
    class Meta:
        model = CategoryItem
        fields = ['category_name']
        widgets = {
            'category_name': forms.TextInput(attrs={'class': 'form-group form-control'}),
        }

class ShoppingForm(forms.ModelForm):
    class Meta:
        model = ShoppingItem
        fields = ['item_date','item_name', 'quantity', 'estimated_price','category_id','comment']
        widgets = {
            'item_date': forms.TextInput(attrs={'type': 'date', 'value': tz.now().date(), 'class': 'form-group form-control'}),
            'item_name': forms.TextInput(attrs={'class': 'form-group form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-group form-control'}),
            'estimated_price': forms.NumberInput(attrs={'class': 'form-group form-control'}),
            'category_id': forms.Select(attrs={'class': 'form-group form-control'}),
            'comment': forms.TextInput(attrs={'class': 'form-group form-control'}),
        }
class ShoppingUpdateForm(forms.ModelForm):
    class Meta:
        model = ShoppingItem
        fields = ['item_date','item_name', 'quantity','status','urgent' ,'estimated_price','category_id','comment']
        widgets = {
            'item_date': forms.TextInput(attrs={'type': 'date', 'value': tz.now().date(), 'class': 'form-group form-control'}),
            'item_name': forms.TextInput(attrs={'class': 'form-group form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-group form-control'}),
            'estimated_price': forms.NumberInput(attrs={'class': 'form-group form-control'}),
            'category_id': forms.Select(attrs={'class': 'form-group form-control'}),
            'urgent': forms.Select(attrs={'class':'form-group form-control'}),
            'status': forms.Select(attrs={'class': 'form-group form-control'}),
            'comment': forms.TextInput(attrs={'class': 'form-group form-control'}),
        }


class BoughtForm(forms.ModelForm):
    class Meta:
        model = BoughtItem
        fields = ['date_bought','quantity_bought', 'amount_paid', 'comment']
        widgets = {
            'date_bought': forms.TextInput(attrs={'type': 'date', 'value': tz.now().date(), 'class': 'form-group form-control'}),
            'quantity_bought': forms.NumberInput(attrs={'class': 'form-group form-control'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-group form-control'}),
            'comment': forms.TextInput(attrs={'class': 'form-group form-control'}),
        }