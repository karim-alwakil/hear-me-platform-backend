from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import re
from .models import Client, Influencer
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
User = get_user_model()



def normalize_iban(value: str) -> str:
    return re.sub(r'\s+', '', value).upper()

# IBAN checksum validation (basic, reliable)
def is_valid_iban(iban: str) -> bool:
    iban = normalize_iban(iban)
    # Basic pattern: 2 letters country + 2 digits + up to 30 alnum
    if not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}$', iban):
        return False

    # Move first 4 chars to the end and replace letters with numbers (A=10 ... Z=35)
    rearranged = iban[4:] + iban[:4]
    converted = ''
    for ch in rearranged:
        if ch.isdigit():
            converted += ch
        else:
            converted += str(ord(ch) - 55)  # A->10 ... Z->35

    # Perform mod-97
    # To avoid huge ints, iteratively compute remainder
    remainder = 0
    for i in range(0, len(converted), 9):  # process in chunks
        part = str(remainder) + converted[i:i+9]
        remainder = int(part) % 97
    return remainder == 1



# Utility function for token generation
def generate_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh)
    }

class RegisterSerializer(serializers.Serializer):

    def to_internal_value(self, data):
        """
        Bypass field-level parsing so validate() receives the full incoming dict.
        Keep a shallow copy to avoid mutating the original request data.
        """
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise serializers.ValidationError("Invalid data format; expected an object.")
        return data.copy()
    
    def validate(self, data):
        # Conditional validation based on role
        logger.info(f"Validating data: {data}")
        role = data.get('role')
        if not role:
            raise serializers.ValidationError("Role is required.")
        
#data filtering for validation
        data_copy = data.copy()
        user_data = {}
        for field in User._meta.get_fields():
            field_name = field.name
            if field_name in data_copy:
                user_data[field_name] = data_copy.pop(field_name)

# Validate the user data
        user_instance = User(**user_data)
        try:
            user_instance.full_clean()
        except serializers.ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        
        if role == 'client':
            # data_copy.pop('bio_videos')
            client_instance = Client(**data_copy)
            try:
                client_instance.full_clean(exclude=['user'])
            except serializers.ValidationError as e:
                raise serializers.ValidationError(e.message_dict)

        elif role == 'influencer':
            # IBAN validation if present and role is influencer
            iban_val = data.get('iban')
            if iban_val:
                from .serializers import is_valid_iban, normalize_iban
                if not is_valid_iban(iban_val):
                    raise serializers.ValidationError({'iban': 'Invalid IBAN.'})
                # normalize before saving
                data['iban'] = normalize_iban(iban_val)

            bank_name_val = data.get('bank_name')
            # validate bank_name length/characters
            if bank_name_val and len(bank_name_val) > 150:
                raise serializers.ValidationError({'bank_name': 'Bank name too long.'})

            Influencer_instance = Influencer(**data_copy) 
            try:
                Influencer_instance.full_clean(exclude=['user'])
            except serializers.ValidationError as e:
                raise serializers.ValidationError(e.message_dict)

        return data
    
    def create(self, validated_data):
        # Extract role-specific data
        role = validated_data.pop('role')

        # Create the user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            password=validated_data['password'],
            role=role
        )

        # Handle role-specific models
        if role == 'client':
            Client.objects.create(user=user)
        elif role == 'influencer':
            Influencer.objects.create(
                user=user,
                full_name=validated_data.get('full_name', ''),
                biography=validated_data.get('biography', ''),
                category=validated_data.get('category', ''),
                profile_picture=validated_data.get('profile_picture'),
                bio_videos=validated_data.get('bio_videos', []),
                daily_price=validated_data.get('daily_price'),
                weekly_price=validated_data.get('weekly_price'),
                instagram_acc_link=validated_data.get('instagram_acc_link'),
                tiktok_acc_link=validated_data.get('tiktok_acc_link'),
                snapchat_acc_link=validated_data.get('snapchat_acc_link'),
                youtube_acc_link=validated_data.get('youtube_acc_link'),
                bank_name=validated_data.get('bank_name'),
                iban=validated_data.get('iban'),
            )

        # Generate tokens
        tokens = generate_tokens(user)
        validated_data.update(tokens)
        validated_data['user'] = user

        return validated_data

class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=[('client', 'Client'), ('influencer', 'Influencer')])

    def validate(self, data):
        user = authenticate(phone_number=data['phone_number'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if user.role != data['role']:
            raise serializers.ValidationError("Role mismatch.")
        if user.role == 'influencer' and user.influencer_profile.status != 'approved':
            raise serializers.ValidationError("Influencer account not approved.")
        data['user'] = user
        return data

    def create(self, validated_data):
        user = validated_data['user']
        tokens = generate_tokens(user)
        validated_data.update(tokens)
        return validated_data
    
class ProfilePictureUploadSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=True)

    class Meta:
        model = Influencer
        fields = ['profile_picture']

    def validate_profile_picture(self, value):

        # Validate file size (e.g., max 5MB)
        max_size = 5 * 1024 * 1024 
        if value.size > max_size: 
            raise serializers.ValidationError("Profile picture size should not exceed 5MB.")


        # Valisate file type
        validated_extensions = ['.jpg', '.jpeg', '.png', '.webp'] 
        if not any(str(value.name).lower().endswith(ext) for ext in validated_extensions):
            raise serializers.ValidationError("Unsupported file type. Allowed types: JPG, JPEG, PNG, WEBP.")
        
        return value
    
    def save(self, user):
        influencer = user.influencer_profile
        influencer.profile_picture = self.validated_data['profile_picture']
        influencer.save()
        return influencer

class BankDetailsSerializer(serializers.ModelSerializer):
    iban = serializers.CharField(required=True)
    bank_name = serializers.CharField(required=True, max_length=150)

    class Meta:
        model = Influencer
        fields = ['bank_name', 'iban']

    def validate_iban(self, value):
        value = normalize_iban(value)
        if not is_valid_iban(value):
            raise serializers.ValidationError("Invalid IBAN.")
        return value
