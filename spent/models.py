from django.db import models
from django.utils import timezone as tz
from django.conf import settings
from .utils import generateUUID
import uuid


from django.db.models.lookups import In
from django.db.models.fields import Field

@Field.register_lookup
class NotIn(In):
    lookup_name = "notin"
    def get_rhs_op(self, connection, rhs):
        return 'NOT' + connection.operators['in'] %rhs

# class YearlyTheme(models.Model):
#     year = models.DateField()
#     theme = models.CharField(max_length=64)

#     def __str__(self):
#         return self.theme
#     class Meta:
#         ordering =["-year"]


from django.db import models





class BudgetCategory(models.Model):
    name = models.CharField(max_length=32)
    priority= models.IntegerField()
    voided = models.IntegerField(default=0)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_created= models.DateTimeField(auto_now_add=True)
    date_updated=models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class BudgetClassItem(models.Model):
    name = models.CharField(max_length=32)
    budget_category = models.ForeignKey(BudgetCategory,on_delete=models.CASCADE)
    voided = models.IntegerField(default=0)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_created= models.DateTimeField(auto_now_add=True)
    date_updated= models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    date = models.DateField()
    category = models.CharField(max_length=32)
    as_savings=models.BooleanField(default=False)
    budget_category = models.ForeignKey(BudgetClassItem,on_delete=models.CASCADE,blank=True,null=True)
    inactive = models.BooleanField(default=False)
    voided = models.IntegerField(default=0)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.category
    class Meta:
        ordering =["category"]

class Spent(models.Model):
    date = models.DateField()
    category_id = models.ForeignKey(Category,on_delete=models.CASCADE)
    amount = models.IntegerField()
    comment = models.CharField(max_length=256,null=True,blank=True)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    voided = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.date} -- {self.category_id} --{self.amount}"

    class Meta:
        ordering =["-date"]



class Track(models.Model):
    start_date = models.DateField()
    end_date = models.DateField(null=True,blank=True)
    amount = models.IntegerField()
    daily_limit = models.IntegerField(default=0)
    voided = models.IntegerField(default=0)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.start_date}---{self.end_date}---{self.amount}"
    class Meta:
        ordering =["-start_date"]


class Budget(models.Model):
    name = models.CharField(max_length=32)
    description= models.CharField(max_length=128,null=True,blank=True)
    track_id = models.ForeignKey(Track,on_delete=models.CASCADE)
    voided = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    def __str__(self):
        return self.name
    class Meta:
        ordering=['-track_id__start_date']


class BudgetItem(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE)
    budget_class_item = models.ForeignKey(BudgetClassItem,on_delete=models.CASCADE)
    amount = models.IntegerField()
    voided = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

class BudgetLog(models.Model):
    budgetitem = models.ForeignKey(BudgetItem,on_delete=models.CASCADE)
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE)
    budget_class_item = models.ForeignKey(BudgetClassItem,on_delete=models.CASCADE)
    amount = models.IntegerField()
    comment=models.CharField(max_length=256,null=True,blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

class Tracker(models.Model):
    category_id= models.ForeignKey(Category,on_delete=models.CASCADE)
    voided = models.IntegerField(default=0)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    track_id = models.ForeignKey(Track,on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.category_id}-{self.user_id}--{self.track_id}"
class Tracking(models.Model):
    spent_id = models.ForeignKey(Spent,on_delete=models.CASCADE)
    track_id = models.ForeignKey(Track,on_delete=models.CASCADE)
    voided = models.IntegerField(default=0)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.spent_id} ---{self.track_id}"

class SavingsTracker(models.Model):
    spent_id = models.ForeignKey(Spent,on_delete=models.CASCADE)
    voided = models.IntegerField(default=0)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.spent_id)
    class Meta:
        ordering =["-date_created"]

# Create your models here
class WeeklySavingsTracker(models.Model):
    category_id = models.ForeignKey(BudgetClassItem, on_delete=models.CASCADE)
    voided = models.IntegerField(default=0)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    track_id = models.ForeignKey(Track, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.category_id}-{self.user_id}--{self.track_id}"


class SpentWeekBudget(models.Model):
    budget_id = models.ForeignKey(Budget,on_delete=models.CASCADE)
    budget_category_id = models.ForeignKey(BudgetClassItem,on_delete=models.CASCADE)
    week_start = models.DateField()
    week_end = models.DateField()
    budget_amount = models.FloatField(null=True,blank=True)
    budget_spent_start = models.FloatField(null=True,blank=True)
    week_budget = models.FloatField(null=True,blank=True)
    week_spent = models.FloatField(null=True,blank=True)
    week_remaining = models.FloatField(null=True,blank=True)
    bf = models.BooleanField(default=False)
    saved = models.BooleanField(default=False)
    amount_bf = models.FloatField(null=True, blank=True)
    amount_saved = models.FloatField(null=True, blank=True)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    locked = models.BooleanField(default=False)
    voided = models.BooleanField(default=False)
    class Meta:
        db_table = 'spent_week_budget'  # Matches the table name in SQLite

# Create your models here.
