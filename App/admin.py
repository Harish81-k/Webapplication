from django.contrib import admin
from .models import PaintProduct, Profile, Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline] # ఆర్డర్ లోపల ఐటమ్స్ కనిపించడానికి

admin.site.register(PaintProduct)
admin.site.register(Profile)