from django.contrib import admin
from . import models
admin.site.register(models.ShoppingItem)
admin.site.register(models.BoughtItem)
admin.site.register(models.CategoryItem)

