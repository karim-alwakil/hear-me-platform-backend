from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Client, Influencer

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'password1', 'password2'),
        }),
    )

@admin.register(Influencer)
class InfluencerAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'get_phonenumber', 'get_email', 'status', 'iban', 'bank_name')
    list_editable = ('status',)
    list_filter = ('status',)
    search_fields = ('user__username', 'user__email', 'iban')
    raw_id_fields = ('user',)

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

    def get_phonenumber(self, obj):
        return obj.user.phone_number
    get_phonenumber.short_description = 'Phone Number'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'get_phonenumber', 'get_email', 'get_date_joined')
    search_fields = ('user__username', 'user__email')
    raw_id_fields = ('user',)

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def get_date_joined(self, obj):
        return obj.user.date_joined
    get_date_joined.short_description = 'Date Joined'

    def get_phonenumber(self, obj):
        return obj.user.phone_number
    get_phonenumber.short_description = 'Phone Number'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')