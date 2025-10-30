from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):

    USER_TYPES = [
        ('client', 'Client'),
        ('influencer', 'Influencer'),
    ]

    phone_number = models.CharField(max_length=15, unique=True)
    role = models.CharField(max_length=20, choices= USER_TYPES, default='client')
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    # Default username to phone_number if not provided
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.phone_number
        super().save(*args, **kwargs)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['username', 'email']

    def __str__(self):
        return f"{self.username} ({self.role}) - {self.phone_number}"

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')

    def __str__(self):
        return f"Client profile for {self.user.email}"

class Influencer(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    CATEGORY_CHOICES = [
        ('Tech', 'Tech'),
        ('Travel', 'Travel'),
        ('Comedy', 'Comedy'),
        ('Sports', 'Sports'),
        ('Entrepreneurship', 'Entrepreneurship'),
        ('Gaming', 'Gaming')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='influencer_profile')
    full_name = models.CharField(max_length=255, blank=True, null=True)
    biography = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='influencer_profiles/', blank=True, null=True)
    bio_videos = models.JSONField(default=list, blank=True)  # List of video URLs
    daily_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    weekly_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    instagram_acc_link = models.URLField(blank=True, null=True)
    tiktok_acc_link = models.URLField(blank=True, null=True)
    snapchat_acc_link = models.URLField(blank=True, null=True)
    youtube_acc_link = models.URLField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    iban = models.CharField(max_length=34, blank=True, null=True, help_text="IBAN no spaces, uppercase")
    

    def __str__(self):
        return f"Influencer profile for {self.user.email}"
    
    def save(self, *args, **kwargs):
        if len(self.bio_videos) > 5:
            raise ValueError("An influencer can have a maximum of 5 bio videos.")
        super().save(*args, **kwargs)



