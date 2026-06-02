# C:\Users\haris\OneDrive\Desktop\Birla\App\models.py
from django.db import models  # This ensures 'models' is defined!

class PaintProduct(models.Model):
    name = models.CharField(max_length=255)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    color_code = models.CharField(max_length=7, default="#02c39a")
    image = models.ImageField(upload_to='paints_catalog/')

    def __str__(self):
        return self.name

from django.db import models
from django.contrib.auth.models import User


from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, blank=True)
    profile_image = models.ImageField(upload_to='profile_pics/', default='default.jpg', blank=True)
    delivery_address = models.TextField(blank=True, help_text="Enter your full shipping address for orders.")
    
    # కేవలం 10 అంకెల కోసం వాలిడేటర్
    phone_validator = RegexValidator(
        regex=r'^\d{10}$', 
        message="Phone number must be exactly 10 digits."
    )
    
    phone = models.CharField(validators=[phone_validator], max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


from django.db import models
from django.contrib.auth.models import User

class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Dispatched', 'Dispatched'),
        ('Delivered', 'Delivered'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    delivery_address = models.TextField() # Profile address ikkada copy avthundi
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='COD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=255)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product_name} (Order #{self.order.id})"