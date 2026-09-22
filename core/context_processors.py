from django.conf import settings
from core.security import generate_human_token

def security_context(request):
    """
    Injects human verification token and Cloudflare Turnstile keys into template contexts.
    """
    return {
        'CLOUDFLARE_TURNSTILE_SITE_KEY': getattr(settings, 'CLOUDFLARE_TURNSTILE_SITE_KEY', ''),
        'human_token': generate_human_token(),
    }
