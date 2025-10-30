from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .serializers import RegisterSerializer, LoginSerializer, BankDetailsSerializer
from .models import User
from .file_validators import validate_video_file
import os
import uuid
import logging

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info(f"RegisterView received data: {request.data}")
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            data: dict = serializer.save()
            user: User = data.get('user')
            return Response({
                "user": {
                    "id": user.pk,
                    "username": user.username,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "role": user.role
                },
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token")
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            data: dict = serializer.save()
            return Response({
                "message": "Login successful",
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"]
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ProfilePictureUploadView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get("profile_picture")

        if not file_obj:
            return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Save file manually to MEDIA_ROOT/influencer_profiles/
        file_path = default_storage.save(f"influencer_profiles/{file_obj.name}", ContentFile(file_obj.read()))
        file_url = request.build_absolute_uri(default_storage.url(file_path))

        return Response({"profile_picture_url": file_url}, status=status.HTTP_201_CREATED)


class InfluencerBankDetailsView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        user = request.user
        if not hasattr(user, 'influencer_profile'):
            return Response({"detail": "Only influencers can set bank details."}, status=403)

        serializer = BankDetailsSerializer(user.influencer_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Mask the IBAN in the response (only show last 4 chars)
            masked = serializer.validated_data['iban']
            masked_display = '****' + masked[-4:]
            return Response({
                "message": "Bank details updated.",
                "iban_masked": masked_display,
                "bank_name": serializer.validated_data['bank_name']
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UploadBioVideosView(APIView):
    permission_classes = [AllowAny]  # change to IsAuthenticated if only logged-in users can upload

    def post(self, request):
        # Expect files under "bio_videos" (multiple) or single "bio_videos"
        files = request.FILES.getlist("bio_videos")
        if not files:
            return Response({"detail": "No files provided."}, status=status.HTTP_400_BAD_REQUEST)

        if len(files) > 5:
            return Response({"detail": "Max 5 videos allowed."}, status=status.HTTP_400_BAD_REQUEST)

        saved = []
        for f in files:
            try:
                validate_video_file(f)
            except Exception as e:
                return Response({"detail": f"File validation failed for {f.name}: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

            # safe filename
            ext = os.path.splitext(f.name)[1]
            key = f"influencer_bio_videos/{uuid.uuid4().hex}{ext}"

            # save using default_storage (MEDIA_ROOT)
            path = default_storage.save(key, ContentFile(f.read()))
            file_url = request.build_absolute_uri(default_storage.url(path))

            saved.append({
                "filename": f.name,
                "path": path,
                "url": file_url,
                "size": f.size,
            })

        return Response({"uploaded": saved}, status=status.HTTP_201_CREATED)