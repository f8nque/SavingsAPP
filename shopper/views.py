from django.shortcuts import render,redirect
from django.views import View
from datetime import datetime
from django.views.generic.edit import CreateView,UpdateView,DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.conf import settings
from django.db import connection
from django.db.models import Sum
import datetime
import calendar
from .models import CategoryItem,ShoppingItem,BoughtItem
from .forms import CategoryForm,ShoppingForm,BoughtForm,ShoppingUpdateForm
from django.contrib.auth.models import User
# Create your views here.
class CategoryView(View,LoginRequiredMixin):
    def get(self,request):
        form = CategoryForm()
        return render(request,'shopper/category_form.html',{'form':form})
    def post(self,request):
        form = CategoryForm(request.POST)
        user = User.objects.get(username=self.request.user)
        if(form.is_valid()):
            category_name = form.cleaned_data['category_name']
            category = CategoryItem()
            category.category_name = category_name
            category.user_id =user
            category.save()
            return redirect('shopping_category_list')
        return render(request, 'shopper/category_form.html', {'form': form})
class CategoryListView(View,LoginRequiredMixin):
    def get(self,request):
        user = User.objects.get(username=self.request.user)
        data = CategoryItem.objects.filter(voided=0,user_id=user)
        return render(request,'shopper/category_list.html',{'data':data})
class CategoryUpdateView(View,LoginRequiredMixin):
    def get(self,request,pk):
        category_obj = CategoryItem.objects.get(pk=pk)
        form = CategoryForm(instance=category_obj)
        return render(request,'shopper/category_update_form.html',{'form':form})
    def post(self,request,pk):
        form = CategoryForm(request.POST)
        category_obj = CategoryItem.objects.get(pk=pk)
        if(form.is_valid()):
            category_name = form.cleaned_data['category_name']
            category_obj.category_name = category_name
            category_obj.save()
            return redirect('shopping_category_list')
        return render(request, 'shopper/category_update_form.html', {'form': form})
class CategoryDeleteView(View,LoginRequiredMixin):
    def get(self,request,pk):
        category_obj = CategoryItem.objects.get(pk=pk)
        return render(request,'shopper/category_delete_form.html',{'obj':category_obj})
    def post(self,request,pk):
        category_obj = CategoryItem.objects.get(pk=pk)
        if(request.POST['submit']=='delete'):
            category_obj.voided=1
            category_obj.save()
        return redirect('shopping_category_list')

#.................................................................................
class ShoppingItemView(View,LoginRequiredMixin):
    def get(self,request):
        user = User.objects.get(username=self.request.user)
        form = ShoppingForm()
        form.fields['category_id'].queryset = CategoryItem.objects.filter(voided=0, user_id=user)
        return render(request,'shopper/shopping_form.html',{'form':form})
    def post(self,request):
        form = ShoppingForm(request.POST)
        user = User.objects.get(username=self.request.user)
        if form.is_valid():
            item_date = form.cleaned_data['item_date']
            item_name = form.cleaned_data['item_name']
            quantity = form.cleaned_data['quantity']
            estimated_price = form.cleaned_data['estimated_price']
            category_id = form.cleaned_data['category_id']
            comment = form.cleaned_data['comment']
            shopping_obj = ShoppingItem()
            shopping_obj.item_date = item_date
            shopping_obj.item_name = item_name
            shopping_obj.quantity = quantity
            shopping_obj.estimated_price=estimated_price
            shopping_obj.category_id=category_id
            shopping_obj.comment = comment
            shopping_obj.user_id =user
            shopping_obj.save()
            return redirect('shopping_list')
        return render(request,'shopper/shopping_form.html', {'form': form})
class ShoppingUpdateView(View,LoginRequiredMixin):
    def get(self,request,pk):
        user = User.objects.get(username=self.request.user)
        shopping_item = ShoppingItem.objects.get(pk=pk)
        form = ShoppingUpdateForm(instance=shopping_item)
        form.fields['category_id'].queryset = CategoryItem.objects.filter(voided=0, user_id=user)
        return render(request,'shopper/shopping_update_form.html',{'form':form})
    def post(self,request,pk):
        form = ShoppingUpdateForm(request.POST)
        user = User.objects.get(username=self.request.user)
        shopping_obj = ShoppingItem.objects.get(pk=pk)
        if form.is_valid():
            item_date = form.cleaned_data['item_date']
            item_name = form.cleaned_data['item_name']
            quantity = form.cleaned_data['quantity']
            estimated_price = form.cleaned_data['estimated_price']
            category_id = form.cleaned_data['category_id']
            comment = form.cleaned_data['comment']
            status = form.cleaned_data['status']
            urgent = form.cleaned_data['urgent']
            shopping_obj.item_date = item_date
            shopping_obj.item_name = item_name
            shopping_obj.quantity = quantity
            shopping_obj.estimated_price=estimated_price
            shopping_obj.category_id=category_id
            shopping_obj.urgent = urgent
            shopping_obj.status=status
            shopping_obj.comment = comment
            shopping_obj.user_id =user
            shopping_obj.save()
            return redirect('shopping_list')
        return render(request,'shopper/shopping_update_form.html', {'form': form})
class ShoppingDeleteView(View,LoginRequiredMixin):
    def get(self,request,pk):
        shop_item = ShoppingItem.objects.get(pk=pk)
        return render(request,'shopper/shopping_delete_form.html',{'obj':shop_item})
    def post(self,request,pk):
        shop_item = ShoppingItem.objects.get(pk=pk)
        if(request.POST['submit']=='delete'):
            shop_item.voided=1
            shop_item.save()
        return redirect('shopping_list')
class ShoppingListView(View,LoginRequiredMixin):
    def get(self,request):
        user = User.objects.get(username=self.request.user)
        with connection.cursor() as cursor:
            cursor.execute("""
            select count(si.item_name) as num
            from shopper_shoppingitem si
            where si.voided = 0
            and si.urgent = 'yes'
            and si.status <> 'completed'
            """)
            columns = [col[0] for col in cursor.description]
            num_urgent = [dict(zip(columns, row)) for row in cursor.fetchall()]


        with connection.cursor() as cursor:
            cursor.execute(f"""
            select si.item_date,
            si.id,
            si.item_name,
            si.quantity,
            si.estimated_price,
            si.comment,
            si.status,
            si.urgent,
            si.category_id_id,
            b.quantity_bought,
            b.amount_paid
            from shopper_shoppingitem si
            left outer join (
            select distinct bi.item_id_id,sum(quantity_bought) as quantity_bought,
            sum(amount_paid) as amount_paid
            from shopper_boughtitem bi
            where bi.voided=0 and bi.user_id_id = {user.id}
            group by bi.item_id_id
            )b on si.id = b.item_id_id
            where si.voided=0
            and si.user_id_id ={user.id} and (si.status="notbought" or si.status="pending")
            order by si.item_date desc
            """)
            columns = [col[0] for col in cursor.description]
            shoppingitems = [dict(zip(columns, row)) for row in cursor.fetchall()]
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select ci.id,
            ci.category_name,
            b.quantity,
            b.quantity_bought,
            b.estimated_price,
            b.amount_paid
            from
            shopper_categoryitem ci
            inner join(
            select distinct
            sum(si.quantity) as quantity,
            sum(si.estimated_price) as estimated_price,
            si.category_id_id,
            sum(b.quantity_bought) as quantity_bought,
            sum(b.amount_paid) as amount_paid
            from shopper_shoppingitem si
            left outer join (
            select distinct bi.item_id_id,sum(quantity_bought) as quantity_bought,
            sum(amount_paid) as amount_paid
            from shopper_boughtitem bi
            where bi.voided=0 and bi.user_id_id = {user.id}
            group by bi.item_id_id
            )b on si.id = b.item_id_id
            where si.voided=0 and (si.status="notbought" or si.status="pending")
            and si.user_id_id ={user.id}
            group by si.category_id_id) b on ci.id = b.category_id_id
            where ci.voided=0 and ci.user_id_id={user.id}
            """)
            columns = [col[0] for col in cursor.description]
            groupdata = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return render(request,'shopper/shopping_list.html',{'data':shoppingitems,'groupdata':groupdata,'num_urgent':num_urgent})

    def post(self,request):
        status = request.POST['status']
        user = User.objects.get(username=self.request.user)
        if(status == "all"):
            with connection.cursor() as cursor:
                cursor.execute(f"""
                        select si.item_date,
                        si.id,
                        si.item_name,
                        si.quantity,
                        si.estimated_price,
                        si.comment,
                        si.status,
                        si.urgent,
                        si.category_id_id,
                        b.quantity_bought,
                        b.amount_paid
                        from shopper_shoppingitem si
                        left outer join (
                        select distinct bi.item_id_id,sum(quantity_bought) as quantity_bought,
                        sum(amount_paid) as amount_paid
                        from shopper_boughtitem bi
                        where bi.voided=0 and bi.user_id_id = {user.id}
                        group by bi.item_id_id
                        )b on si.id = b.item_id_id
                        where si.voided=0
                        and si.user_id_id ={user.id}
                        order by si.item_date desc
                        """)
                columns = [col[0] for col in cursor.description]
                shoppingitems = [dict(zip(columns, row)) for row in cursor.fetchall()]
            with connection.cursor() as cursor:
                cursor.execute(f"""
                        select ci.id,
                        ci.category_name,
                        b.quantity,
                        b.quantity_bought,
                        b.estimated_price,
                        b.amount_paid
                        from
                        shopper_categoryitem ci
                        inner join(
                        select distinct
                        sum(si.quantity) as quantity,
                        sum(si.estimated_price) as estimated_price,
                        si.category_id_id,
                        sum(b.quantity_bought) as quantity_bought,
                        sum(b.amount_paid) as amount_paid
                        from shopper_shoppingitem si
                        left outer join (
                        select distinct bi.item_id_id,sum(quantity_bought) as quantity_bought,
                        sum(amount_paid) as amount_paid
                        from shopper_boughtitem bi
                        where bi.voided=0 and bi.user_id_id = {user.id}
                        group by bi.item_id_id
                        )b on si.id = b.item_id_id
                        where si.voided=0
                        and si.user_id_id ={user.id}
                        group by si.category_id_id) b on ci.id = b.category_id_id
                        where ci.voided=0 and ci.user_id_id={user.id}
                        """)
                columns = [col[0] for col in cursor.description]
                groupdata = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return render(request, 'shopper/shopping_list.html', {'data': shoppingitems, 'groupdata': groupdata})
        else:
            with connection.cursor() as cursor:
                cursor.execute(f"""
                        select si.item_date,
                        si.id,
                        si.item_name,
                        si.quantity,
                        si.estimated_price,
                        si.comment,
                        si.status,
                        si.category_id_id,
                        b.quantity_bought,
                        b.amount_paid
                        from shopper_shoppingitem si
                        left outer join (
                        select distinct bi.item_id_id,sum(quantity_bought) as quantity_bought,
                        sum(amount_paid) as amount_paid
                        from shopper_boughtitem bi
                        where bi.voided=0 and bi.user_id_id = {user.id}
                        group by bi.item_id_id
                        )b on si.id = b.item_id_id
                        where si.voided=0
                        and si.user_id_id ={user.id}  and si.status="{status}"
                        order by si.item_date desc
                        """)
                columns = [col[0] for col in cursor.description]
                shoppingitems = [dict(zip(columns, row)) for row in cursor.fetchall()]
            with connection.cursor() as cursor:
                cursor.execute(f"""
                        select ci.id,
                        ci.category_name,
                        b.quantity,
                        b.quantity_bought,
                        b.estimated_price,
                        b.amount_paid
                        from
                        shopper_categoryitem ci
                        inner join(
                        select distinct
                        sum(si.quantity) as quantity,
                        sum(si.estimated_price) as estimated_price,
                        si.category_id_id,
                        sum(b.quantity_bought) as quantity_bought,
                        sum(b.amount_paid) as amount_paid
                        from shopper_shoppingitem si
                        left outer join (
                        select distinct bi.item_id_id,sum(quantity_bought) as quantity_bought,
                        sum(amount_paid) as amount_paid
                        from shopper_boughtitem bi
                        where bi.voided=0 and bi.user_id_id = {user.id}
                        group by bi.item_id_id
                        )b on si.id = b.item_id_id
                        where si.voided=0
                        and si.user_id_id ={user.id} and si.status="{status}"
                        group by si.category_id_id) b on ci.id = b.category_id_id
                        where ci.voided=0 and ci.user_id_id={user.id}
                        """)
                columns = [col[0] for col in cursor.description]
                groupdata = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return render(request, 'shopper/shopping_list.html', {'data': shoppingitems, 'groupdata': groupdata})

class BoughtItemView(View,LoginRequiredMixin):
    def get(self,request,pk):
        user = User.objects.get(username=self.request.user)
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select si.item_date,
                    si.item_name,
                    si.quantity,
                    si.estimated_price,
                    si.comment,
                    si.status,
                    b.quantity_bought,
                    b.amount_paid
                    from shopper_shoppingitem si
                    left outer join (
                    select distinct bi.item_id_id,sum(quantity_bought) as quantity_bought,
                    sum(amount_paid) as amount_paid
                    from shopper_boughtitem bi
                    where bi.voided=0 and bi.user_id_id = {user.id}
                    group by bi.item_id_id
                    )b on si.id = b.item_id_id
                    where si.voided=0
                    and si.user_id_id ={user.id} and si.id={pk}
                    """)
            columns = [col[0] for col in cursor.description]
            shopper_obj = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
        form = BoughtForm()
        shopping_item = ShoppingItem.objects.get(pk=pk)
        return render(request,'shopper/bought_item_form.html',{'form':form,'obj':shopping_item,'item':shopper_obj})
    def post(self,request,pk):
        form = BoughtForm(request.POST)
        user = User.objects.get(username=self.request.user)
        shopping_item = ShoppingItem.objects.get(pk=pk)
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select sum(bi.quantity_bought) as total_quantity
            from shopper_boughtitem bi
            where bi.voided=0
             and bi.user_id_id={user.id}
             and bi.item_id_id ={pk}
            """)
            columns = [col[0] for col in cursor.description]
            total = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
            total_quantity = total['total_quantity']
        if form.is_valid():
            date_bought = form.cleaned_data['date_bought']
            quantity_bought = form.cleaned_data['quantity_bought']
            amount_paid = form.cleaned_data['amount_paid']
            comment = form.cleaned_data['comment']
            bi_obj = BoughtItem()
            bi_obj.date_bought = date_bought
            bi_obj.quantity_bought = quantity_bought
            bi_obj.amount_paid = amount_paid
            bi_obj.comment = comment
            bi_obj.user_id =user
            bi_obj.item_id = shopping_item
            bi_obj.save()
            if(total_quantity is None):
                t = 0
            else:
                t= total_quantity
            if t + quantity_bought >= shopping_item.quantity:
                shopping_item.status="completed"
            else:
                shopping_item.status="pending"
            shopping_item.save()
            return redirect(f"/shopper/boughtlist/{shopping_item.id}")
        return render(request, 'shopper/bought_item_form.html', {'form': form, 'obj': shopping_item})

class BoughtListView(View,LoginRequiredMixin):
    def get(self,request,pk):
        user = User.objects.get(username=self.request.user)
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select si.item_date,
                    si.item_name,
                    si.quantity,
                    si.estimated_price,
                    si.comment,
                    si.status,
                    b.quantity_bought,
                    b.amount_paid,
                    (si.estimated_price - b.amount_paid) as amount_remaining
                    from shopper_shoppingitem si
                    left outer join (
                    select distinct bi.item_id_id,sum(quantity_bought) as quantity_bought,
                    sum(amount_paid) as amount_paid
                    from shopper_boughtitem bi
                    where bi.voided=0 and bi.user_id_id = {user.id}
                    group by bi.item_id_id
                    )b on si.id = b.item_id_id
                    where si.voided=0
                    and si.user_id_id ={user.id} and si.id={pk}
                    """)
            columns = [col[0] for col in cursor.description]
            shopper_obj = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
        shopping_item = ShoppingItem.objects.get(pk=pk)
        bought_list_data = BoughtItem.objects.filter(voided=0,user_id=user,item_id=shopping_item)
        return render(request,'shopper/bought_list.html',{'data':bought_list_data,'pk':shopping_item.id,'item':shopper_obj})



class BoughtUpdateView(View,LoginRequiredMixin):
    def get(self,request,pk):
        bought_item = BoughtItem.objects.get(pk=pk)
        form = BoughtForm(instance=bought_item)
        shopping_item = ShoppingItem.objects.get(pk=bought_item.item_id.id)
        return render(request,'shopper/bought_update_form.html',{'form':form,'obj':shopping_item})
    def post(self,request,pk):
        bi_obj = BoughtItem.objects.get(pk=pk)
        form = BoughtForm(request.POST)
        user = User.objects.get(username=self.request.user)
        shopping_item = ShoppingItem.objects.get(pk=bi_obj.item_id.id)
        with connection.cursor() as cursor:
            cursor.execute(f"""
            select sum(bi.quantity_bought) as total_quantity
            from shopper_boughtitem bi
            where bi.voided=0
             and bi.user_id_id={user.id}
             and bi.item_id_id ={pk}
            """)
            columns = [col[0] for col in cursor.description]
            total = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
            total_quantity = total['total_quantity']
        if form.is_valid():
            date_bought = form.cleaned_data['date_bought']
            quantity_bought = form.cleaned_data['quantity_bought']
            amount_paid = form.cleaned_data['amount_paid']
            comment = form.cleaned_data['comment']
            if (total_quantity is None):
                t = 0
            else:
                t = total_quantity - bi_obj.quantity_bought
            bi_obj.date_bought = date_bought
            bi_obj.quantity_bought = quantity_bought
            bi_obj.amount_paid = amount_paid
            bi_obj.comment = comment
            bi_obj.user_id =user
            bi_obj.item_id = shopping_item
            bi_obj.save()

            if t + quantity_bought >= shopping_item.quantity:
                shopping_item.status="completed"
            else:
                shopping_item.status="pending"
            shopping_item.save()
            return redirect(f"/shopper/boughtlist/{shopping_item.id}")
        return render(request, 'shopper/bought_update_form.html', {'form': form, 'obj': shopping_item})

class BoughtDeleteView(View,LoginRequiredMixin):
    def get(self,request,pk):
        bought_item = BoughtItem.objects.get(pk=pk)
        return render(request,'shopper/bought_delete_form.html',{'obj':bought_item})
    def post(self,request,pk):
        bought_item = BoughtItem.objects.get(pk=pk)
        user = User.objects.get(username=self.request.user)
        shopping_item = ShoppingItem.objects.get(pk=bought_item.item_id.id)
        with connection.cursor() as cursor:
            cursor.execute(f"""
                    select sum(bi.quantity_bought) as total_quantity
                    from shopper_boughtitem bi
                    where bi.voided=0
                     and bi.user_id_id={user.id}
                     and bi.item_id_id ={pk}
                    """)
            columns = [col[0] for col in cursor.description]
            total = [dict(zip(columns, row)) for row in cursor.fetchall()][0]
            total_quantity = total['total_quantity']
        if(request.POST['submit']=='delete'):
            bought_item.voided=1
            bought_item.save()
            if (total_quantity is None):
                t = 0
            else:
                t = total_quantity - bought_item.quantity_bought
            if t + shopping_item.quantity:
                shopping_item.status="completed"
            else:
                shopping_item.status="pending"
            shopping_item.save()

        return redirect(f"/shopper/boughtlist/{bought_item.item_id.id}")