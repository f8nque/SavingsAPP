from django.db import connection
from .models import TaskItem,Task
from django.contrib.auth.models import User
from django.utils import timezone as tz
import datetime
import calendar

def db_update(user):
    daily_db_update(user)
    weekly_db_update(user)
    monthly_db_update(user)
    custom_db_update(user)
def daily_db_update(user):
    today = tz.now().date()
    with connection.cursor() as cursor:
        cursor.execute(f"""
        select *
        from(
        select t.id,
        t.task_name,
        t.start_date,
        t.end_date,
        t.times,
        t.priority,
        0 as task_number
        from planner_task t
        where t.id not in 
        (
        select a.task_id
        from planner_taskitem a
        where a.voided = 0 and  a.task_item_date ='{today}'
        )and t.voided=0 and t.user_id_id = {user} and t.active ='active'
        and t.interval='daily' and t.start_date <= '{today}' and t.end_date >= '{today}') zero_task
        
		UNION
		select * from
        (
        select t.id,
        t.task_name,
        t.start_date,
        t.end_date,
        t.times,
        t.priority,
        ti.task_item_number
        from (
        select c.task_id,sum(task_item_number) as task_item_number
        from(
        select 
        a.task_id,1 as task_item_number
        from planner_taskitem a
        where a.voided = 0 and  a.task_item_date ='{today}'
        ) c
        group by c.task_id) ti
        inner join planner_task t on ti.task_id = t.id
        where ti.task_item_number < t.times and t.user_id_id ={user} and t.interval='daily' and t.voided=0
        and t.active='active' and t.end_date >= '{today}'
		and t.id not in 
		(
			select distinct pti.task_id
			from planner_taskitem pti
			inner join planner_task pt on pti.task_id = pt.id
			where pti.task_item_date = '{today}'
			and (pti.status ='pending' or pti.status ='not done') and pt.interval ='daily'
		)
        ) less_task
        """)
        columns = [col[0] for col in cursor.description]
        daily_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        for task in daily_data:
            taskItem = TaskItem()
            taskItem.task_item_date = today
            taskItem.task_item_description =''
            taskItem.task_item_number = task['task_number'] + 1
            taskItem.user_id = User.objects.get(pk=user)
            taskItem.task = Task.objects.get(pk=task['id'])
            if task['task_number'] > 0:
                taskItem.status ='pending'
            taskItem.save()



def weekly_db_update(user):
    today = tz.now().date()
    week_start = today - datetime.timedelta(days=today.weekday())
    week_end = week_start + datetime.timedelta(days=6)
    with connection.cursor() as cursor:
        cursor.execute(f"""
        select *
        from(
        select t.id,
        t.task_name,
        t.start_date,
        t.end_date,
        t.times,
        t.priority,
        0 as task_number
        from planner_task t
        where t.id not in 
        (
        select a.task_id
        from planner_taskitem a
        where a.voided = 0 and a.task_item_date >= '{week_start}' and a.task_item_date <= '{week_end}'
        )and t.voided=0 and t.user_id_id = {user} and t.active = 'active'
        and t.interval='weekly'  and t.end_date >= '{today}') zero_task
		
		UNION
		select distinct * from
        (
        select t.id,
        t.task_name,
        t.start_date,
        t.end_date,
        t.times,
        t.priority,
        ti.task_item_number
        from (
        select c.task_id,sum(task_item_number) as task_item_number
        from(
        select 
        a.task_id,1 as task_item_number
        from planner_taskitem a
        where a.voided = 0 and a.task_item_date >= '{week_start}' and a.task_item_date <= '{week_end}'
        ) c
        group by c.task_id) ti
        inner join planner_task t on ti.task_id = t.id
		inner join planner_taskitem pti on t.id = pti.task_id
        where ti.task_item_number < t.times and t.user_id_id ={user}
        and t.active='active'  and t.end_date >= '{today}' and t.interval='weekly'
		and pti.task_item_date between '{week_start}' and '{week_end}'
		and t.id not in(
			select distinct pti.task_id
			from planner_taskitem pti
			inner join planner_task pt on pti.task_id = pt.id
			where pti.task_item_date between '{week_start}' and '{week_end}'
			and (pti.status ='pending' or pti.status ='not done') and pt.interval ='weekly'
		)
        ) less_task
        """)
        columns = [col[0] for col in cursor.description]
        weekly_data = [dict(zip(columns, row)) for row in cursor.fetchall()]


        for task in weekly_data:
            taskItem = TaskItem()
            taskItem.task_item_date = today
            taskItem.task_item_description = ''
            taskItem.task_item_number = task['task_number'] + 1
            taskItem.user_id = User.objects.get(pk=user)
            taskItem.task = Task.objects.get(pk=task['id'])
            if task['task_number'] > 0:
                taskItem.status = 'pending'
            taskItem.save()



def monthly_db_update(user):
    today = tz.now().date()
    month_start = datetime.date(today.year,today.month,1)
    month_end = datetime.date(today.year,today.month,calendar.monthrange(today.year, today.month)[1])
    with connection.cursor() as cursor:
        cursor.execute(f"""
        select *
        from(
        select t.id,
        t.task_name,
        t.start_date,
        t.end_date,
        t.times,
        t.priority,
        0 as task_number
        from planner_task t
        where t.id not in 
        (
        select a.task_id
        from planner_taskitem a
        where a.voided = 0 and a.task_item_date >= '{month_start}' and a.task_item_date <= '{month_end}'
        )and t.voided=0 and t.user_id_id = {user} and t.active = 'active'
        and t.interval='monthly'  and t.end_date >= '{today}') zero_task

		UNION
		select distinct * from
        (
        select t.id,
        t.task_name,
        t.start_date,
        t.end_date,
        t.times,
        t.priority,
        ti.task_item_number
        from (
        select c.task_id,sum(task_item_number) as task_item_number
        from(
        select 
        a.task_id,1 as task_item_number
        from planner_taskitem a
        where a.voided = 0 and a.task_item_date >= '{month_start}' and a.task_item_date <= '{month_end}'
        ) c
        group by c.task_id) ti
        inner join planner_task t on ti.task_id = t.id
		inner join planner_taskitem pti on t.id = pti.task_id
        where ti.task_item_number < t.times and t.user_id_id ={user}
        and t.active='active'  and t.end_date >= '{today}' and t.interval='monthly'
		and pti.task_item_date between '{month_start}' and '{month_end}'
		and t.id not in(
			select distinct pti.task_id
			from planner_taskitem pti
			inner join planner_task pt on pti.task_id = pt.id
			where pti.task_item_date between '{month_start}' and '{month_end}'
			and (pti.status ='pending' or pti.status ='not done') and pt.interval ='monthly'
		)
        ) less_task
        """)
        columns = [col[0] for col in cursor.description]
        monthly_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        for task in monthly_data:
            taskItem = TaskItem()
            taskItem.task_item_date = today
            taskItem.task_item_description = ''
            taskItem.task_item_number = task['task_number'] + 1
            taskItem.user_id = User.objects.get(pk=user)
            taskItem.task = Task.objects.get(pk=task['id'])
            if task['task_number'] > 0:
                taskItem.status = 'pending'
            taskItem.save()

def custom_db_update(user):
    today = tz.now().date()
    with connection.cursor() as cursor:
        cursor.execute(f"""
        select *
        from(
        select t.id,
        t.task_name,
        t.start_date,
        t.end_date,
        t.times,
        t.priority,
        0 as task_number
        from planner_task t
        where t.id not in 
        (
        select a.task_id
        from planner_taskitem a
        inner join planner_task b on a.task_id = b.id
        where a.voided = 0 and a.task_item_date >= b.start_date and a.task_item_date <= b.end_date
        )and t.voided=0 and t.user_id_id = {user} and t.active = 'active'
        and t.interval='custom'  and t.end_date >= '{today}') zero_task

		UNION
		select distinct * from
        (
        select t.id,
        t.task_name,
        t.start_date,
        t.end_date,
        t.times,
        t.priority,
        ti.task_item_number
        from (
        select c.task_id,sum(task_item_number) as task_item_number
        from(
        select 
        a.task_id,1 as task_item_number
        from planner_taskitem a
        inner join planner_task b on a.task_id = b.id
        where a.voided = 0 and a.task_item_date >= b.start_date and a.task_item_date <= b.end_date
        ) c
        group by c.task_id) ti
        inner join planner_task t on ti.task_id = t.id
		inner join planner_taskitem pti on t.id = pti.task_id
        where ti.task_item_number < t.times and t.user_id_id ={user}
        and t.active='active'  and t.end_date >= '{today}' and t.interval='custom'
		and pti.task_item_date between t.start_date and t.end_date
		and t.id not in(
			select distinct pti.task_id
			from planner_taskitem pti
			inner join planner_task pt on pti.task_id = pt.id
			where pti.task_item_date between pt.start_date and pt.end_date
			and (pti.status ='pending' or pti.status ='not done') and pt.interval ='custom'
		)
        ) less_task
        """)
        columns = [col[0] for col in cursor.description]
        custom_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        for task in custom_data:
            taskItem = TaskItem()
            taskItem.task_item_date = today
            taskItem.task_item_description = ''
            taskItem.task_item_number = task['task_number'] + 1
            taskItem.user_id = User.objects.get(pk=user)
            taskItem.task = Task.objects.get(pk=task['id'])
            if task['task_number'] > 0:
                taskItem.status = 'pending'
            taskItem.save()