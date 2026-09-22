import os
import logging
from pathlib import Path
from django.core.management import call_command

logger = logging.getLogger(__name__)
_DB_INITIALIZED = False
_LAST_ADMIN_SYNC = 0

class AutoDatabaseInitMiddleware:
    """
    Middleware that automatically initializes migrations, ensures admin superuser,
    and syncs live records from MongoDB Atlas on Vercel serverless cold-start,
    and sets high-performance SEO and security headers.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        global _DB_INITIALIZED

        if not _DB_INITIALIZED:
            _DB_INITIALIZED = True
            try:
                from core.models import SafariPackage
                # Ultra-fast check (SELECT 1 LIMIT 1) instead of heavy full-table scanning
                needs_seed = False
                try:
                    if not SafariPackage.objects.exists():
                        needs_seed = True
                except Exception:
                    # Tables missing in /tmp/db.sqlite3, run migrations
                    try:
                        call_command('migrate', interactive=False)
                        if not SafariPackage.objects.exists():
                            needs_seed = True
                    except Exception:
                        needs_seed = False

                # Only if database is completely unseeded do we populate fixtures
                if needs_seed:
                    fixture = Path(__file__).resolve().parent.parent / 'initial_data.json'
                    if fixture.exists():
                        try:
                            call_command('loaddata', str(fixture), interactive=False)
                        except Exception as e:
                            logger.warning(f"Fixture load notice: {e}")

                    try:
                        from core.mongodb import sync_all_from_mongo_to_sqlite
                        sync_all_from_mongo_to_sqlite()
                    except Exception as e:
                        logger.warning(f"MongoDB hydration notice: {e}")

            except Exception as e:
                logger.error(f"AutoDatabaseInit error: {e}")

        # Ensure Admin Superuser Exists ONLY when an administrator navigates to the admin panel
        if request.path.startswith('/admin/'):
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                admin_user = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
                admin_pass = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123')
                admin_email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@discoveryala.com')

                user_obj = User.objects.filter(username=admin_user).first()
                if not user_obj:
                    User.objects.create_superuser(
                        username=admin_user,
                        email=admin_email,
                        password=admin_pass
                    )
                else:
                    if not user_obj.is_staff or not user_obj.is_superuser:
                        user_obj.is_staff = True
                        user_obj.is_superuser = True
                        user_obj.save()
            except Exception as e:
                logger.warning(f"Superuser auto-check notice: {e}")

        # In Admin panel, ensure SQLite periodically has fresh MongoDB records (at most once every 5 minutes)
        global _LAST_ADMIN_SYNC
        import time
        now = time.time()
        if request.path.startswith('/admin/') and getattr(request, 'user', None) and request.user.is_authenticated and request.user.is_staff:
            if 'blogpost' in request.path:
                try:
                    from core.mongodb import sync_blogs_from_mongo_to_sqlite
                    sync_blogs_from_mongo_to_sqlite()
                except Exception:
                    pass
            elif now - _LAST_ADMIN_SYNC > 300:
                _LAST_ADMIN_SYNC = now
                try:
                    from core.mongodb import sync_all_from_mongo_to_sqlite
                    sync_all_from_mongo_to_sqlite()
                except Exception:
                    pass

        response = self.get_response(request)

        # Performance & Security Headers
        if not response.has_header('X-Content-Type-Options'):
            response['X-Content-Type-Options'] = 'nosniff'
        if not response.has_header('Referrer-Policy'):
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Edge CDN Caching Optimization (Vercel & Global CDNs)
        # Prevents serverless function exhaustion while maximizing Core Web Vitals & TTFB
        is_safe_method = request.method in ('GET', 'HEAD')
        is_authed = getattr(request, 'user', None) and request.user.is_authenticated
        is_private_path = request.path.startswith('/admin') or request.path.startswith('/book')

        if not is_safe_method or is_authed or is_private_path:
            # Never cache private, authenticated, or transaction routes
            if not response.has_header('Cache-Control'):
                response['Cache-Control'] = 'private, no-cache, no-store, must-revalidate'
        elif response.status_code == 200:
            # Check for active flash messages
            has_messages = False
            try:
                from django.contrib.messages import get_messages
                has_messages = bool(len(get_messages(request)))
            except Exception:
                pass

            if not has_messages and not response.has_header('Cache-Control'):
                if request.path in ('/robots.txt', '/sitemap.xml', '/site.webmanifest', '/llms.txt', '/llms-full.txt'):
                    # 7-day Edge cache for sitemaps/robots/llms.txt
                    cache_rule = 'public, max-age=86400, s-maxage=604800, stale-while-revalidate=604800'
                    cdn_rule = 'public, s-maxage=604800, stale-while-revalidate=604800'
                else:
                    # 10-minute browser cache + 24-hour Edge CDN cache
                    # Eliminates repeat serverless invocations from visitors and web crawlers
                    cache_rule = 'public, max-age=600, s-maxage=86400, stale-while-revalidate=604800'
                    cdn_rule = 'public, s-maxage=86400, stale-while-revalidate=604800'

                response['Cache-Control'] = cache_rule
                response['CDN-Cache-Control'] = cdn_rule
                response['Vercel-CDN-Cache-Control'] = cdn_rule

        return response


