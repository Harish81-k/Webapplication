import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Birla.settings')
django.setup()

from django.contrib.auth import get_user_model

def setup_permanent_admin():
    User = get_user_model()

    # ఇక్కడ Username, Email రెండూ ఒకటే ఇవ్వడం మంచిది (కన్ఫ్యూజన్ లేకుండా ఉంటుంది)
    USERNAME = 'admin@gmail.com'
    EMAIL = 'admin@gmail.com' 
    PASSWORD = 'Harish@12'

    print("--------------------------------------------------")
    if not User.objects.filter(username=USERNAME).exists():
        print(f"[INFO] Creating superuser account for: {USERNAME}...")
        User.objects.create_superuser(username=USERNAME, email=EMAIL, password=PASSWORD)
        print("[SUCCESS] Superuser created successfully!")
    else:
        print(f"[INFO] Superuser '{USERNAME}' already exists. Syncing password...")
        user = User.objects.get(username=USERNAME)
        user.set_password(PASSWORD)
        
        # ఇవి చాలా ముఖ్యం
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True  # ఒకవేళ అకౌంట్ ఇన్‌యాక్టివ్‌గా ఉంటే యాక్టివేట్ చేస్తుంది
        
        user.save()
        print("[SUCCESS] Password, permissions, and active status updated successfully!")
    print("--------------------------------------------------")

if __name__ == '__main__':
    setup_permanent_admin()