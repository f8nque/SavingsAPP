from django.db import models
from django.conf import settings
# Create your models here.
class Chart(models.Model):
    choices =(("active","active"),("disabled","disabled"))
    chart_date = models.DateField()
    chart_name = models.CharField(max_length=128)
    status =models.CharField(max_length=64,default="active",choices=choices)
    perc = models.IntegerField()
    priority = models.IntegerField()
    voided = models.IntegerField(default=0)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priority','status']

    def __str__(self):
        return self.chart_name



class Allocate(models.Model):
    allocate_date= models.DateField()
    allocate_amount= models.IntegerField()
    comment = models.CharField(max_length=256,null=True,blank=True)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    voided = models.IntegerField(default=0)
    date_created=models.DateTimeField(auto_now_add=True)
    date_updated=models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.allocate_date}--{self.allocate_amount}--{self.comment}"

class Transact(models.Model):
    transact_date = models.DateField()
    allocate_id= models.ForeignKey(Allocate,on_delete=models.CASCADE)
    transact_allocation = models.IntegerField(default=0)
    chart_id =models.ForeignKey(Chart,on_delete=models.CASCADE)
    allocated_amount=models.IntegerField(default=0)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    voided=models.IntegerField(default=0)
    date_created=models.DateTimeField(auto_now_add=True)
    date_updated=models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.transact_date}--{self.transact_allocation}--{self.allocated_amount}"

class Transfer(models.Model):
    transact_id = models.ForeignKey(Transact, on_delete=models.CASCADE)
    transfer_date = models.DateField()
    transfer_amount=models.IntegerField(default=0)
    comment = models.CharField(max_length=256,null=True,blank=True)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    voided=models.IntegerField(default=0)
    date_created=models.DateTimeField(auto_now_add=True)
    date_updated=models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.transfer_date}--{self.transfer_amount}--{self.comment}"
