from django.db import models
from django.conf import settings
# Create your models here.
class CategoryItem(models.Model):
    category_name = models.CharField(max_length=128)
    voided= models.IntegerField(default=0)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_created= models.DateTimeField(auto_now_add=True)
    date_updated=models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.category_name
class ShoppingItem(models.Model):
    choices = (('notbought','notbought'),('pending','pending'),('completed','completed'))
    item_date = models.DateField()
    item_name = models.CharField(max_length=128)
    quantity = models.IntegerField(default=1)
    estimated_price = models.IntegerField()
    status = models.CharField(max_length=32,choices=choices,default="notbought")
    category_id = models.ForeignKey(CategoryItem,on_delete=models.CASCADE)
    comment = models.CharField(max_length=256,null=True,blank=True)
    urgent = models.CharField(max_length=8,choices=(('yes','yes'),('no','no')),default='no')
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    voided = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.item_name
    class Meta:
        ordering=['-item_date']

class BoughtItem(models.Model):
    date_bought= models.DateField()
    quantity_bought= models.IntegerField()
    amount_paid = models.IntegerField()
    comment = models.CharField(max_length=256,null=True,blank=True)
    item_id = models.ForeignKey(ShoppingItem,on_delete=models.CASCADE)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    voided = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    def __str__(self):
        return str(self.date_bought)
    class Meta:
        ordering=['-date_bought']


