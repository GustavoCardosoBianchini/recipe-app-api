'''
Customização do admin do core
'''

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# essa biblioteca é importante para questões de tradução uma vez implementada no admin
# não precisamos implementar novamente. Boas Praticas.
from django.utils.translation import gettext_lazy as _

from core import models


class UserAdmin(BaseUserAdmin):
    '''define the admin pages for users.'''

    ordering = ['id']
    list_display = ['email', 'name']

    #fiedlsets precisam ser uma tupla não podem ser mutaveis
    fieldsets = (
        (None, {'fields':('email', 'password')}),
        (
            _('Permissions'),
            {
                'fields':(
                    'is_active',
                    'is_staff',
                    'is_superuser',
                )
            }
        ),
        (_('Hello word'), {'fields': ('last_login',)}),
    )
    # impede que os campos sejam modificados
    readonly_fields = ['last_login']
    add_fieldsets = (
        (None, {
        'classes': ('wide',),
        'fields': (
            'email',
            'password1',
            'password2',
            'name',
            'is_active',
            'is_staff',
            'is_superuser',
        ),
        }),
    )

admin.site.register(models.User, UserAdmin)
admin.site.register(models.Recipe)
admin.site.register(models.Tag)
admin.site.register(models.Ingredient)