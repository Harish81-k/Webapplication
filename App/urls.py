from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.profile_dashboard, name='dashboard'),
    path('profile/', views.update_profile, name='profile'),


   
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),

    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/create-payment/', views.create_razorpay_order, name='create_razorpay_order'),
    path('checkout/place-order/', views.place_order, name='place_order'),
    path('order-dashboard/', views.order_dash, name='order_dash'),
    path('order/cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('order/delete/<int:order_id>/', views.delete_order, name='delete_order'),
    path('checkout/success/', views.order_success, name='order_success'), 
    

    path('admin-orders/', views.admin_orders, name='admin_orders'),
    path('admin-dashboard/', views.admin_user_dashboard, name='admin_dashboard'),
    path('update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('add/paint/', views.add_paint_view, name='add_paint'),
    path('delete-paint/<int:paint_id>/', views.delete_paint, name='delete_paint'),

]