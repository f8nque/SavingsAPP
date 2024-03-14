from django.contrib import admin
from . import models
admin.site.register(models.Chart)
admin.site.register(models.Allocate)
admin.site.register(models.Transact)
admin.site.register(models.Transfer)
