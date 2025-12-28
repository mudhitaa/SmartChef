from django.contrib import admin
from .models import Profile, Recipe, Comment, Reply, Follow, Notification

# Register models
admin.site.register(Profile)
admin.site.register(Recipe)
admin.site.register(Comment)
admin.site.register(Reply)
admin.site.register(Follow)
admin.site.register(Notification)

# Register your models here.
