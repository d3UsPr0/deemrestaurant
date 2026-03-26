from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard, name='dashboard'),
    
    # Order management
    path('orders/', views.order_list, name='order_list'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    
    # Menu management
    path('menu/', views.menu_management, name='menu_management'),
    path('menu/add/', views.menu_item_add, name='menu_item_add'),
    path('menu/<int:pk>/edit/', views.menu_item_edit, name='menu_item_edit'),
    path('menu/<int:pk>/delete/', views.menu_item_delete, name='menu_item_delete'),
    
    # Booking management
    path('bookings/', views.booking_list, name='booking_list'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
]