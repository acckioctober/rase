from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class CustomUserAdmin(UserAdmin):
    # Добавление новых полей в список отображаемых полей
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'photo', 'date_birth')

    # Добавление полей в форму редактирования
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ('photo', 'date_birth')}),
    )

    # Добавление полей в форму создания пользователя
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {'fields': ('photo', 'date_birth')}),
    )


admin.site.register(User, CustomUserAdmin)



# admin.site.register(User, UserAdmin)
