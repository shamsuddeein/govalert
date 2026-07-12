from django.db import migrations

def create_superuser(apps, schema_editor):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    email = 'talktoshamsuddeen@gmail.com'
    password = 'Allahu_akbar01'
    username = 'talktoshamsuddeen'
    
    if not User.objects.filter(email__iexact=email).exists():
        if User.objects.filter(username=username).exists():
            username = 'shamsuddeen_admin'
        User.objects.create_superuser(username=username, email=email, password=password)
    else:
        u = User.objects.get(email__iexact=email)
        u.set_password(password)
        u.is_superuser = True
        u.is_staff = True
        u.save()

def remove_superuser(apps, schema_editor):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    email = 'talktoshamsuddeen@gmail.com'
    User.objects.filter(email__iexact=email).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_superuser, remove_superuser),
    ]
