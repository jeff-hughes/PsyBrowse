#!/usr/bin/env python

from django.contrib.auth.models import User

from psybrowse_app.models import UserProfile

if User.objects.count() == 0:
    admin = User.objects.create(username='jeff.hughes@gmail.com')
    admin.set_password('admin')
    admin.email = admin.username  # username and email are the same
    admin.first_name = 'Jeff'
    admin.last_name = 'Hughes'
    admin.is_superuser = True
    admin.is_staff = True
    admin.save()

    user_profile = UserProfile(user=admin, affiliation='University of Waterloo')
    user_profile.save()