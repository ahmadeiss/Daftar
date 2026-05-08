from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import MerchantProfile, SubscriptionPayment


User = get_user_model()


@receiver(post_save, sender=User)
def ensure_merchant_profile(sender, instance, created, **kwargs):
    if getattr(instance, "_skip_profile_signal", False):
        return
    if instance.is_superuser:
        return
    MerchantProfile.objects.get_or_create(
        user=instance,
        defaults={
            "store_name": instance.first_name or instance.email or instance.username,
            "owner_name": instance.first_name,
        },
    )


@receiver(post_save, sender=MerchantProfile)
def refresh_profile_status(sender, instance, **kwargs):
    if instance.subscription_status == MerchantProfile.SubscriptionStatus.SUSPENDED:
        return
    state = instance.billing_state
    if state == "overdue" and instance.subscription_status != MerchantProfile.SubscriptionStatus.PAST_DUE:
        MerchantProfile.objects.filter(pk=instance.pk).update(
            subscription_status=MerchantProfile.SubscriptionStatus.PAST_DUE
        )


@receiver(post_save, sender=SubscriptionPayment)
def apply_paid_subscription(sender, instance, created, **kwargs):
    if instance.status != instance.Status.PAID:
        return

    profile = instance.merchant
    profile.plan = instance.plan or profile.plan
    profile.subscription_status = MerchantProfile.SubscriptionStatus.ACTIVE
    profile.subscription_started_at = instance.period_start
    profile.subscription_expires_at = instance.period_end
    profile.user.is_active = True
    profile.user.save(update_fields=["is_active"])
    MerchantProfile.objects.filter(pk=profile.pk).update(
        plan_id=profile.plan_id,
        subscription_status=profile.subscription_status,
        subscription_started_at=profile.subscription_started_at,
        subscription_expires_at=profile.subscription_expires_at,
    )
