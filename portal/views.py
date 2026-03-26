from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from web.models import Order, OrderItem, MenuItem, Category, Booking
from .forms import LoginForm, OrderStatusForm, MenuItemForm
from datetime import timedelta

def is_manager(user):
    return user.is_staff or user.is_superuser

def login_view(request):
    if request.user.is_authenticated:
        return redirect('portal:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('portal:dashboard')
    else:
        form = LoginForm()
    
    return render(request, 'portal/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('portal:login')

@login_required
@user_passes_test(is_manager)
def dashboard(request):
    # Statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    delivered_today = Order.objects.filter(
        status='delivered',
        delivered_at__date=timezone.now().date()
    ).count()
    total_revenue = Order.objects.filter(status='delivered').aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    # Recent orders
    recent_orders = Order.objects.order_by('-created_at')[:10]
    
    # Popular items
    popular_items = OrderItem.objects.values(
        'menu_item__name'
    ).annotate(
        total_ordered=Sum('quantity')
    ).order_by('-total_ordered')[:5]
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_today': delivered_today,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'popular_items': popular_items,
    }
    return render(request, 'portal/dashboard.html', context)

@login_required
@user_passes_test(is_manager)
def order_list(request):
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    orders = Order.objects.all().order_by('-created_at')
    
    if status:
        orders = orders.filter(status=status)
    
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(full_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone_number__icontains=search)
        )
    
    context = {
        'orders': orders,
        'current_status': status,
        'search_query': search,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'portal/order_list.html', context)

@login_required
@user_passes_test(is_manager)
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            old_status = order.status
            order = form.save(commit=False)
            
            # Update timestamps based on status
            if order.status == 'approved' and old_status != 'approved':
                order.approved_at = timezone.now()
            elif order.status == 'delivered' and old_status != 'delivered':
                order.delivered_at = timezone.now()
            
            order.save()
            messages.success(request, f'Order #{order_number} status updated to {order.get_status_display()}')
            return redirect('portal:order_detail', order_number=order_number)
    else:
        form = OrderStatusForm(instance=order)
    
    return render(request, 'portal/order_detail.html', {
        'order': order,
        'form': form
    })

@login_required
@user_passes_test(is_manager)
def menu_management(request):
    menu_items = MenuItem.objects.all().select_related('category').order_by('category__order', 'name')
    categories = Category.objects.all()
    
    return render(request, 'portal/menu_management.html', {
        'menu_items': menu_items,
        'categories': categories,
    })

@login_required
@user_passes_test(is_manager)
def menu_item_add(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item added successfully!')
            return redirect('portal:menu_management')
    else:
        form = MenuItemForm()
    
    return render(request, 'portal/menu_item_form.html', {
        'form': form,
        'title': 'Add Menu Item'
    })

@login_required
@user_passes_test(is_manager)
def menu_item_edit(request, pk):
    menu_item = get_object_or_404(MenuItem, pk=pk)
    
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=menu_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item updated successfully!')
            return redirect('portal:menu_management')
    else:
        form = MenuItemForm(instance=menu_item)
    
    return render(request, 'portal/menu_item_form.html', {
        'form': form,
        'title': 'Edit Menu Item',
        'menu_item': menu_item
    })

@login_required
@user_passes_test(is_manager)
def menu_item_delete(request, pk):
    menu_item = get_object_or_404(MenuItem, pk=pk)
    
    if request.method == 'POST':
        menu_item.delete()
        messages.success(request, 'Menu item deleted successfully!')
        return redirect('portal:menu_management')
    
    return render(request, 'portal/menu_item_confirm_delete.html', {
        'menu_item': menu_item
    })

@login_required
@user_passes_test(is_manager)
def booking_list(request):
    bookings = Booking.objects.all().order_by('-event_date', 'event_time')
    return render(request, 'portal/booking_list.html', {'bookings': bookings})

@login_required
@user_passes_test(is_manager)
def reports(request):
    # Date range filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    orders = Order.objects.all()
    
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)
    
    # Summary statistics
    total_orders = orders.count()
    total_revenue = orders.filter(status='delivered').aggregate(total=Sum('total_amount'))['total'] or 0
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Orders by status
    orders_by_status = orders.values('status').annotate(count=Count('id'))
    
    # Popular items
    popular_items = OrderItem.objects.filter(
        order__in=orders
    ).values(
        'menu_item__name'
    ).annotate(
        total_ordered=Sum('quantity')
    ).order_by('-total_ordered')[:10]
    
    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'orders_by_status': orders_by_status,
        'popular_items': popular_items,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'portal/reports.html', context)