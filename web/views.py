from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Category, MenuItem, Gallery, Favorite, Order, OrderItem, Booking
from .forms import OrderForm, BookingForm, OrderCommentForm
import json
from decimal import Decimal
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from django.contrib.auth.models import User
from .models import UserProfile


def home(request):
    featured_items = MenuItem.objects.filter(is_featured=True)[:6]
    gallery_items = Gallery.objects.filter(is_featured=True)[:6]
    context = {
        'featured_items': featured_items,
        'gallery_items': gallery_items,
    }
    return render(request, 'web/home.html', context)

def menu_list(request):
    category_slug = request.GET.get('category')
    search_query = request.GET.get('search')
    
    menu_items = MenuItem.objects.filter(is_available=True)
    
    if category_slug:
        menu_items = menu_items.filter(category__slug=category_slug)
    
    if search_query:
        menu_items = menu_items.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    categories = Category.objects.all()
    
    context = {
        'menu_items': menu_items,
        'categories': categories,
        'selected_category': category_slug,
    }
    return render(request, 'web/menu_list.html', context)

def menu_detail(request, pk):
    menu_item = get_object_or_404(MenuItem, pk=pk, is_available=True)
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, menu_item=menu_item).exists()
    
    context = {
        'menu_item': menu_item,
        'is_favorite': is_favorite,
    }
    return render(request, 'web/menu_detail.html', context)

def gallery(request):
    gallery_items = Gallery.objects.all()
    return render(request, 'web/gallery.html', {'gallery_items': gallery_items})

def about(request):
    return render(request, 'web/about.html')

def contact(request):
    return render(request, 'web/contact.html')

def booking(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            if request.user.is_authenticated:
                booking.user = request.user
            booking.save()
            messages.success(request, 'Booking request submitted successfully! We will contact you soon.')
            return redirect('web:booking_success')
    else:
        form = BookingForm()
    
    return render(request, 'web/booking.html', {'form': form})

def booking_success(request):
    return render(request, 'web/booking_success.html')

def add_to_cart(request):
    if request.method == 'POST':
        menu_item_id = request.POST.get('menu_item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        menu_item = get_object_or_404(MenuItem, pk=menu_item_id)
        
        cart = request.session.get('cart', {})
        
        if menu_item_id in cart:
            cart[menu_item_id]['quantity'] += quantity
        else:
            cart[menu_item_id] = {
                'name': menu_item.name,
                'price': str(menu_item.price),
                'quantity': quantity,
                'image': menu_item.image.url if menu_item.image else None,
            }
        
        request.session['cart'] = cart
        request.session.modified = True
        
        messages.success(request, f'{menu_item.name} added to cart!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': sum(item['quantity'] for item in cart.values())
            })
        
        return redirect('web:view_cart')
    
    return redirect('web:menu_list')

def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = Decimal('0.00')
    
    for item_id, item_data in cart.items():
        try:
            menu_item = MenuItem.objects.get(pk=item_id)
            subtotal = Decimal(item_data['price']) * item_data['quantity']
            total += subtotal
            cart_items.append({
                'id': item_id,
                'name': item_data['name'],
                'price': Decimal(item_data['price']),
                'quantity': item_data['quantity'],
                'subtotal': subtotal,
                'image': menu_item.image.url if menu_item.image else None,
            })
        except MenuItem.DoesNotExist:
            continue
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'web/cart.html', context)

def update_cart(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        action = request.POST.get('action')
        
        cart = request.session.get('cart', {})
        
        if item_id in cart:
            if action == 'increase':
                cart[item_id]['quantity'] += 1
            elif action == 'decrease':
                if cart[item_id]['quantity'] > 1:
                    cart[item_id]['quantity'] -= 1
                else:
                    del cart[item_id]
            elif action == 'remove':
                del cart[item_id]
        
        request.session['cart'] = cart
        request.session.modified = True
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Your cart is empty!')
        return redirect('web:menu_list')
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            
            # Calculate total
            total = Decimal('0.00')
            for item_id, item_data in cart.items():
                total += Decimal(item_data['price']) * item_data['quantity']
            
            order.total_amount = total
            order.user = request.user if request.user.is_authenticated else None
            order.save()
            
            # Create order items
            for item_id, item_data in cart.items():
                menu_item = MenuItem.objects.get(pk=item_id)
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item_data['quantity'],
                    price=item_data['price']
                )
            
            # Clear cart
            request.session['cart'] = {}
            request.session.modified = True
            
            messages.success(request, 'Order placed successfully! Your order number is ' + order.order_number)
            
            # TODO: Send notification to manager via SMS
            # You can integrate with SMS services like Twilio here
            
            return redirect('web:order_success', order_number=order.order_number)
    else:
        form = OrderForm()
    
    return render(request, 'web/checkout.html', {'form': form})

def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'web/order_success.html', {'order': order})

@login_required
def toggle_favorite(request, menu_item_id):
    menu_item = get_object_or_404(MenuItem, pk=menu_item_id)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        menu_item=menu_item
    )
    
    if not created:
        favorite.delete()
        is_favorite = False
        message = 'Removed from favorites'
    else:
        is_favorite = True
        message = 'Added to favorites'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_favorite': is_favorite,
            'message': message
        })
    
    messages.success(request, message)
    return redirect('web:menu_detail', pk=menu_item_id)

@login_required
def favorites(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('menu_item')
    return render(request, 'web/favorites.html', {'favorites': favorites})

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'web/my_orders.html', {'orders': orders})

@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    if request.method == 'POST':
        form = OrderCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.order = order
            comment.user = request.user
            comment.save()
            messages.success(request, 'Comment added successfully!')
            return redirect('web:order_detail', order_number=order_number)
    else:
        form = OrderCommentForm()
    
    return render(request, 'web/order_detail.html', {
        'order': order,
        'form': form
    })
    
def get_cart_count(request):
    cart = request.session.get('cart', {})
    count = sum(item['quantity'] for item in cart.values())
    return JsonResponse({'count': count})

def register(request):
    if request.user.is_authenticated:
        return redirect('web:home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            
            # Log the user in after registration
            login(request, user)
            messages.success(request, f'Welcome {user.first_name}! Your account has been created successfully.')
            return redirect('web:home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'web/register.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('web:home')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Check if login is email or username
            if '@' in username:
                try:
                    user_obj = User.objects.get(email=username)
                    username = user_obj.username
                except User.DoesNotExist:
                    pass
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # 🔥 THIS FIXES THE ERROR - Creates profile if it doesn't exist
                try:
                    profile = user.profile
                except UserProfile.DoesNotExist:
                    UserProfile.objects.create(user=user)
                
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                
                # Redirect to next parameter if exists
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('web:home')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'web/login.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('web:home')

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('web:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    # Get user's orders
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'form': form,
        'orders': orders,
    }
    return render(request, 'web/profile.html', context)