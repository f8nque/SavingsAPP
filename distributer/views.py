from django.shortcuts import render,redirect
from django.views import View
from .models import Chart,Transact,Transfer,Allocate
from .forms import ChartForm,TransactForm,TransferForm,AllocateForm
from datetime import datetime
from django.views.generic.edit import CreateView,UpdateView,DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.conf import settings
from django.db import connection
from django.db.models import Sum
import datetime
import calendar
# Create your views here.

class ChartRegistrationView(View,LoginRequiredMixin):
    login_url = settings.LOGIN_URL

    def get(self, request, *args, **kwargs):
        form = ChartForm()
        return render(request, 'distributer/chart_form.html', {'form': form})

    def post(self, request, *args, **kwargs):
        user = User.objects.get(username=self.request.user)  # get the logged in user
        form = ChartForm(request.POST)
        if form.is_valid():
            chart_date = form.cleaned_data['chart_date']
            chart_name = form.cleaned_data['chart_name']
            status = form.cleaned_data['status']
            perc = form.cleaned_data['perc']
            priority = form.cleaned_data['priority']
            # add to the Credit Table
            chart = Chart()
            chart.chart_date = chart_date
            chart.chart_name = chart_name
            chart.status = status
            chart.perc = perc
            chart.priority = priority
            chart.user_id = user
            chart.save()  # commit to the database
        else:
            return render(request, 'distributer/chart_form.html', {'form': form})
        return redirect('chart_list')

class ChartListView(View,LoginRequiredMixin):
    login_url = settings.LOGIN_URL
    def get(self,request,*args,**kwargs):
        user = User.objects.get(username=self.request.user)
        with connection.cursor() as cursor:
            cursor.execute(f"""
            SELECT sum(c.perc) as allocate_percentage
            from distributer_chart c
            where c.voided = 0 and c.user_id_id={user.id}
            and c.status="active"
            """)
            columns = [col[0] for col in cursor.description]
            perc = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
        chart_list = Chart.objects.filter(voided=0,user_id= user).order_by('status','priority')
        return render(request,'distributer/chart_list.html',{'chart_list':chart_list,'perc':perc})

class ChartUpdateView(View,LoginRequiredMixin):
    login_url = settings.LOGIN_URL
    def get(self,request,pk):
        chart = Chart.objects.get(pk=pk)
        form = ChartForm(instance=chart)
        return render(request,'distributer/chart_update_form.html',{'form':form})
    def post(self,request,pk):
        #user = User.objects.get(username=self.request.user)  # get the logged in user
        chart = Chart.objects.get(pk=pk)
        form = ChartForm(request.POST)
        if form.is_valid():
            chart_date = form.cleaned_data['chart_date']
            chart_name = form.cleaned_data['chart_name']
            status = form.cleaned_data['status']
            perc = form.cleaned_data['perc']
            priority = form.cleaned_data['priority']
            # add to the Credit Table
            chart.chart_date = chart_date
            chart.chart_name = chart_name
            chart.status = status
            chart.perc = perc
            chart.priority = priority
            chart.save()  # commit to the database
        else:
            return render(request, 'distributer/chart_update_form.html', {'form': form})
        return redirect('chart_list')

class ChartDeleteView(View,LoginRequiredMixin):
    def get(self,request,pk):
        chart = Chart.objects.get(pk=pk)
        return render(request,'distributer/chart_delete_form.html',{'chart':chart})
    def post(self,request,pk):
        chart = Chart.objects.get(pk=pk)
        print(request.POST['submit'])
        if(request.POST['submit']=='delete'):
            chart.voided =1
            chart.save()
            return redirect('chart_list')
        else:
            return redirect('chart_list')

class AllocateEntryView(View,LoginRequiredMixin):
    def get(self,request):
        form = AllocateForm()
        return render(request,'distributer/transact_form.html',{'form':form})
    def post(self,request):
        form = AllocateForm(request.POST)
        user = User.objects.get(username=self.request.user)
        if form.is_valid():
            alloc_date = form.cleaned_data['allocate_date']
            alloc_amount = form.cleaned_data['allocate_amount']
            comment = form.cleaned_data['comment']
            all_table = Allocate()
            all_table.allocate_date = alloc_date
            all_table.allocate_amount = alloc_amount
            all_table.comment = comment
            all_table.user_id = user
            all_table.save()
            #part 2 distribute the amount allocated to the charts.
            chart = Chart.objects.filter(status="active",voided=0)
            for c in chart:
                t = Transact()
                t.transact_allocation=c.perc
                t.transact_date = alloc_date
                t.chart_id = c
                t.allocate_id = all_table
                t.allocated_amount = int(c.perc * 0.01 * alloc_amount)
                t.user_id = user
                t.save()
            return redirect('transaction_list')
class AllocateUpdateView(View,LoginRequiredMixin):
    def get(self,request,pk):
        allocate_obj = Allocate.objects.get(pk=pk)
        form = AllocateForm(instance=allocate_obj)
        return render(request, 'distributer/transact_update_form.html', {'form': form})
    def post(self,request,pk):
        allocate_obj = Allocate.objects.get(pk=pk)
        form = AllocateForm(request.POST)
        if(form.is_valid()):
            allocate_date = form.cleaned_data['allocate_date']
            allocate_amount = form.cleaned_data['allocate_amount']
            comment = form.cleaned_data['comment']
            allocate_obj.allocate_date =allocate_date
            allocate_obj.allocate_amount  = allocate_amount
            allocate_obj.comment = comment
            allocate_obj.save()
            return redirect('transaction_list')

class AllocateDeleteView(View,LoginRequiredMixin):
    def get(self,request,pk):
        alloc_obj = Allocate.objects.get(pk=pk)
        return render(request,'distributer/allocate_delete_form.html',{'obj':alloc_obj})
    def post(self,request,pk):
        alloc_obj = Allocate.objects.get(pk=pk)
        if(request.POST['submit']=='delete'):
            alloc_obj.delete() #do a permanent delete
        return redirect('transaction_list')



class TransactionListView(View,LoginRequiredMixin):
    def get(self,request):
        user = User.objects.get(username=self.request.user)
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select
            final.id,
            final.allocate_date,
            final.allocate_amount as transacted_amount ,
            sum(final.allocated_amount) as allocated_amount,
            sum(final.transferred_amount) as transferred_amount,
            final.comment
            from(
            select a.id,
             a.allocate_date,
             a.allocate_amount,
             b.chart_name,
             b.allocated_amount,
             b.transferred_amount,
             a.comment
            from distributer_allocate a
            left outer join(
            select
            t.id,
            c.chart_name,
            t.allocate_id_id,
            t.allocated_amount,
            trans.transferred_amount
             from distributer_transact t
            inner join distributer_chart c on t.chart_id_id = c.id
            left outer join (
            select distinct tr.transact_id_id,sum(tr.transfer_amount) as transferred_amount
            from distributer_transfer tr
            where tr.voided=0  and tr.user_id_id={user.id}
            group by tr.transact_id_id
            )trans on t.id = trans.transact_id_id
            where t.voided=0 and t.user_id_id={user.id}) b on a.id = b.allocate_id_id
            where a.voided=0
            and a.user_id_id = {user.id}
            order by a.allocate_date desc) final
            group by final.id
            order by final.allocate_date desc

            """)
            columns = [col[0] for col in cursor.description]
            allocation_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return render(request,'distributer/transaction_list.html',{'data':allocation_data})

class IndividualTransactionView(View,LoginRequiredMixin):
    def get(self,request,pk):
        user = User.objects.get(username=self.request.user)
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select
            final.id,
            final.allocate_date,
            final.allocate_amount as transacted_amount ,
            sum(final.allocated_amount) as allocated_amount,
            sum(final.transferred_amount) as transferred_amount
            from(
            select a.id,
             a.allocate_date,
             a.allocate_amount,
             b.chart_name,
             b.allocated_amount,
             b.transferred_amount,
             b.transact_allocation
            from distributer_allocate a
            left outer join(
            select
            t.id,
            c.chart_name,
            t.allocate_id_id,
            t.allocated_amount,
            t.transact_allocation,
            trans.transferred_amount
             from distributer_transact t
            inner join distributer_chart c on t.chart_id_id = c.id
            left outer join (
            select distinct tr.transact_id_id,sum(tr.transfer_amount) as transferred_amount
            from distributer_transfer tr
            where tr.voided=0  and tr.user_id_id={user.id}
            group by tr.transact_id_id
            )trans on t.id = trans.transact_id_id
            where t.voided=0 and t.user_id_id={user.id}) b on a.id = b.allocate_id_id
            where a.voided=0 and a.id={pk}
            order by a.allocate_date desc) final
            group by final.id
            """)
            columns = [col[0] for col in cursor.description]
            alloc_data = [dict(zip(columns, row)) for row in cursor.fetchall()][0]

        with connection.cursor() as cursor:
            cursor.execute(f"""
            select t.id,
            c.chart_name,
            c.priority,
            t.transact_allocation as perc,
            t.allocated_amount,
            case when tran.transferred_amount is Null then 0
            else tran.transferred_amount end as transferred_amount,
            case when tran.transferred_amount is Null then t.allocated_amount
            else t.allocated_amount - tran.transferred_amount end as amount_remaining
            from distributer_transact t
            inner join distributer_allocate a on t.allocate_id_id = a.id
            inner join distributer_chart c on t.chart_id_id = c.id
            left outer join(
            select distinct
            a.id as transact_id,
            a.chart_id_id,
            sum(a.transfer_amount) as transferred_amount
            from(
            select t.id,
            t.chart_id_id,
            tr.transfer_amount
            from
            distributer_transact t
            left outer join distributer_transfer tr
            on t.id = tr.transact_id_id
            where t.voided=0 and tr.voided=0) a
            group by a.id,a.chart_id_id
            )tran on t.id = tran.transact_id
            where t.voided =0 and a.id={pk} and t.user_id_id= {user.id}
            """)
            columns = [col[0] for col in cursor.description]
            individual_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return render(request,'distributer/individual_transaction_list.html',{'data':individual_data,'item':alloc_data})


class IndividualTransactionForm(View,LoginRequiredMixin):
    def get(self,request,pk):
        user = User.objects.get(username=self.request.user)
        form = TransactForm()
        form.fields['chart_id'].queryset = Chart.objects.filter(voided=0,status='active',user_id=user)
        alloc_item = Allocate.objects.get(pk=pk)
        return render(request,'distributer/individual_transaction_form.html',{'form':form,'alloc_item':alloc_item})
    def post(self,request,pk):
        form = TransactForm(request.POST)
        alloc_item = Allocate.objects.get(pk=pk)
        user = User.objects.get(username=self.request.user)
        if form.is_valid():
            transact_date = form.cleaned_data['transact_date']
            chart_id  = form.cleaned_data['chart_id']
            allocated_amount = form.cleaned_data['allocated_amount']
            transact_obj = Transact()
            transact_obj.transact_date = transact_date
            transact_obj.allocate_id = alloc_item
            transact_obj.chart_id = chart_id
            transact_obj.allocated_amount = allocated_amount
            transact_obj.user_id = user
            transact_obj.save()
            return redirect(f'/allocate/individual_list/{alloc_item.id}')

class IndividualUpdateForm(View,LoginRequiredMixin):
    def get(self,request,pk):
        user = User.objects.get(username=self.request.user)
        transact_item = Transact.objects.get(pk=pk)
        form = TransactForm(instance=transact_item)
        form.fields['chart_id'].queryset = Chart.objects.filter(voided=0, status='active',user_id=user)
        return render(request,'distributer/individual_update_form.html',{'form':form})
    def post(self,request,pk):
        form = TransactForm(request.POST)
        user = User.objects.get(username=self.request.user)
        if form.is_valid():
            transact_date = form.cleaned_data['transact_date']
            chart_id = form.cleaned_data['chart_id']
            allocated_amount = form.cleaned_data['allocated_amount']
            transact_obj = Transact.objects.get(pk=pk)
            transact_obj.transact_date = transact_date
            transact_obj.chart_id = chart_id
            transact_obj.allocated_amount = allocated_amount
            transact_obj.save()
            return redirect(f'/allocate/individual_list/{transact_obj.allocate_id.id}')
class IndividualDeleteView(View,LoginRequiredMixin):
    def get(self,request,pk):
        transaction_obj = Transact.objects.get(pk=pk)
        return render(request,'distributer/individual_transaction_delete_form.html',{'obj':transaction_obj})
    def post(self,request,pk):
        if(request.POST['submit']=='delete'):
            transact_obj = Transact.objects.get(pk=pk)
            transact_obj.voided=1
            transact_obj.save()
        return redirect(f'/allocate/individual_list/{transact_obj.allocate_id.id}')


class TransferIndividualListView(View,LoginRequiredMixin):
    def get(self,request,pk):
        user = User.objects.get(username=self.request.user)
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select tr.id, tr.transfer_date,tr.transfer_amount,tr.comment
            from distributer_transfer tr
            where tr.voided=0 and tr.user_id_id={user.id}
            and tr.transact_id_id = {pk}
            order by tr.transfer_date desc
            """)
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select
            t.transact_date,
            c.chart_name,
            t.allocated_amount,
            tr.transferred_amount,
            case when tr.transferred_amount is Null then
            t.allocated_amount
            else t.allocated_amount - tr.transferred_amount end as remaining_amount
             FROM
            distributer_transact t
            inner join distributer_chart c on t.chart_id_id = c.id
            left outer join(
            select a.transact_id_id, sum(a.transfer_amount) as transferred_amount
            from distributer_transfer a
            where a.voided=0 and a.user_id_id ={user.id}
            group by a.transact_id_id) tr on t.id = tr.transact_id_id
            where t.user_id_id = {user.id} and t.voided=0
            and t.id = {pk}
            """)
            columns = [col[0] for col in cursor.description]
            transact_data = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
        return render(request,'distributer/transfer_individual_list.html',{'pk':pk,'data':data,'transaction':transact_data})

class TransferEntryView(View,LoginRequiredMixin):
    def get(self,request,pk):
        t = Transact.objects.get(pk=pk)
        user = User.objects.get(username=self.request.user)
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select t.transact_date,
            c.chart_name,
            t.allocated_amount,
            tr.transferred_amount,
            case when tr.transferred_amount is Null then
            t.allocated_amount
            else t.allocated_amount - tr.transferred_amount end as remaining_amount
             FROM
            distributer_transact t
            inner join distributer_chart c on t.chart_id_id = c.id
            left outer join(
            select a.transact_id_id, sum(a.transfer_amount) as transferred_amount
            from distributer_transfer a
            where a.voided=0 and a.user_id_id ={user.id}
            group by a.transact_id_id) tr on t.id = tr.transact_id_id
            where t.user_id_id = {user.id} and t.voided=0
            and t.id = {pk}
            """)
            columns = [col[0] for col in cursor.description]
            transact_data = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
        form = TransferForm()
        return render(request,'distributer/transfer_form.html',{'form':form,'pk':pk,'data':transact_data})
    def post(self,request,pk):
        t = Transact.objects.get(pk=pk)
        form = TransferForm(request.POST)
        user = User.objects.get(username=self.request.user)
        if(form.is_valid()):
            transfer_date = form.cleaned_data['transfer_date']
            transfer_amount = form.cleaned_data['transfer_amount']
            comment = form.cleaned_data['comment']
            transfer_obj = Transfer()
            transfer_obj.transfer_date = transfer_date
            transfer_obj.transfer_amount = transfer_amount
            transfer_obj.comment = comment
            transfer_obj.user_id = user
            transfer_obj.transact_id = t
            transfer_obj.save()
            return redirect(f'/allocate/transfer_list/{pk}')
        return render(request,'distributer/transfer_form.html',{'form':form,'pk':pk})


class TransferUpdateView(View,LoginRequiredMixin):
    def get(self,request,pk):
        tr = Transfer.objects.get(pk=pk)
        user = User.objects.get(username=self.request.user)
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select t.transact_date,
            c.chart_name,
            t.allocated_amount,
            tr.transferred_amount,
            case when tr.transferred_amount is Null then
            t.allocated_amount
            else t.allocated_amount - tr.transferred_amount end as remaining_amount
             FROM
            distributer_transact t
            inner join distributer_chart c on t.chart_id_id = c.id
            left outer join(
            select a.transact_id_id, sum(a.transfer_amount) as transferred_amount
            from distributer_transfer a
            where a.voided=0 and a.user_id_id ={user.id}
            group by a.transact_id_id) tr on t.id = tr.transact_id_id
            where t.user_id_id = {user.id} and t.voided=0
            and t.id = {tr.transact_id_id}
            """)
            columns = [col[0] for col in cursor.description]
            transact_data = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
        form = TransferForm(instance=tr)
        return render(request,'distributer/transfer_update_form.html',{'form':form,'pk':pk,'data':transact_data})
    def post(self,request,pk):
        form = TransferForm(request.POST)
        if(form.is_valid()):
            transfer_date = form.cleaned_data['transfer_date']
            transfer_amount = form.cleaned_data['transfer_amount']
            comment = form.cleaned_data['comment']
            transfer_obj = Transfer.objects.get(pk=pk)
            transfer_obj.transfer_date = transfer_date
            transfer_obj.transfer_amount = transfer_amount
            transfer_obj.comment = comment
            transfer_obj.save()
            return redirect(f'/allocate/transfer_list/{transfer_obj.transact_id.id}')
        return render(request,'distributer/transfer_update_form.html',{'form':form,'pk':pk})

class TransferDeleteView(View,LoginRequiredMixin):
    def get(self,request,pk):
        transfer_obj = Transfer.objects.get(pk=pk)
        return render(request,'distributer/transfer_delete_form.html',{'obj':transfer_obj})
    def post(self,request,pk):
        transfer_obj = Transfer.objects.get(pk=pk)
        if(request.POST['submit'] == "delete"):
            transfer_obj.voided=1
            transfer_obj.save()
        return redirect(f'/allocate/transfer_list/{transfer_obj.transact_id.id}')

class ChartReportView(View,LoginRequiredMixin):
    def get(self,request):
        today = datetime.datetime.now()
        start_date_f = datetime.date(today.year,today.month,1)
        end_date_f = datetime.date(today.year,today.month,calendar.monthrange(today.year,today.month)[1])
        start_date = start_date_f.strftime('%Y-%m-%d')
        end_date = end_date_f.strftime('%Y-%m-%d')
        user = User.objects.get(username=self.request.user)
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select sum(a.allocate_amount) as allocated_amount,sum(b.allocated_amount) as transacted_amount,
            sum(b.transferred_amount) as transferred_amount
             from
            distributer_allocate a
            left outer join(
            select t.allocate_id_id,
            sum(t.allocated_amount) as allocated_amount,
            sum(trans.transferred_amount) as transferred_amount
            from distributer_transact t
            left outer join(
            select distinct tr.transact_id_id,sum(tr.transfer_amount) as transferred_amount
            from distributer_transfer tr
            where tr.voided=0 and tr.user_id_id ={user.id}
            group by tr.transact_id_id
            )trans on t.id = trans.transact_id_id
            where t.voided=0 and t.user_id_id = {user.id}
            group by t.allocate_id_id
            )b on a.id = b.allocate_id_id
            where a.voided=0 and a.user_id_id={user.id}
            and a.allocate_date between "{start_date}" and "{end_date}"
            """)
            columns = [col[0] for col in cursor.description]
            consolidated_data = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select chart.chart_name,dist.allocated_amount,dist.transferred_amount
             from
            distributer_chart chart
            inner join (
            select b.chart_id_id,sum(b.allocated_amount) as allocated_amount,
            sum(b.transferred_amount) as transferred_amount
            from(
            select t.transact_date,t.chart_id_id,t.allocated_amount,tr.transferred_amount
            from distributer_transact t
            inner join distributer_chart c on t.chart_id_id = c.id
            left outer join(
            select a.transact_id_id,sum(a.transfer_amount) as transferred_amount
            from distributer_transfer a
            where a.voided=0 and a.user_id_id ={user.id}
            group by a.transact_id_id) tr on t.id = tr.transact_id_id
            where t.voided=0 and t.user_id_id= {user.id}
            and t.transact_date between "{start_date}" and "{end_date}"
            ) b
            group by b.chart_id_id) dist on chart.id = dist.chart_id_id
            """)
            columns = [col[0] for col in cursor.description]
            transaction_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        context={
            'data': transaction_data,
            'start_date_f':start_date_f,
            'end_date_f':end_date_f,
            'start_date':start_date,
            'end_date':end_date,
            'trans_data':consolidated_data,
        }
        return render(request,'distributer/chart_report.html',context)
    def post(self,request):
        try:
            start_date = request.POST['start_date']
            end_date = request.POST['end_date']
            start_date_f= datetime.datetime.strptime(start_date,'%Y-%m-%d')
            end_date_f = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        except:
            today = datetime.datetime.today()
            start_date_f = datetime.date(today.year, today.month, 1)
            end_date_f = datetime.date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
            start_date = start_date_f.strftime('%Y-%m-%d')
            end_date = end_date_f.strftime('%Y-%m-%d')
        user = User.objects.get(username=self.request.user)
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select sum(a.allocate_amount) as allocated_amount,sum(b.allocated_amount) as transacted_amount,
            sum(b.transferred_amount) as transferred_amount
             from
            distributer_allocate a
            left outer join(
            select t.allocate_id_id,
            sum(t.allocated_amount) as allocated_amount,
            sum(trans.transferred_amount) as transferred_amount
            from distributer_transact t
            left outer join(
            select distinct tr.transact_id_id,sum(tr.transfer_amount) as transferred_amount
            from distributer_transfer tr
            where tr.voided=0 and tr.user_id_id ={user.id}
            group by tr.transact_id_id
            )trans on t.id = trans.transact_id_id
            where t.voided=0 and t.user_id_id = {user.id}
            group by t.allocate_id_id
            )b on a.id = b.allocate_id_id
            where a.voided=0 and a.user_id_id={user.id}
            and a.allocate_date between "{start_date}" and "{end_date}"
            """)
            columns = [col[0] for col in cursor.description]
            consolidated_data = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select chart.chart_name,dist.allocated_amount,dist.transferred_amount
                     from
                    distributer_chart chart
                    inner join (
                    select b.chart_id_id,sum(b.allocated_amount) as allocated_amount,
                    sum(b.transferred_amount) as transferred_amount
                    from(
                    select t.transact_date,t.chart_id_id,t.allocated_amount,tr.transferred_amount
                    from distributer_transact t
                    inner join distributer_chart c on t.chart_id_id = c.id
                    left outer join(
                    select a.transact_id_id,sum(a.transfer_amount) as transferred_amount
                    from distributer_transfer a
                    where a.voided=0 and a.user_id_id ={user.id}
                    group by a.transact_id_id) tr on t.id = tr.transact_id_id
                    where t.voided=0 and t.user_id_id= {user.id}
                    and t.transact_date between "{start_date}" and "{end_date}"
                    ) b
                    group by b.chart_id_id) dist on chart.id = dist.chart_id_id
                    """)
            columns = [col[0] for col in cursor.description]
            transaction_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        context = {
            'data': transaction_data,
            'start_date_f': start_date_f,
            'end_date_f': end_date_f,
            'start_date': start_date,
            'end_date': end_date,
            'trans_data': consolidated_data,
        }
        return render(request, 'distributer/chart_report.html', context)


class TransferReportView(View,LoginRequiredMixin):
    def get(self,request):
        today = datetime.datetime.now()
        start_date_f = datetime.date(today.year,today.month,1)
        end_date_f = datetime.date(today.year,today.month,calendar.monthrange(today.year,today.month)[1])
        start_date = start_date_f.strftime('%Y-%m-%d')
        end_date = end_date_f.strftime('%Y-%m-%d')
        user = User.objects.get(username=self.request.user)
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select sum(p.allocate_amount) as allocated_amount,
            sum(p.transacted_amount) as transacted_amount,
            sum(p.transferred_amount) as transferred_amount
            from(
            select x.id,x.allocate_amount,y.transacted_amount,z.transferred_amount
            from(
            SELECT distinct a.id,a.allocate_date,a.allocate_amount FROM distributer_transfer tr
            inner join distributer_transact t on tr.transact_id_id = t.id
            inner join distributer_allocate a on t.allocate_id_id = a.id
            where tr.voided =0 and t.voided =0 and a.voided= 0 and
            tr.user_id_id = {user.id} and t.user_id_id = {user.id} and a.user_id_id = {user.id}
            and tr.transfer_date between "{start_date}" and "{end_date}") x
            left outer join (
            select distinct id,sum(allocated_amount) as transacted_amount
            from(
            SELECT distinct  a.id,t.id as alloc_id,t.transact_date,t.allocated_amount FROM distributer_transfer tr
            inner join distributer_transact t on tr.transact_id_id = t.id
            inner join distributer_allocate a on t.allocate_id_id = a.id
            where tr.voided =0 and t.voided =0 and a.voided= 0
            and tr.user_id_id = {user.id} and t.user_id_id = {user.id} and a.user_id_id = {user.id}
            and tr.transfer_date between "{start_date}" and "{end_date}") transacted
            group by id
            )y on x.id = y.id
            left outer join (
            select distinct trans.id,sum(trans.transfer_amount) as transferred_amount
            from(
            SELECT distinct a.id,tr.id as transfer_id,tr.transfer_date, tr.transfer_amount FROM distributer_transfer tr
            inner join distributer_transact t on tr.transact_id_id = t.id
            inner join distributer_allocate a on t.allocate_id_id = a.id
            where tr.voided =0 and t.voided =0 and a.voided= 0 and
            tr.user_id_id = {user.id} and t.user_id_id = {user.id} and a.user_id_id = {user.id}
            and tr.transfer_date between "{start_date}" and "{end_date}" ) trans
            group by id

            )z on x.id = z.id)p
            """)
            columns = [col[0] for col in cursor.description]
            consolidated_data = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
        with connection.cursor() as cursor:
            cursor.execute(f"""
            SELECT a.id,a.allocate_date, a.allocate_amount,t.transact_date,t.allocated_amount,tr.transfer_date, tr.transfer_amount,tr.comment
            FROM distributer_transfer tr
            inner join distributer_transact t on tr.transact_id_id = t.id
            inner join distributer_allocate a on t.allocate_id_id = a.id
            where tr.voided =0 and tr.user_id_id = {user.id}
            and tr.transfer_date between "{start_date}" and "{end_date}"
            order by a.allocate_date desc,tr.transfer_date desc
            """)
            columns = [col[0] for col in cursor.description]
            transaction_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        context={
            'data': transaction_data,
            'start_date_f':start_date_f,
            'end_date_f':end_date_f,
            'start_date':start_date,
            'end_date':end_date,
            'trans_data':consolidated_data,
            'amount_remaining':consolidated_data.get('transacted_amount',0)-consolidated_data.get('transferred_amount',0),
            'transfer_deficit': consolidated_data.get('allocated_amount',0)-consolidated_data.get('transacted_amount',0),
        }
        return render(request,'distributer/transfer_report.html',context)
    def post(self,request):
        try:
            start_date = request.POST['start_date']
            end_date = request.POST['end_date']
            start_date_f= datetime.datetime.strptime(start_date,'%Y-%m-%d')
            end_date_f = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        except:
            today = datetime.datetime.today()
            start_date_f = datetime.date(today.year, today.month, 1)
            end_date_f = datetime.date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
            start_date = start_date_f.strftime('%Y-%m-%d')
            end_date = end_date_f.strftime('%Y-%m-%d')
        user = User.objects.get(username=self.request.user)
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select sum(p.allocate_amount) as allocated_amount,
            sum(p.transacted_amount) as transacted_amount,
            sum(p.transferred_amount) as transferred_amount
            from(
            select x.id,x.allocate_amount,y.transacted_amount,z.transferred_amount
            from(
            SELECT distinct a.id,a.allocate_date,a.allocate_amount FROM distributer_transfer tr
            inner join distributer_transact t on tr.transact_id_id = t.id
            inner join distributer_allocate a on t.allocate_id_id = a.id
            where tr.voided =0 and t.voided =0 and a.voided= 0 and
            tr.user_id_id = {user.id} and t.user_id_id = {user.id} and a.user_id_id = {user.id}
            and tr.transfer_date between "{start_date}" and "{end_date}") x
            left outer join (
            select distinct id,sum(allocated_amount) as transacted_amount
            from(
            SELECT distinct  a.id,t.id as alloc_id,t.transact_date,t.allocated_amount FROM distributer_transfer tr
            inner join distributer_transact t on tr.transact_id_id = t.id
            inner join distributer_allocate a on t.allocate_id_id = a.id
            where tr.voided =0 and t.voided =0 and a.voided= 0
            and tr.user_id_id = {user.id} and t.user_id_id = {user.id} and a.user_id_id = {user.id}
            and tr.transfer_date between "{start_date}" and "{end_date}") transacted
            group by id
            )y on x.id = y.id
            left outer join (
            select distinct trans.id,sum(trans.transfer_amount) as transferred_amount
            from(
            SELECT distinct a.id,tr.id as transfer_id,tr.transfer_date, tr.transfer_amount FROM distributer_transfer tr
            inner join distributer_transact t on tr.transact_id_id = t.id
            inner join distributer_allocate a on t.allocate_id_id = a.id
            where tr.voided =0 and t.voided =0 and a.voided= 0 and
            tr.user_id_id = {user.id} and t.user_id_id = {user.id} and a.user_id_id = {user.id}
            and tr.transfer_date between "{start_date}" and "{end_date}" ) trans
            group by id

            )z on x.id = z.id)p
            """)
            columns = [col[0] for col in cursor.description]
            consolidated_data = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    SELECT a.id,a.allocate_date, a.allocate_amount,t.transact_date,t.allocated_amount,tr.transfer_date, tr.transfer_amount,tr.comment
                    FROM distributer_transfer tr
                    inner join distributer_transact t on tr.transact_id_id = t.id
                    inner join distributer_allocate a on t.allocate_id_id = a.id
                    where tr.voided =0 and tr.user_id_id = {user.id}
                    and tr.transfer_date between "{start_date}" and "{end_date}"
                    order by tr.transfer_date desc
                    """)
            columns = [col[0] for col in cursor.description]
            transaction_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        context = {
            'data': transaction_data,
            'start_date_f': start_date_f,
            'end_date_f': end_date_f,
            'start_date': start_date,
            'end_date': end_date,
            'trans_data': consolidated_data,
        }
        return render(request, 'distributer/transfer_report.html', context)

