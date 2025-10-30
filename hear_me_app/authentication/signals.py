from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import logging

from .models import Influencer

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Influencer)
def influencer_pre_save(sender, instance, **kwargs):
    # stash old status so post_save can detect changes
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._old_status = getattr(old, 'status', None)
        except sender.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Influencer)
def influencer_post_save(sender, instance, created, **kwargs):
    # ignore creation; only notify on status transitions
    if created:
        return

    old_status = getattr(instance, '_old_status', None)
    new_status = getattr(instance, 'status', None)
    if old_status == new_status:
        return

    if new_status not in ('approved', 'rejected'):
        return

    user_email = getattr(instance.user, 'email', None)
    if not user_email:
        logger.warning("Influencer %s has no email; skipping notification", instance.pk)
        return

    subject = "حالة حساب المؤثر الخاص بك قد تم تحديثها"  # "Your Influencer Account Status Has Been Updated"
    if new_status == 'approved':
        message = (
            "تهانينا - تم الموافقة علي حسابك كمؤثر \n\n"
            "يمكنك الآن تسجيل الدخول وبدء استخدام ميزات المؤثرين لدينا. شكراً لانضمامك إلينا!"
        )
    else:  # rejected
        message = (
            "نأسف - تم رفض حسابك كمؤثر \n\n"
            "اذا كنت تعتقد ان هذا كان خطأ، يرجى التواصل مع دعم العملاء للمساعدة."
        )

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', None)

    try:
        send_mail(subject, message, from_email, [user_email], fail_silently=False)
        logger.info("Sent %s email to %s", new_status, user_email)
    except Exception:
        logger.exception("Failed to send influencer status email to %s", user_email)