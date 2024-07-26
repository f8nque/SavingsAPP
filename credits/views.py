from django.shortcuts import render,redirect,get_object_or_404

# Create your views here.
from datetime import datetime
from django.views.generic.edit import CreateView,UpdateView,DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from .forms import DebtRegistrationForm,DebtServiceForm
from django.views import View
from django.conf import settings
from .models import Credit,CreditService
from django.db import connection

class DebtRegistrationView(LoginRequiredMixin,View):
    login_url = settings.LOGIN_URL
    def get(self,request,*args,**kwargs):
        form = DebtRegistrationForm()
        return render(request,'credits/debt_registration_form.html',{'form':form})
    def post(self,request,*args,**kwargs):
        user = User.objects.get(username=self.request.user)#get the logged in user
        form = DebtRegistrationForm(request.POST)
        if form.is_valid():
            credit_date = form.cleaned_data['credit_date']
            credit_agency = form.cleaned_data['credit_agency']
            amount = form.cleaned_data['amount']
            credit_service_date = form.cleaned_data['credit_service_date']
            comment=form.cleaned_data['comment']
            #add to the Credit Table
            credit = Credit()
            credit.credit_date = credit_date
            credit.credit_agency = credit_agency
            credit.amount = amount
            credit.credit_service_date = credit_service_date
            credit.comment = comment
            credit.user_id = user

            credit.save()#commit to the database
        else:
            return render(request,'credits/debt_registration_form.html',{'form':form})
        return redirect('debt_list')

class DebtServiceView(LoginRequiredMixin,View):
    def get(self,request,*args,**kwargs):
        login = settings.LOGIN_URL
        user = User.objects.get(username=self.request.user)
        form = DebtServiceForm(user)
        return render(request,'credits/debt_service_form.html',{'form':form})
    def post(self,request,*args,**kwargs):
        user =  User.objects.get(username=self.request.user)#get the logged in user
        form = DebtServiceForm(user,request.POST)
        if form.is_valid():
            debt_id = form.cleaned_data['debt_id']
            amount= form.cleaned_data['amount']
            comment = form.cleaned_data['comment']
            service_date = form.cleaned_data['service_date']
            creditService = CreditService()
            creditService.debt_id=debt_id
            creditService.service_date=service_date
            creditService.amount = amount
            creditService.comment = comment
            creditService.user_id = user
            creditService.save() # commit to the database
            with connection.cursor() as cursor:
                cursor.execute(f"""
                SELECT
                    sum(cs.amount) as total
                     FROM credits_creditservice cs
                     where cs.voided=0 and cs.debt_id_id={debt_id.id}
                """)
                columns = [col[0] for col in cursor.description]
                amount_paid = [dict(zip(columns,row)) for row in cursor.fetchall()]
                if len(amount_paid)>0:
                    amount_paid= amount_paid[0]['total']
                else:
                    amount_paid = 0
                if amount_paid == debt_id.amount:
                    debt_id.paid= 1
                    debt_id.save()
            return redirect('debt_list')
        return render(request,'credits/debt_service_form.html',{'form':form})


#list Debts Summary
class DebtSummaryView(LoginRequiredMixin,View):
    login = settings.LOGIN_URL
    def get(self,request,*args,**kwargs):
        user = User.objects.get(username=self.request.user)
        user_id = user.id
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select final.*
            from(
            SELECT distinct
            c.id,
            c.credit_date,
            c.credit_agency,
            c.amount,
            c.credit_service_date,
            c.comment,
            c.paid,
            case when (c.paid == 0) and date(c.credit_service_date) < CURRENT_DATE
            then "Overdue"
            when (c.paid == 0) and (date(c.credit_service_date) >= CURRENT_DATE) then "In Progress"
            when c.paid=1 then "Debt Paid"
            else "" end as paying_status,
			date('now') as n,

            case when service.amount_paid == c.amount then "Fully Paid"
            when service.amount_paid is not null then "Partially Paid"
            else "Not Paid" end as service_status,
            case when service.amount_paid is NULL then 0
             else service.amount_paid end as amount_paid,
			 case when service.amount_paid is NULL then c.amount
			 else c.amount - service.amount_paid end as amount_remaining
             FROM credits_credit c
             left outer join (
             SELECT
             cs.debt_id_id,
             sum(cs.amount) as amount_paid
             FROM credits_creditservice cs
             where cs.voided=0
             group by cs.debt_id_id
             )service on c.id = service.debt_id_id
            where c.voided=0  and c.user_id_id={user_id}
            order by c.credit_date desc) final
            where final.amount_remaining > 0
            """)
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns,row)) for row in cursor.fetchall()]

            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT sum(c.amount) as total_debt
                     FROM credits_credit c
                     where c.voided=0 and c.paid=0 and c.user_id_id={user_id}
                """)
                columns = [col[0] for col in cursor.description]
                debt_owed = [dict(zip(columns,row)) for row in cursor.fetchall()]
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT sum(s.amount) debt_paid
                     FROM credits_credit c
                     inner join (
                     SELECT
                    cs.amount,
                    cs.debt_id_id
                     FROM credits_creditservice cs
                     where cs.voided=0
                     )s on c.id = s.debt_id_id
                     where c.voided=0 and c.paid=0 and c.user_id_id={user_id}
                """)
                columns = [col[0] for col in cursor.description]
                debt_paid = [dict(zip(columns,row)) for row in cursor.fetchall()]

            if len(debt_owed)>0:
                debt_owed= debt_owed[0]['total_debt']
            else:
                debt_owed = 0
            if len(debt_paid)>0:
                debt_paid= debt_paid[0]['debt_paid']
            else:
                debt_paid = 0
            if(debt_paid is None):
                debt_paid = 0
            if(debt_owed is None):
                debt_owed =0
            context ={
                'data':data,
                'debt': (debt_owed-debt_paid),
                'help_text':"PENDING"
                }
            return render(request,"credits/debt_summary_list.html",context)
    def post(self,request):
        user = User.objects.get(username=self.request.user)
        user_id = user.id
        post_data = request.POST['select']
        if post_data == "SETTLED":
            with connection.cursor() as cursor:
                cursor.execute(f"""
                        select final.*
                        from(
                        SELECT distinct
                        c.id,
                        c.credit_date,
                        c.credit_agency,
                        c.amount,
                        c.credit_service_date,
                        c.comment,
                        c.paid,
                        case when (c.paid == 0) and date(c.credit_service_date) < CURRENT_DATE
                        then "Overdue"
                        when (c.paid == 0) and (date(c.credit_service_date) >= CURRENT_DATE) then "In Progress"
                        when c.paid=1 then "Debt Paid"
                        else "" end as paying_status,
                        date('now') as n,

                        case when service.amount_paid == c.amount then "Fully Paid"
                        when service.amount_paid is not null then "Partially Paid"
                        else "Not Paid" end as service_status,
                        case when service.amount_paid is NULL then 0
                         else service.amount_paid end as amount_paid,
                         case when service.amount_paid is NULL then c.amount
                         else c.amount - service.amount_paid end as amount_remaining
                         FROM credits_credit c
                         left outer join (
                         SELECT
                         cs.debt_id_id,
                         sum(cs.amount) as amount_paid
                         FROM credits_creditservice cs
                         where cs.voided=0
                         group by cs.debt_id_id
                         )service on c.id = service.debt_id_id
                        where c.voided=0  and c.user_id_id={user_id}
                        order by c.credit_date desc) final
                        where final.amount_remaining <=0
                        """)
                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        elif (post_data == 'PENDING'):
            with connection.cursor() as cursor:
                cursor.execute(f"""
                        select final.*
                        from(
                        SELECT distinct
                        c.id,
                        c.credit_date,
                        c.credit_agency,
                        c.amount,
                        c.credit_service_date,
                        c.comment,
                        c.paid,
                        case when (c.paid == 0) and date(c.credit_service_date) < CURRENT_DATE
                        then "Overdue"
                        when (c.paid == 0) and (date(c.credit_service_date) >= CURRENT_DATE) then "In Progress"
                        when c.paid=1 then "Debt Paid"
                        else "" end as paying_status,
                        date('now') as n,

                        case when service.amount_paid == c.amount then "Fully Paid"
                        when service.amount_paid is not null then "Partially Paid"
                        else "Not Paid" end as service_status,
                        case when service.amount_paid is NULL then 0
                         else service.amount_paid end as amount_paid,
                         case when service.amount_paid is NULL then c.amount
                         else c.amount - service.amount_paid end as amount_remaining
                         FROM credits_credit c
                         left outer join (
                         SELECT
                         cs.debt_id_id,
                         sum(cs.amount) as amount_paid
                         FROM credits_creditservice cs
                         where cs.voided=0
                         group by cs.debt_id_id
                         )service on c.id = service.debt_id_id
                        where c.voided=0  and c.user_id_id={user_id}
                        order by c.credit_date desc) final
                        where final.amount_remaining > 0
                        """)
                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            with connection.cursor() as cursor:
                cursor.execute(f"""
                        select final.*
                        from(
                        SELECT distinct
                        c.id,
                        c.credit_date,
                        c.credit_agency,
                        c.amount,
                        c.credit_service_date,
                        c.comment,
                        c.paid,
                        case when (c.paid == 0) and date(c.credit_service_date) < CURRENT_DATE
                        then "Overdue"
                        when (c.paid == 0) and (date(c.credit_service_date) >= CURRENT_DATE) then "In Progress"
                        when c.paid=1 then "Debt Paid"
                        else "" end as paying_status,
                        date('now') as n,

                        case when service.amount_paid == c.amount then "Fully Paid"
                        when service.amount_paid is not null then "Partially Paid"
                        else "Not Paid" end as service_status,
                        case when service.amount_paid is NULL then 0
                         else service.amount_paid end as amount_paid,
                         case when service.amount_paid is NULL then c.amount
                         else c.amount - service.amount_paid end as amount_remaining
                         FROM credits_credit c
                         left outer join (
                         SELECT
                         cs.debt_id_id,
                         sum(cs.amount) as amount_paid
                         FROM credits_creditservice cs
                         where cs.voided=0
                         group by cs.debt_id_id
                         )service on c.id = service.debt_id_id
                        where c.voided=0  and c.user_id_id={user_id}
                        order by c.credit_date desc) final
                        """)
                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        with connection.cursor() as cursor:
            cursor.execute(f"""
                        SELECT sum(c.amount) as total_debt
                         FROM credits_credit c
                         where c.voided=0 and c.paid=0 and c.user_id_id={user_id}
                    """)
            columns = [col[0] for col in cursor.description]
            debt_owed = [dict(zip(columns, row)) for row in cursor.fetchall()]
        with connection.cursor() as cursor:
            cursor.execute(f"""
                        SELECT sum(s.amount) debt_paid
                         FROM credits_credit c
                         inner join (
                         SELECT
                        cs.amount,
                        cs.debt_id_id
                         FROM credits_creditservice cs
                         where cs.voided=0
                         )s on c.id = s.debt_id_id
                         where c.voided=0 and c.paid=0 and c.user_id_id={user_id}
                    """)
            columns = [col[0] for col in cursor.description]
            debt_paid = [dict(zip(columns, row)) for row in cursor.fetchall()]

        if len(debt_owed) > 0:
            debt_owed = debt_owed[0]['total_debt']
        else:
            debt_owed = 0
        if len(debt_paid) > 0:
            debt_paid = debt_paid[0]['debt_paid']
        else:
            debt_paid = 0
        if (debt_paid is None):
            debt_paid = 0
        if (debt_owed is None):
            debt_owed = 0
        context = {
            'data': data,
            'debt': (debt_owed - debt_paid),
            'help_text':post_data
        }
        return render(request, "credits/debt_summary_list.html", context)


class DebtServiceHistoryView(LoginRequiredMixin,View):
    login = settings.LOGIN_URL
    def get(self,request,pk,*args,**kwargs):
        user = User.objects.get(username=self.request.user)
        user_id = user.id
        debt_record = Credit.objects.get(pk=pk)
        #1.get the debt summary - amount and remaining amount
        #2.service history based on debt id
        # debt owed
        with connection.cursor() as cursor:
            cursor.execute(f"""
             SELECT distinct
            c.credit_date,
            c.credit_agency,
            c.amount,
            c.credit_service_date,
            c.comment,
            c.paid,
            case when (c.paid == 0) and cast(c.credit_service_date as date) > CURRENT_DATE
            then "Overdue"
            when (c.paid == 0) and (cast(c.credit_service_date as date) <= CURRENT_DATE) then "In Progress"
            when c.paid=1 then "Debt Paid"
            else "" end as paying_status,
            case when service.amount_paid == c.amount then "Fully Paid"
            when service.amount_paid is not null then "Partially Paid"
            else "Not Paid" end as service_status,
            case when service.amount_paid is NULL then 0
             else service.amount_paid end as amount_paid,
			 case when service.amount_paid is NULL then c.amount
			 else c.amount - service.amount_paid end as amount_remaining
             FROM credits_credit c
             left outer join (
             SELECT
             cs.debt_id_id,
             sum(cs.amount) as amount_paid
             FROM credits_creditservice cs
             where cs.voided=0
             group by cs.debt_id_id
             )service on c.id = service.debt_id_id
            where c.voided=0 and c.user_id_id={user_id} and c.id={pk}
            order by c.credit_date desc
            """)
            columns = [col[0] for col in cursor.description]
            debt = [dict(zip(columns,row)) for row in cursor.fetchall()]
            if len(debt) > 0:
                debt = debt[0]
            else:
                debt ={}

        debt_history = CreditService.objects.filter(voided=0,user_id=user,debt_id=debt_record)
        context ={
            'debt':debt,
            'data':debt_history,
            }
        return render(request,'credits/debt_history_form.html',context)




class UpdateDebtRegistrationView(LoginRequiredMixin,UpdateView):
    template_name="credits/update_debt_registration_form.html"
    model= Credit
    fields =["credit_date","credit_agency","amount","credit_service_date","comment"]
    pk_url_kwarg ="pk"
    success_url="/credits/debtlist/"
    login_url = settings.LOGIN_URL

class DeleteDebtRegistrationView(LoginRequiredMixin,View):
    template_name="credits/delete_debt_registration_form.html"
    model =Credit
    pk_url_kwarg="pk"
    success_url='/debtlist'
    login_url = settings.LOGIN_URL
    def get(self,request,pk,*args,**kwargs):
        object=get_object_or_404(Credit,pk=pk)
        return render(request,self.template_name,{"obj":object})
    def post(self,request,pk,*args,**kwargs):
        print(request.POST['delete'])
        if request.POST['delete'] == "delete":
            Credit.objects.filter(pk=pk).update(voided=1)
            return redirect('debt_list')
        else:
            return redirect('debt_list')


class UpdateDebtServiceView(LoginRequiredMixin,UpdateView):
    template_name="credits/update_debt_service_form.html"
    model= CreditService
    fields =["debt_id","service_date","amount","comment"]
    pk_url_kwarg ="pk"
    success_url="/credits/debtlist/"
    login_url = settings.LOGIN_URL

class DeleteDebtServiceView(LoginRequiredMixin,View):
    template_name="credits/delete_debt_service_form.html"
    model =CreditService
    pk_url_kwarg="pk"
    success_url='/credits/debtlist'
    login_url = settings.LOGIN_URL
    def get(self,request,pk,*args,**kwargs):
        object=get_object_or_404(self.model,pk=pk)
        return render(request,self.template_name,{"obj":object})
    def post(self,request,pk,*args,**kwargs):
        print(request.POST['delete'])
        if request.POST['delete'] == "delete":
            self.model.objects.filter(pk=pk).update(voided=1)
            return redirect('debt_list')
        else:
            return redirect('debt_list')


class DebtAnalysisSummaryView(LoginRequiredMixin,View):
    def get(self,request):
        year = datetime.now().date().year
        user_id = User.objects.get(username=self.request.user).id
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select a.month,a.year,a.amount_borrowed,
            case when b.amount_paid is null then 0
            else  b.amount_paid end as amount_paid,
            case when b.amount_paid is null then
            cast(a.amount_borrowed as INTEGER) - 0
            else
            cast(a.amount_borrowed as INTEGER) - cast(b.amount_paid as INTEGER) end as amount_remaining,

                        case when a.amount_borrowed > b.amount_paid then "Not settled"
                        else "Settled" end as outcome,
                        case when a.amount_borrowed > b.amount_paid then 0
                        else 1 end as outcome_status
            from (
            select temp_debt_sum.month_id,temp_debt_sum.month,temp_debt_sum.year,sum(temp_debt_sum.amount) as amount_borrowed FROM
            (
            select
            case when cast(strftime('%m',c.credit_date) as INTEGER) = 1 then "January"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 2 then "February"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 3 then "March"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 4 then "April"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 5 then "May"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 6 then "June"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 7 then "July"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 8 then "August"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 9 then "September"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 10 then "October"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 11 then "November"
            else "December"
             end as month,
             strftime('%Y',c.credit_date) as year,
             cast(strftime('%m',c.credit_date) as INTEGER) as month_id,
            c.amount from credits_credit c
            where c.voided = 0 and c.user_id_id={user_id} and strftime('%Y',c.credit_date)="{year}")temp_debt_sum
            group by temp_debt_sum.month,temp_debt_sum.year
            order by temp_debt_sum.month_id desc
            ) a
            left outer join
            (

            select serv_group.month,serv_group.year,sum(serv_group.amount_paid) as amount_paid
            from(
            select
            case when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 1 then "January"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 2 then "February"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 3 then "March"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 4 then "April"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 5 then "May"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 6 then "June"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 7 then "July"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 8 then "August"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 9 then "September"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 10 then "October"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 11 then "November"
            else "December"
             end as month,
             strftime('%Y',serv_temp.credit_date) as year,
             cast(strftime('%m',serv_temp.credit_date) as INTEGER) as month_id,
             serv_temp.amount_paid
            from(
            select c.credit_date,
            case when cs.amount is null then 0
            else cs.amount end as amount_paid
            from
            credits_credit c
            left outer join
            credits_creditservice cs on c.id = cs.debt_id_id
            where cs.voided =0 and c.voided=0 and c.user_id_id={user_id}) serv_temp) serv_group
            group by serv_group.month,serv_group.year
            )b on a.month=b.month and a.year=b.year
            """)
            columns = [col[0] for col in cursor.description]
            monthly_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select distinct
            cast(strftime('%m',c.credit_date) as INTEGER) as id,
            case when cast(strftime('%m',c.credit_date) as INTEGER) = 1 then "January"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 2 then "February"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 3 then "March"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 4 then "April"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 5 then "May"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 6 then "June"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 7 then "July"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 8 then "August"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 9 then "September"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 10 then "October"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 11 then "November"
            else "December"
             end as month
            from credits_credit c
            where
             strftime('%Y',c.credit_date)="{year}"
             and c.voided=0 and c.user_id_id={user_id}
             order by strftime('%m',c.credit_date)
            """)
            columns = [col[0] for col in cursor.description]
            months = [dict(zip(columns, row)) for row in cursor.fetchall()]

        with connection.cursor() as cursor:
            cursor.execute(f"""
            select distinct
            t.credit_agency,cast(strftime('%m',t.credit_date) as INTEGER) as id
            from credits_credit t
            where t.voided=0 and
             t.user_id_id={user_id} and
             strftime('%Y',t.credit_date)="{year}"
             order by
             cast(strftime('%m',t.credit_date) as INTEGER) desc
            """)
            columns = [col[0] for col in cursor.description]
            agencies = [dict(zip(columns, row)) for row in cursor.fetchall()]

        month_agency_data ={}
        for agency in agencies:
            month_data_list= {}
            for month in months:
                month_data_list[month['month']]=0
            month_agency_data[agency['credit_agency']]= month_data_list

        with connection.cursor() as cursor:
            cursor.execute(f"""
            select a.*
            from(
            select distinct m.id,m.month,m.year,m.credit_agency,sum(m.amount) amount_borrowed
            from (
            select
            case when cast(strftime('%m',c.credit_date) as INTEGER) = 1 then "January"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 2 then "February"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 3 then "March"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 4 then "April"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 5 then "May"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 6 then "June"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 7 then "July"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 8 then "August"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 9 then "September"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 10 then "October"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 11 then "November"
            else "December"
             end as month,
             cast(strftime('%m',c.credit_date) as INTEGER) as id,
             strftime('%Y',c.credit_date) as year,
            c.credit_date,
            c.credit_agency,
            c.amount from credits_credit c
            where c.voided = 0 and c.user_id_id={user_id} and strftime('%Y',c.credit_date) ="{year}"
            order by c.credit_date asc
            )m
            group by m.month,m.year,m.credit_agency) a
            order by a.id
            """)
            columns = [col[0] for col in cursor.description]
            agency_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        for d in agency_data:
            month_agency_data[d['credit_agency']][d['month']] =d['amount_borrowed']
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select DISTINCT strftime("%Y",c.credit_date) as year
             from credits_credit c
            where c.voided=0 and c.user_id_id={user_id}
            order by cast(strftime("%Y",c.credit_date) as Integer) desc
            """)
            debt_years = [row[0] for row in cursor.fetchall()]


        #months variable
        months_list = []

        if len(month_agency_data) > 0:
            months_list = list(list(month_agency_data.values())[0].keys())



        context ={
            'monthly_data':monthly_data,
            'agency_data': month_agency_data,
            'months':months_list,
            'debt_years':debt_years,
        }
        return render(request,"credits/debt_analysis_form.html",context)
    def post(self,request):
        year = request.POST['debt_year']
        user_id = User.objects.get(username=self.request.user).id
        with connection.cursor() as cursor:
            cursor.execute(f"""
                   select a.month,a.year,a.amount_borrowed,
            case when b.amount_paid is null then 0
            else  b.amount_paid end as amount_paid,
            case when b.amount_paid is null then
            cast(a.amount_borrowed as INTEGER) - 0
            else
            cast(a.amount_borrowed as INTEGER) - cast(b.amount_paid as INTEGER) end as amount_remaining,

                        case when a.amount_borrowed > b.amount_paid then "Not settled"
                        else "Settled" end as outcome,
                        case when a.amount_borrowed > b.amount_paid then 0
                        else 1 end as outcome_status
            from (
            select temp_debt_sum.month_id,temp_debt_sum.month,temp_debt_sum.year,sum(temp_debt_sum.amount) as amount_borrowed FROM
            (
            select
            case when cast(strftime('%m',c.credit_date) as INTEGER) = 1 then "January"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 2 then "February"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 3 then "March"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 4 then "April"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 5 then "May"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 6 then "June"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 7 then "July"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 8 then "August"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 9 then "September"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 10 then "October"
            when cast(strftime('%m',c.credit_date) as INTEGER) = 11 then "November"
            else "December"
             end as month,
             strftime('%Y',c.credit_date) as year,
             cast(strftime('%m',c.credit_date) as INTEGER) as month_id,
            c.amount from credits_credit c
            where c.voided = 0 and c.user_id_id={user_id} and strftime('%Y',c.credit_date)="{year}")temp_debt_sum
            group by temp_debt_sum.month,temp_debt_sum.year
            order by temp_debt_sum.month_id desc
            ) a
            left outer join
            (

            select serv_group.month,serv_group.year,sum(serv_group.amount_paid) as amount_paid
            from(
            select
            case when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 1 then "January"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 2 then "February"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 3 then "March"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 4 then "April"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 5 then "May"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 6 then "June"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 7 then "July"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 8 then "August"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 9 then "September"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 10 then "October"
            when cast(strftime('%m',serv_temp.credit_date) as INTEGER) = 11 then "November"
            else "December"
             end as month,
             strftime('%Y',serv_temp.credit_date) as year,
             cast(strftime('%m',serv_temp.credit_date) as INTEGER) as month_id,
             serv_temp.amount_paid
            from(
            select c.credit_date,
            case when cs.amount is null then 0
            else cs.amount end as amount_paid
            from
            credits_credit c
            left outer join
            credits_creditservice cs on c.id = cs.debt_id_id
            where cs.voided =0 and c.voided=0 and c.user_id_id={user_id}) serv_temp) serv_group
            group by serv_group.month,serv_group.year
            )b on a.month=b.month and a.year=b.year
                    """)
            columns = [col[0] for col in cursor.description]
            monthly_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select
                    cast(strftime('%m',c.credit_date) as INTEGER) as id,
                    case when cast(strftime('%m',c.credit_date) as INTEGER) = 1 then "January"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 2 then "February"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 3 then "March"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 4 then "April"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 5 then "May"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 6 then "June"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 7 then "July"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 8 then "August"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 9 then "September"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 10 then "October"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 11 then "November"
                    else "December"
                     end as month
                    from credits_credit c
                    where
                     strftime('%Y',c.credit_date)="{year}"
                     and c.voided=0 and c.user_id_id={user_id}
                     order by strftime('%m',c.credit_date)
                    """)
            columns = [col[0] for col in cursor.description]
            months = [dict(zip(columns, row)) for row in cursor.fetchall()]

        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select distinct
                    t.credit_agency,cast(strftime('%m',t.credit_date) as INTEGER) as id
                    from credits_credit t
                    where t.voided=0 and
                     t.user_id_id=1 and
                     strftime('%Y',t.credit_date)="{year}"
                     order by
                     cast(strftime('%m',t.credit_date) as INTEGER) desc
                    """)
            columns = [col[0] for col in cursor.description]
            agencies = [dict(zip(columns, row)) for row in cursor.fetchall()]

        month_agency_data = {}
        for agency in agencies:
            month_data_list = {}
            for month in months:
                month_data_list[month['month']] = 0
            month_agency_data[agency['credit_agency']] = month_data_list

        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select a.*
                    from(
                    select distinct m.id,m.month,m.year,m.credit_agency,sum(m.amount) amount_borrowed
                    from (
                    select
                    case when cast(strftime('%m',c.credit_date) as INTEGER) = 1 then "January"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 2 then "February"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 3 then "March"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 4 then "April"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 5 then "May"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 6 then "June"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 7 then "July"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 8 then "August"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 9 then "September"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 10 then "October"
                    when cast(strftime('%m',c.credit_date) as INTEGER) = 11 then "November"
                    else "December"
                     end as month,
                     cast(strftime('%m',c.credit_date) as INTEGER) as id,
                     strftime('%Y',c.credit_date) as year,
                    c.credit_date,
                    c.credit_agency,
                    c.amount from credits_credit c
                    where c.voided = 0 and c.user_id_id={user_id} and strftime('%Y',c.credit_date) ="{year}"
                    order by c.credit_date asc
                    )m
                    group by m.month,m.year,m.credit_agency) a
                    order by a.id
                    """)
            columns = [col[0] for col in cursor.description]
            agency_data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        for d in agency_data:
            month_agency_data[d['credit_agency']][d['month']] = d['amount_borrowed']
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select DISTINCT strftime("%Y",c.credit_date) as year
                     from credits_credit c
                    where c.voided=0 and c.user_id_id={user_id}
                    order by cast(strftime("%Y",c.credit_date) as Integer) desc
                    """)
            debt_years = [row[0] for row in cursor.fetchall()]

        context = {
            'monthly_data': monthly_data,
            'agency_data': month_agency_data,
            'months': list(list(month_agency_data.values())[0].keys()),
            'debt_years': debt_years,
        }
        return render(request, "credits/debt_analysis_form.html", context)






