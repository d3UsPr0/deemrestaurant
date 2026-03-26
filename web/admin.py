from django.contrib import admin
from .models import Category, MenuItem, Gallery, Favorite, Order, OrderItem, OrderComment, Booking

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_available', 'is_featured']
    list_filter = ['category', 'is_available', 'is_featured']
    search_fields = ['name', 'description']

@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_featured', 'created_at']
    list_filter = ['is_featured']

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'menu_item', 'created_at']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['menu_item', 'quantity', 'price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'full_name', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'full_name', 'email']
    inlines = [OrderItemInline]
    readonly_fields = ['order_number', 'created_at', 'updated_at']

@admin.register(OrderComment)
class OrderCommentAdmin(admin.ModelAdmin):
    list_display = ['order', 'user', 'rating', 'created_at']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['name', 'event_type', 'event_date', 'event_time', 'number_of_guests']
    list_filter = ['event_type', 'event_date']