# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.shortcuts import render,redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import TaskForm,UpdateTaskForm,TaskItemForm
from .models import Task, TaskItem
from .utility import db_update
from django.utils import timezone as tz
from datetime import datetime
import datetime as dt
import calendar
from django.db.models import Q

# Create your views here.
# class IntervalCreateView(View):
#     def get(self,request):
#         form = IntervalForm()
#         return render(request,'planner/interval_create_form.html',{'form':form})
#     def post(self,request):
#         user = User.objects.get(username=self.request.user)  # get the logged in user
#         form = IntervalForm(request.POST)
#         if form.is_valid():
#             int_name = form.cleaned_data['interval_name']
#             int_desc = form.cleaned_data['interval_description']
#             interval = Interval()  #
#             interval.interval_name = int_name
#             interval.interval_description = int_desc
#             interval.user_id = user
#             interval.save()
#         return redirect('interval_list')
#
# class IntervalListView(View):
#     def get(self,request,*args,**kwargs):
#         user = User.objects.get(username=self.request.user)  # get the logged in user
#         interval_list = Interval.objects.filter(voided=0,user_id=user)
#         return render(request,'planner/interval_list.html',{'data':interval_list})
#
# class IntervalUpdateView(View):
#     def get(self,request,pk):
#         interval = Interval.objects.get(pk=pk)
#         form = IntervalForm(instance=interval)
#         return render(request,'planner/interval_update_form.html',{'form':form,'id':interval.id})
#     def post(self,request,pk):
#         form = IntervalForm(request.POST)
#         if(form.is_valid()):
#             int_name = form.cleaned_data['interval_name']
#             int_desc = form.cleaned_data['interval_description']
#             interval = Interval.objects.get(pk=pk)
#             interval.interval_name = int_name
#             interval.interval_description = int_desc
#             interval.save()
#             return redirect('interval_list')
#         return render(request,'planner/interval_update_form.html',{'form':form,'id':interval.id})
#
#
#
# class IntervalDeleteView(View):
#     def get(self,request,pk):
#         interval = Interval.objects.get(pk=pk)
#         return render(request,'planner/interval_delete_form.html',{'pk':interval.id,'data':interval})
#
#     def post(self,request,pk):
#         if request.POST['sub'] == 'cancel':
#             return redirect('interval_list')
#         interval = Interval.objects.get(pk=pk)
#         interval.voided = 1
#         interval.save()
#         return redirect('interval_list')


class TaskCreateView(LoginRequiredMixin,View):
    def get(self,request):
        #user = User.objects.get(username=self.request.user)#get the logged in user
        form = TaskForm()
        return render(request,'planner/task_create_form.html',{'form':form})
    def post(self,request):
        user = User.objects.get(username=self.request.user)
        form = TaskForm(request.POST)
        if form.is_valid():
            interval = form.cleaned_data['interval']
            task_name = form.cleaned_data['task_name']
            task_date = form.cleaned_data['task_date']
            task_description = form.cleaned_data['task_description']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            times = form.cleaned_data['times']
            priority = form.cleaned_data['priority']


            task = Task()
            task.interval = interval
            task.task_name = task_name
            task.task_date = task_date
            task.task_description= task_description
            task.start_date = start_date
            task.end_date = end_date
            task.times = times
            task.priority = priority
            task.user_id = user
            task.save()
            return redirect('task_list')
        return render('planner/task_create_form.html',{'form':form})


class TaskUpdateView(LoginRequiredMixin,View):
    def get(self,request,pk):
        user = User.objects.get(username=self.request.user)
        task = Task.objects.get(pk=pk)
        form= UpdateTaskForm(instance=task)
        return render(request,'planner/task_update_form.html',{'form':form,'id':pk})
    def post(self,request,pk):
        user = User.objects.get(username=self.request.user)
        form = UpdateTaskForm(request.POST)
        if form.is_valid():
            interval = form.cleaned_data['interval']
            task_name = form.cleaned_data['task_name']
            task_date = form.cleaned_data['task_date']
            task_description = form.cleaned_data['task_description']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            times = form.cleaned_data['times']
            priority = form.cleaned_data['priority']
            active = form.cleaned_data['active']

            task = Task.objects.get(pk=pk)
            task.interval = interval
            task.task_name = task_name
            task.task_date = task_date
            task.task_description = task_description
            task.start_date = start_date
            task.end_date = end_date
            task.times = times
            task.priority = priority
            task.active = active
            task.user_id = user
            task.save()
            return redirect('task_list')
        return render('planner/task_update_form.html', {'form': form})


class TaskListView(LoginRequiredMixin,View):
    def get(self,request):
        user = User.objects.get(username= self.request.user)
        db_update(user.id) # check if there are any updates
        tasks = Task.objects.filter(user_id=user,voided=0)
        return render(request,'planner/task_list.html',{'tasks':tasks})

class TaskDeleteView(LoginRequiredMixin,View):
    def get(self,request,pk,*args,**kwargs):
        task = Task.objects.get(pk =pk)
        return render(request,'planner/task_delete_form.html',{'pk':pk,'task':task})
    def post(self,request,pk):
        if request.POST['sub'] == 'cancel':
            return redirect('task_list')
        task = Task.objects.get(pk=pk)
        task.voided = 1
        task.save()
        return redirect('task_list')

class TaskItemPostView(LoginRequiredMixin,View):
    def post(self,request,pk):
        today = tz.now().date()
        taskItem = TaskItem.objects.get(pk=pk)
        task_item_description = request.POST['task_item_description']
        taskItem.status='done'
        taskItem.task_item_description = task_item_description
        taskItem.post_date =today
        taskItem.save() # commit
        return redirect('pending_tasks')

class TaskItemListView(LoginRequiredMixin,View):
    def get(self,request):
        user = User.objects.get(username=self.request.user)
        today = tz.now().date()
        week_start = today - dt.timedelta(days=today.weekday())
        week_end = week_start + dt.timedelta(days=6)
        month_start = dt.date(today.year,today.month,1)
        month_end = dt.date(today.year,today.month,calendar.monthrange(today.year,today.month)[1])
        year_start = dt.date(today.year,1,1)
        year_end = dt.date(today.year,12,31)
        db_update(user.id)  # check if there are any updates
        user = User.objects.get(username=self.request.user)
        daily_data = TaskItem.objects.filter(voided=0,task__interval = 'daily',user_id= user,task_item_date=today)
        weekly_data = TaskItem.objects.filter(
                                            voided=0,
                                              task__interval='weekly',
                                              user_id=user,
                                              task_item_date__range=(week_start,week_end))



        monthly_data = TaskItem.objects.filter(Q(status='pending') |Q(status='not done') | Q(status='done',task_item_date=today),
                                                voided=0, task__interval='monthly',
                                               user_id=user,
                                              task_item_date__range=(month_start,month_end))

        custom_data = TaskItem.objects.filter( Q(status='pending') | Q(status ='not done') | Q(status='done',task_item_date=today),                                                voided=0, task__interval='custom', user_id=user,
                                               task_item_date__range=(year_start, year_end))
        return render(request,'planner/task_event.html',{'daily_data':daily_data,'weekly_data':weekly_data,
                                                         'monthly_data':monthly_data,'custom_data':custom_data})


class TaskItemView(LoginRequiredMixin,View):
    def get(self,request,pk):
        task_item = TaskItem.objects.get(pk=pk)
        return render(request,'planner/task_item_view.html',{'task_item':task_item})