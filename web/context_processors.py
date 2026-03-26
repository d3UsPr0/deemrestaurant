from .models import Category
from django.contrib import messages

def cart_items_count(request):
    cart = request.session.get('cart', {})
    count = sum(item['quantity'] for item in cart.values())
    return {'cart_items_count': count}

def categories(request):
    return {'categories': Category.objects.all()}