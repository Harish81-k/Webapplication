from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponse
import razorpay
from django.http import JsonResponse
from django.conf import settings
from decimal import Decimal


from .forms import SignupForm, LoginForm, ProfileForm
from .models import PaintProduct, Profile
from .cart_session import Cart

# Aliasing for uniform cart implementation 
from App.models import PaintProduct as Paint  

# ==========================================
# 1. CORE / GENERAL VIEWS
# ==========================================

def home(request):
    return render(request, 'index.html')


def about(request):
    return render(request, 'about.html')


# ==========================================
# 2. AUTHENTICATION VIEWS
# ==========================================

def signup(request):
    form = SignupForm()
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            User.objects.create_user(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1']
            )
            messages.success(request, "Account Created Successfully")
            return redirect('login')
            
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Using email as username configuration
            user = authenticate(
                request,
                username=email,
                password=password
            )

            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "Invalid Email or Password")

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ==========================================
# 3. PAINT CATALOG / GALLERY VIEWS
# ==========================================

@login_required
def add_paint_view(request):
    if not request.user.is_superuser:
        return redirect('home')
        
    if request.method == 'POST':
        paint_name = request.POST.get('paint_name')
        rate = request.POST.get('rate')
        color_code = request.POST.get('color_code')
        paint_image = request.FILES.get('paint_image')
        
        PaintProduct.objects.create(
            name=paint_name,
            rate=rate,
            color_code=color_code,
            image=paint_image
        )
        return redirect('gallery')
        
    return render(request, 'add_paint.html')


def gallery_view(request):
    """Fetches all catalog coatings and lists them inside the grid layout."""
    paints = PaintProduct.objects.all().order_by('-id')
    return render(request, 'gallery.html', {'paints': paints})


# ==========================================
# 4. USER PROFILE / DASHBOARD VIEWS
# ==========================================

@login_required
def update_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'profile.html', {'form': form})


@login_required
def profile_dashboard(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'dashboard.html', {'profile': profile})


# ==========================================
# 5. SHOPPING CART VIEWS (HTMX ENABLED)
# ==========================================

def cart_detail(request):
    """Calculates summary pricing and renders the primary cart template interface."""
    cart = Cart(request)
    
    # Calculate numeric balances cleanly before text conversion
    subtotal = sum(float(item['total_price']) for item in cart)
    shipping = 0.00 if subtotal > 5000 or subtotal == 0 else 250.00
    tax = round(subtotal * 0.18, 2)
    total = subtotal + shipping + tax

    context = {
        'cart': cart,
        'subtotal': f"{subtotal:.2f}",
        'tax': f"{tax:.2f}",
        'total': f"{total:.2f}",
    }
    
    return render(request, 'cart.html', context)


@require_POST
def cart_add(request, product_id):
    """Processes product adds from gallery, then maps window redirections securely."""
    cart = Cart(request)
    paint = get_object_or_404(Paint, id=product_id)
    
    quantity = int(request.POST.get('quantity', 1))
    cart.add(product=paint, quantity=quantity)
    
    if request.headers.get('HX-Request'):
        response = HttpResponse(status=204)
        response['HX-Redirect'] = request.build_absolute_uri('/cart/')
        return response
        
    return redirect('cart_detail')


@require_POST
def cart_update(request, product_id):
    """Modifies product item quantity indices directly from cart increment switches."""
    cart = Cart(request)
    paint = get_object_or_404(Paint, id=product_id)
    
    # POST డేటా ని రీడ్ చేయడం
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity <= 0:
        cart.remove(paint)
    else:
        cart.add(product=paint, quantity=quantity, override_quantity=True)
        
    # HTMX టార్గెట్ గ్లిచెస్ రాకుండా ఉండటానికి నేరుగా కార్ట్ పేజీకే రిడైరెక్ట్ చేయండి
    return redirect('cart_detail') # మీ url name 'cart_detail' అయితే అది ఇవ్వండి

@require_POST
def cart_remove(request, product_id):
    """Drops target items entirely from cookie arrays."""
    cart = Cart(request)
    paint = get_object_or_404(Paint, id=product_id)
    
    cart.remove(paint)
    return cart_detail(request)


def checkout_view(request):
    """Renders the final payment selection screen with calculated context variables."""
    try:
        cart = Cart(request)
    except Exception as e:
        return render(request, 'payment_failed.html', {'error': f"Cart system initialization failed: {str(e)}"})
    
    # Safety check: Don't let users visit checkout if the cart is empty
    if not cart or len(cart) == 0:
        return redirect('cart_detail')
        
    # --- మీ కార్ట్ కి సరిపోయేలా ఇక్కడ టోటల్ ని లెక్కించాం ---
    subtotal = sum(float(item['total_price']) for item in cart)
    tax = round(subtotal * 0.18, 2)  # 18% GST allocation format
    total = subtotal + tax
    
    context = {
        'cart': cart,
        'subtotal': f"{subtotal:.2f}",
        'tax': f"{tax:.2f}",
        'total': f"{total:.2f}"
    }
    return render(request, 'proceed_to_order.html', context)


def create_razorpay_order(request):
    if request.method == "POST":
        cart = Cart(request)
        if not cart or len(cart) == 0:
            return JsonResponse({"error": "Your allocation cart context is empty."}, status=400)
            
        subtotal = sum(float(item['total_price']) for item in cart)
        tax = subtotal * 0.18
        total_amount = int((subtotal + tax) * 100) 
        
        try:
            # This now works because razorpay_client is initialized at the top of the file
            razorpay_order = razorpay_client.order.create({
                "amount": total_amount,
                "currency": "INR",
                "payment_capture": "1"
            })
            
            return JsonResponse({
                "razorpay_order_id": razorpay_order['id'],
                "razorpay_merchant_key": settings.RAZORPAY_KEY_ID,
                "amount": total_amount
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
            
    return JsonResponse({"error": "Invalid request method."}, status=405)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem, Profile

@login_required
def place_order(request):
    cart = Cart(request)
    if not cart or len(cart) == 0: 
        return redirect('cart_detail')
        
    if request.method == "POST":
        profile = Profile.objects.filter(user=request.user).first()
        subtotal = sum(float(item['total_price']) for item in cart)
        total_bill = subtotal + (subtotal * 0.18)

        # Create the order
        order = Order.objects.create(
            user=request.user,
            full_name=profile.full_name if profile else request.user.first_name,
            email=request.user.email,
            phone=profile.phone if profile else "Not Provided",
            delivery_address=profile.delivery_address if profile else "Not Provided",
            total_amount=total_bill,
            # Capture the payment method sent from the form
            payment_method=request.POST.get('payment_method', 'COD'),
            # Save Razorpay transaction ID if it exists
            razorpay_order_id=request.POST.get('razorpay_order_id', ''),
            razorpay_payment_id=request.POST.get('razorpay_payment_id', '')
        )

        for item in cart:
            product_obj = item['product']
            OrderItem.objects.create(
                order=order,
                product_name=product_obj.name,
                rate=product_obj.rate,
                quantity=item['quantity'],
                total_price=float(item['total_price'])
            )

        # Clear session
        if 'cart' in request.session:
            del request.session['cart']
            request.session.modified = True

        messages.success(request, f"Order #{order.id} placed successfully!")
        return redirect('order_success')
        
    return redirect('checkout')
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Order, Profile  # ఇక్కడ Profile మోడల్ కచ్చితంగా ఇంపోర్ట్ చేయాలి

@login_required
def order_dash(request):
    # ఆర్డర్స్ పొందండి
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # ప్రొఫైల్ పొందండి (ఒకవేళ యూజర్ కి ప్రొఫైల్ లేకపోతే None వస్తుంది)
    user_profile = Profile.objects.filter(user=request.user).first()
    
    # ఇప్పుడు రెండింటినీ పంపిస్తున్నాము
    return render(request, 'order_dash.html', {
        'orders': user_orders,
        'profile': user_profile 
    })

from django.shortcuts import get_object_or_404

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    # కేవలం 'Pending' లో ఉన్న ఆర్డర్‌లను మాత్రమే క్యాన్సిల్ చేయడానికి అనుమతించండి
    if order.status == 'Pending':
        order.status = 'Cancelled'
        order.save()
        messages.success(request, "Order cancelled successfully.")
    else:
        messages.error(request, "Cannot cancel a dispatched or delivered order.")
    return redirect('order_dash')

@login_required
def delete_order(request, order_id):
    # 1. Fetch the order
    if request.user.is_superuser:
        order = get_object_or_404(Order, id=order_id)
    else:
        # Standard users can ONLY delete their own orders
        order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # 2. Check deletion rules
    can_delete = False
    
    if request.user.is_superuser:
        # Superuser can delete if it is Cancelled OR Delivered
        if order.status in ['Cancelled', 'Delivered']:
            can_delete = True
    else:
        # Standard user can ONLY delete if it is Cancelled
        if order.status == 'Cancelled':
            can_delete = True
            
    # 3. Perform action
    if can_delete:
        order.delete()
        messages.success(request, "Order deleted successfully.")
    else:
        messages.error(request, "You do not have permission to delete this order.")
        
    # 4. Redirect based on role
    if request.user.is_superuser:
        return redirect('admin_orders')
    else:
        return redirect('order_dash')


# App/views.py
from django.shortcuts import render, redirect
from .models import Order, OrderItem, Profile
from django.contrib.auth.decorators import login_required

@login_required
def place_order(request):
    cart = Cart(request)
    if not cart or len(cart) == 0: return redirect('cart_detail')
        
    if request.method == "POST":
        # Ensure profile is fetched safely
        profile = Profile.objects.filter(user=request.user).first()
        
        subtotal = sum(float(item['total_price']) for item in cart)
        total_bill = subtotal + (subtotal * 0.18) # 18% Tax

        order = Order.objects.create(
            user=request.user,
            full_name=profile.full_name if profile else request.user.first_name,
            email=request.user.email,
            phone=profile.phone if profile else "Not Provided",
            delivery_address=profile.delivery_address if profile else "Not Provided",
            total_amount=total_bill,
            payment_method='COD'
        )

        for item in cart:
            product_obj = item['product']
            OrderItem.objects.create(
                order=order,
                product_name=product_obj.name,
                rate=product_obj.rate,
                quantity=item['quantity'],
                total_price=float(item['total_price'])
            )

        if 'cart' in request.session:
            del request.session['cart']
            request.session.modified = True

        messages.success(request, f"Order #{order.id} placed successfully!")
        return redirect('order_success')
    return redirect('checkout')

# అడ్మిన్ కోసం ఆర్డర్స్ చూడటానికి
def admin_orders(request):
    if not request.user.is_superuser:
        return redirect('home')
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'admin_orders.html', {'orders': orders})


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

@login_required
def update_order_status(request, order_id):
    if not request.user.is_superuser:
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        new_status = request.POST.get('status')
        order.status = new_status
        order.save()
        messages.success(request, f"Order #{order_id} status updated to {new_status}")
    
    return redirect('admin_orders')

# views.py
from django.shortcuts import render

def order_success(request):
    return render(request, 'order_success.html') # Ensure this file exists


from django.shortcuts import render
from django.contrib.auth.models import User
from .models import Profile

def admin_user_dashboard(request):
    # Count only non-staff users
    regular_users_count = User.objects.filter(is_staff=False).count()
    
    # Get profiles belonging to non-staff users
    profiles = Profile.objects.select_related('user').filter(user__is_staff=False)
    
    context = {
        'total_users': regular_users_count,
        'profiles': profiles,
    }
    return render(request, 'admin_dashboard.html', context)

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

@staff_member_required
def delete_paint(request, paint_id):
    if request.method == 'DELETE':
        paint = get_object_or_404(Paint, id=paint_id)
        paint.delete()
        return HttpResponse("") # Returns empty response to HTMX
    return HttpResponse(status=405) # Method Not Allowed
