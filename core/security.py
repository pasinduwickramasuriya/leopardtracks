import re
import time
import json
import urllib.request
import urllib.parse
import logging
from django.conf import settings
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired

logger = logging.getLogger(__name__)

# Signer for time-gated human verification tokens
_signer = TimestampSigner(salt='discoveryala-human-verification-salt')

# Regex to detect Cyrillic characters (typical in Russian payment/lottery/crypto spam)
CYRILLIC_REGEX = re.compile(r'[\u0400-\u04FF]')

# Known spam keywords (case-insensitive)
SPAM_KEYWORDS = [
    'руб', 'перевод', 'зачислен', 'выплата', 'казино', 'поступил перевод',
    'crypto', 'cryptocurrency', 'casino', 'viagra', 'cialis',
    'investment return', 'passive income', 'telegram @', 't.me/',
    'seo backlink', 'guest post service', 'rank your website'
]

def generate_human_token():
    """
    Generates a cryptographically signed timestamp token for forms.
    """
    payload = f"human_{int(time.time())}"
    return _signer.sign(payload)


def verify_human_token(token, min_seconds=2, max_seconds=86400):
    """
    Validates the human token generated during form render.
    Ensures the submission is not instant (< min_seconds, typical of bots)
    and not expired (> max_seconds).
    """
    if not token:
        return False, "Verification token missing."
    try:
        raw_val = _signer.unsign(token, max_age=max_seconds)
        parts = raw_val.split('_')
        if len(parts) >= 2 and parts[0] == 'human':
            issued_ts = int(parts[1])
            elapsed = time.time() - issued_ts
            if elapsed < min_seconds:
                return False, "Form submitted too quickly (bot detected)."
            return True, "Token valid."
        return False, "Invalid token structure."
    except SignatureExpired:
        return False, "Verification token expired. Please refresh and try again."
    except (BadSignature, Exception):
        return False, "Verification token signature invalid."


def verify_cloudflare_turnstile(token, remote_ip=None, expected_action=None):
    """
    Canonical Cloudflare Turnstile server-side siteverify verification.
    Follows developers.cloudflare.com/turnstile/spin spec:
    - Verifies token string length (0 < len <= 2048)
    - 10-second timeout
    - Validates success === true
    - Optionally validates expected action
    """
    secret_key = getattr(settings, 'CLOUDFLARE_TURNSTILE_SECRET_KEY', '').strip()
    if not secret_key:
        return False, "Turnstile secret not configured"

    if not isinstance(token, str) or len(token) == 0 or len(token) > 2048:
        return False, "Please complete the Cloudflare 'Verify you are human' check."

    try:
        verify_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
        payload = {
            'secret': secret_key,
            'response': token,
        }
        if remote_ip:
            payload['remoteip'] = remote_ip

        data = urllib.parse.urlencode(payload).encode('utf-8')
        req = urllib.request.Request(
            verify_url,
            data=data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Discoveryala-Turnstile-Verification/1.0'
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('success') is True:
                # If action verification is requested, verify match
                if expected_action and result.get('action') and result.get('action') != expected_action:
                    logger.warning(f"Turnstile action mismatch: expected {expected_action}, got {result.get('action')}")
                    return False, "Security verification action mismatch."
                return True, "Verified by Cloudflare Turnstile."
            else:
                error_codes = result.get('error-codes', [])
                logger.warning(f"Turnstile verification failed: {error_codes}")
                return False, "Human verification failed. Please try again."
    except Exception as e:
        logger.error(f"Turnstile API connection error: {e}")
        # In case Cloudflare API network times out, log error and allow graceful handling
        return False, "Security verification service temporarily unreachable. Please retry in a moment."


def is_spam_or_bot(request, extra_fields=None):
    """
    Comprehensive multi-vector check:
    1. Invisible honeypot traps (website_hp, phone_fax_hp).
    2. Cyrillic characters in names/messages.
    3. Common spam phrases and money scam patterns.
    4. Time gate (form submitted in under 2 seconds).
    
    Returns (is_spam, reason).
    """
    if request.method != 'POST':
        return False, "Not a POST request"

    post = request.POST

    # 1. Honeypot check - bots auto-fill hidden fields
    honeypots = ['website_hp', 'address_line_2_hp', 'company_hp']
    for hp in honeypots:
        if post.get(hp, '').strip():
            logger.warning(f"Spam caught: Honeypot '{hp}' filled with '{post.get(hp)}'")
            return True, f"Honeypot trap triggered ({hp})"

    # 2. Text fields to scan for Cyrillic and spam patterns
    text_to_scan = []
    for key in ['full_name', 'name', 'message', 'email', 'email_address', 'subject', 'country']:
        val = post.get(key, '')
        if val:
            text_to_scan.append(val)

    if extra_fields:
        for val in extra_fields:
            if val:
                text_to_scan.append(str(val))

    combined_text = " ".join(text_to_scan)

    # Cyrillic character check (Russian payment scam attack)
    if CYRILLIC_REGEX.search(combined_text):
        logger.warning(f"Spam caught: Cyrillic characters detected in form submission: {combined_text[:120]}")
        return True, "Cyrillic spam detected"

    # Spam keyword check
    combined_lower = combined_text.lower()
    for kw in SPAM_KEYWORDS:
        if kw in combined_lower:
            logger.warning(f"Spam caught: Spam keyword '{kw}' detected")
            return True, f"Spam keyword detected: {kw}"

    # Multiple URLs in message
    url_count = len(re.findall(r'https?://', combined_text, re.IGNORECASE))
    if url_count > 2:
        logger.warning("Spam caught: Excessive links in message")
        return True, "Too many URLs in submission"

    return False, "Clean"


def verify_human_submission(request):
    """
    Verifies human status using Cloudflare Turnstile.
    """
    turnstile_response = request.POST.get('cf-turnstile-response', '').strip()
    if not turnstile_response:
        return False, "Please complete the Cloudflare 'Verify you are human' check before submitting."

    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR')
    is_valid, msg = verify_cloudflare_turnstile(turnstile_response, client_ip)
    if is_valid is False:
        return False, msg

    return True, "Verified human by Cloudflare Turnstile"

