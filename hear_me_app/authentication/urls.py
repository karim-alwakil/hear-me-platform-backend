from django.urls import path
from .views import RegisterView, LoginView, ProfilePictureUploadView, InfluencerBankDetailsView, UploadBioVideosView


urlpatterns = [
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/influencer/upload/profile-picture/', ProfilePictureUploadView.as_view(), name='upload-profile-picture'),
    path('influencer/bank/', InfluencerBankDetailsView.as_view(), name='influencer-bank'), 
    path("api/influencer/upload/bio-videos/", UploadBioVideosView.as_view(), name="upload-bio-videos"),
]

