from djoser.signals import user_activated

from django.dispatch import receiver

@receiver(user_activated)

def activate_user(sender,user,request,**kwargs):
    if not user.is_verified:
        user.is_verified = True
        user.save(update_fields=['is_verified'])