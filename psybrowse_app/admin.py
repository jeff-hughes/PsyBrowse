from datetime import date

from django.contrib import admin

from psybrowse_app.models import (Author, Keyword, Journal, Article,
                                  UserProfile, Subscription)

class AuthorAdmin(admin.ModelAdmin):
    actions_on_top = True
    actions_on_bottom = True
    search_fields = ['first_name', 'last_name']
    fields = (('first_name', 'initials', 'last_name'),
              'flag_conflict',
              'flag_missing')

class JournalAdmin(admin.ModelAdmin):
    actions_on_top = True
    actions_on_bottom = True
    search_fields = ['title']

class PubDateListFilter(admin.SimpleListFilter):
    title = 'By publication date'  # Human-readable title
    parameter_name = 'pub_date'  # Parameter for the filter that will be used
                                 # in the URL query

    def lookups(self, request, model_admin):
        """
        Return a list of tuples. The first element in each tuple is the coded
        value for the option that will appear in the URL query. The second
        element is the human-readable name for the option that will appear in
        the right sidebar.
        """
        return (
            ('1990', '1990s'),
            ('2000', '2000s'),
            ('2010', '2010s'),
        )

    def queryset(self, request, queryset):
        """
        Return the filtered queryset based on the value provided in the query
        string and retrievable via self.value().
        """
        if self.value() == '1990':
            return queryset.filter(pub_date__gte=date(1990, 1, 1),
                                    pub_date__lte=date(1999, 12, 31))
        if self.value() == '2000':
            return queryset.filter(pub_date__gte=date(2000, 1, 1),
                                    pub_date__lte=date(2009, 12, 31))
        if self.value() == '2010':
            return queryset.filter(pub_date__gte=date(2010, 1, 1),
                                    pub_date__lte=date(2019, 12, 31))

class ArticleAdmin(admin.ModelAdmin):
    actions_on_top = True
    actions_on_bottom = True
    list_display = ('title', 'pub_date', 'get_authors_str')
    list_filter = (PubDateListFilter,)
    search_fields = ['title', 'authors__first_name', 'authors__last_name']
    #raw_id_fields = ('journal',)

class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ['affiliation', 'user__first_name', 'user__last_name',
                     'user__email']

admin.site.register(Author, AuthorAdmin)
admin.site.register(Keyword)
admin.site.register(Journal, JournalAdmin)
admin.site.register(Article, ArticleAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
#admin.site.register(Subscription)