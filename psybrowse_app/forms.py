from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext, ugettext_lazy as _

from psybrowse_app.models import Article, UserProfile

class SearchForm(forms.Form):
    """A simple search form  for the top of all pages. It includes only one field, 'search'."""
    search = forms.CharField(max_length=1000)


class AdvSearchForm(forms.Form):
    """
    This form includes more specialized search fields, including title, abstract, etc. Users can search for articles
    matching search values in any of these fields.
    """
    title = forms.CharField(required=False)
    abstract = forms.CharField(required=False)
    authors = forms.CharField(required=False)

    type = forms.MultipleChoiceField(choices=Article.TYPES, required=False, initial=Article.TYPE_DICT.keys())
        # initial value set to highlight all types
    journal = forms.CharField(required=False)
    pub_date_from = forms.DateField(label=_('From'), required=False)
    pub_date_to = forms.DateField(label=_('To'), required=False)

    source = forms.MultipleChoiceField(choices=Article.SOURCES, required=False, initial=Article.SOURCE_DICT.keys())
        # initial value set to highlight all sources
    keywords = forms.CharField(required=False)


class CustomUserCreationForm(UserCreationForm):
    """
    A form that creates a user, with no privileges, from the given username, password, and (optionally) affiliation.
    Creates both a Django auth User and a UserProfile.

    The save() method of this custom user form saves the user's email address as both their username and email. In order
    to make this change, a corresponding change to the length of the username field in the database table must be made,
    increasing it to 75 characters. If the database is rebuilt, this change will need to be made again.
    """
    username = forms.EmailField(
        label=_('Email Address'),
        max_length=75,
        help_text=_('Required. 75 characters or fewer. Must be a valid email address.'),
        error_messages={'invalid': _('This value may contain only letters, numbers and @/./+/-/_ characters.')})
    first_name = forms.CharField(label=_('First Name'), max_length=100)
    last_name = forms.CharField(label=_('Last Name'), max_length=100)
    affiliation = forms.CharField(label=_('Affiliation'), max_length=600, required=False)

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.email = user.username  # username and email are the same
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            user_profile = UserProfile(user=user, affiliation=self.cleaned_data['affiliation'])
            user_profile.save()
        return user