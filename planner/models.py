# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.conf import settings

# Create your models here.
class Interval(models.Model):
    interval_name = models.CharField(max_length=64)
# #     interval_description = models.CharField(max_length=128)
# #     user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
# #     voided = models.IntegerField(default = 0)
# #     date_created = models.DateTimeField(auto_now_add=True)
# #     date_updated = models.DateTimeField(auto_now=True)
#
#     def __str__(self):
#         return self.interval_name
class Task(models.Model):
    interval_choices = (('daily', 'Daily'), ('weekly', 'Weekly'),('monthly','Monthly'),('custom','Custom'))
    interval = models.CharField(max_length=32,choices=interval_choices)
    task_name = models.CharField(max_length=128)
    task_date = models.DateField()
    task_description  = models.CharField(max_length=128)
    start_date = models.DateField()
    end_date =models.DateField()
    choices =(('active','active'),('disabled','disabled'))
    active = models.CharField(max_length=16,choices=choices,default='active')
    times = models.IntegerField(default =1)
    priority = models.IntegerField(default=1)
    voided = models.IntegerField(default =0)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'{self.task_name} - {self.task_description}'

class TaskItem(models.Model):
    task_item_date = models.DateField()
    task = models.ForeignKey(Task,on_delete=models.CASCADE)
    task_item_number = models.IntegerField()
    choices = (('not done','not done'),('pending','pending'),('done','done'))
    task_item_description = models.CharField(max_length=256,blank=True,null=True)
    status = models.CharField(max_length=28,choices=choices,default='not done')
    post_date = models.DateField(null=True,blank=True)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    voided = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'{self.task_item_date}-{self.task_item_description}'
