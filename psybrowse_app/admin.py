from django.contrib import admin

# Register your models here.
from psybrowse_app.models import Author, Keyword, Journal, Article, UserProfile, Subscription
admin.site.register(Author)
admin.site.register(Keyword)
admin.site.register(Journal)
admin.site.register(Article)
admin.site.register(UserProfile)
admin.site.register(Subscription)