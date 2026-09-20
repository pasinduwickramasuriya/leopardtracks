import os
import json
import logging
import threading
from contextlib import contextmanager
from django.conf import settings

logger = logging.getLogger(__name__)
_mongo_client = None

DEFAULT_MONGODB_NAME = 'leopardtracks_db'

_MONGO_SYNC_STATE = threading.local()

def is_mongo_sync_paused():
    """Check if MongoDB post_save / post_delete signals are currently suppressed."""
    return getattr(_MONGO_SYNC_STATE, 'paused', False)

@contextmanager
def disable_mongo_sync():
    """
    Context manager to pause Django signals from pushing models back to MongoDB Atlas
    while hydrating SQLite from MongoDB Atlas.
    """
    _MONGO_SYNC_STATE.paused = True
    try:
        yield
    finally:
        _MONGO_SYNC_STATE.paused = False


class MongoPackageModel:
    def __init__(self, doc):
        self._doc = doc
        self.id = doc.get('id', 1)
        self.pk = self.id
        self.title = doc.get('title', '')
        self.subtitle = doc.get('subtitle', '')
        self.slug = doc.get('slug', '')
        self.imageUrl = doc.get('imageUrl', '') or '/static/images/yala-tent.jpg'
        self.image_file = None
        self.image_urls = doc.get('image_urls', '')
        self.description = doc.get('description', '')
        self.category = doc.get('category', 'half-day')
        self.category_label = doc.get('category_label', 'HALF-DAY GAME DRIVE')
        self.tag_class = doc.get('tag_class', 'tag-sage')
        self.price_type = doc.get('price_type', 'jeep_only')
        self.price = str(doc.get('price', '$55.00'))
        self.price_unit = doc.get('price_unit', 'per 4x4 jeep (up to 7 guests)')
        self.mealPrice = str(doc.get('mealPrice', '0'))
        self.ticketPrice = str(doc.get('ticketPrice', '46'))
        self.childTicketPrice = str(doc.get('childTicketPrice', '20'))
        self.includes_tickets = doc.get('includes_tickets', False)
        self.ticket_addon_price = doc.get('ticket_addon_price', '')
        self.includes_breakfast = doc.get('includes_breakfast', False)
        self.breakfast_addon_price = doc.get('breakfast_addon_price', '')
        self.duration = doc.get('duration', '4 Hours')
        self.vehicle = doc.get('vehicle', 'Private 4x4 Safari Jeep')
        self.inclusions = doc.get('inclusions', '')
        self.exclusions = doc.get('exclusions', '')
        self.highlights = doc.get('highlights', '')
        self.featured = doc.get('featured', False)

    def get_clean_price(self):
        return str(self.price).replace('$', '').strip()

    def get_inclusions_list(self):
        if not self.inclusions:
            return []
        return [inc.strip() for inc in str(self.inclusions).split('\n') if inc.strip()]

    def get_exclusions_list(self):
        if not self.exclusions:
            return []
        return [exc.strip() for exc in str(self.exclusions).split('\n') if exc.strip()]

    def get_highlights_list(self):
        if not self.highlights:
            return []
        return [hl.strip() for hl in str(self.highlights).split('\n') if hl.strip()]

    def get_image_urls_list(self):
        urls = [self.imageUrl] if self.imageUrl else []
        if self.image_urls:
            extra = [u.strip() for u in str(self.image_urls).split('\n') if u.strip()]
            urls.extend(extra)
        return urls


class MongoTourModel:
    def __init__(self, doc):
        self._doc = doc
        self.id = doc.get('id', 1)
        self.pk = self.id
        self.title = doc.get('title', '')
        self.slug = doc.get('slug', '')
        self.route = doc.get('route', '')
        self.price = str(doc.get('price', '280'))
        self.duration = doc.get('duration', '')
        self.imageUrl = doc.get('imageUrl', '') or '/static/images/yala-wildlife-hero.jpg'
        self.description = doc.get('description', '')
        self.longDescription = doc.get('longDescription', '') or self.description
        self.highlights = doc.get('highlights', '')
        self.inclusions = doc.get('inclusions', '')
        self.exclusions = doc.get('exclusions', '')
        self.itinerary_json = doc.get('itinerary_json', '')
        self.isFeatured = doc.get('isFeatured', True)

    def get_clean_price(self):
        return str(self.price).replace('$', '').strip()

    def get_tour_image_url(self):
        return self.imageUrl

    def get_highlights_list(self):
        if not self.highlights:
            return []
        return [h.strip() for h in str(self.highlights).split('\n') if h.strip()]

    def get_inclusions_list(self):
        if not self.inclusions:
            return []
        return [i.strip() for i in str(self.inclusions).split('\n') if i.strip()]

    def get_exclusions_list(self):
        if not self.exclusions:
            return []
        return [e.strip() for e in str(self.exclusions).split('\n') if e.strip()]

    def get_itinerary_list(self):
        if not self.itinerary_json:
            return []
        try:
            return json.loads(self.itinerary_json)
        except Exception:
            return []


class MongoBlogModel:
    def __init__(self, doc):
        self._doc = doc
        self.id = doc.get('id', 1)
        self.pk = self.id
        self.title = doc.get('title', '')
        self.slug = doc.get('slug', '')
        self.category = doc.get('category', 'WILDLIFE')
        self.author = doc.get('author', 'Senior Naturalist Desk')
        self.imageUrl = doc.get('imageUrl', '') or '/static/images/yala-wildlife-hero.jpg'
        self.content = doc.get('content', '')
        self.featured = doc.get('featured', False)
        self.created_at = doc.get('created_at', 'August 2026')

    def get_paragraphs(self):
        if not self.content:
            return []
        return [p.strip() for p in str(self.content).split('\n\n') if p.strip()]


class MongoHeroModel:
    def __init__(self, doc):
        self._doc = doc
        self.id = doc.get('id', 1)
        self.pk = self.id
        self.title = doc.get('title', 'WILD YALA SAFARIS')
        self.subtitle = doc.get('subtitle', "Ceylon's premier 4x4 game drives & luxury glamping.")
        self.description = doc.get('description', '')
        self.badge_text = doc.get('badge_text', 'YALA LEOPARD TRACKS')
        self.imageUrl = doc.get('imageUrl', '') or doc.get('bg_image_url', '') or '/static/images/yala-wildlife-hero.jpg'
        self.bg_image_url = self.imageUrl
        btn_p = doc.get('button_primary_text', 'PACKAGES')
        if btn_p == 'EXPLORE PACKAGES':
            btn_p = 'PACKAGES'
        self.button_primary_text = btn_p
        self.button_primary_url = doc.get('button_primary_url', '/packages/')

        btn_s = doc.get('button_secondary_text', 'BOOK SAFARI')
        if btn_s == 'RESERVE YALA SAFARI JEEP':
            btn_s = 'BOOK SAFARI'
        self.button_secondary_text = btn_s
        self.button_secondary_url = doc.get('button_secondary_url', '/contact/')

        self.cta_text = doc.get('cta_text', 'Book Now')
        self.cta_link = doc.get('cta_link', '#plan-your-stay')
        self.is_active = doc.get('is_active', True)

    def get_hero_image_url(self):
        if self.imageUrl and str(self.imageUrl).strip():
            from .models import optimize_cloudinary_url
            return optimize_cloudinary_url(str(self.imageUrl).strip(), 1200)
        return '/static/images/yala-wildlife-hero.jpg'

    def get_hero_image_mobile_url(self):
        if self.imageUrl and str(self.imageUrl).strip():
            from .models import optimize_cloudinary_url
            return optimize_cloudinary_url(str(self.imageUrl).strip(), 640)
        return '/static/images/yala-wildlife-hero.jpg'


def get_mongo_uri():
    uri = os.getenv('MONGODB_URI', '').strip()
    if not uri:
        try:
            from django.conf import settings
            if getattr(settings, 'configured', False):
                uri = getattr(settings, 'MONGODB_URI', '').strip()
        except Exception:
            pass
    return uri

def get_mongo_dbname():
    name = os.getenv('MONGODB_NAME', '').strip()
    if not name:
        try:
            from django.conf import settings
            if getattr(settings, 'configured', False):
                name = getattr(settings, 'MONGODB_NAME', '').strip()
        except Exception:
            pass
    return name if name else DEFAULT_MONGODB_NAME

def is_mongodb_active():
    val = os.getenv('USE_MONGODB', '').strip()
    if val:
        return val.lower() in ('true', '1', 'yes')
    try:
        from django.conf import settings
        if getattr(settings, 'configured', False):
            return getattr(settings, 'USE_MONGODB', False)
    except Exception:
        pass
    return True

def get_mongo_db():
    global _mongo_client
    try:
        import pymongo
        uri = get_mongo_uri()
        if not uri:
            return None

        db_name = get_mongo_dbname()

        if _mongo_client is None:
            _mongo_client = pymongo.MongoClient(
                uri,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                socketTimeoutMS=15000,
                maxPoolSize=10,
                retryWrites=True,
            )
        
        # Test connection ping if needed
        return _mongo_client[db_name]
    except Exception as e:
        logger.error(f"MongoDB connection error: {e}")
        _mongo_client = None
        return None

# ==============================================================================
# Model Serialization for MongoDB
# ==============================================================================

def package_to_dict(pkg):
    return {
        'id': pkg.id,
        'title': pkg.title or '',
        'subtitle': pkg.subtitle or '',
        'slug': pkg.slug or '',
        'imageUrl': pkg.imageUrl or '',
        'image_urls': pkg.image_urls or '',
        'description': pkg.description or '',
        'category': pkg.category or 'half-day',
        'category_label': pkg.category_label or 'HALF-DAY GAME DRIVE',
        'tag_class': pkg.tag_class or 'tag-sage',
        'price_type': pkg.price_type or 'jeep_only',
        'price': str(pkg.price or '$120'),
        'price_unit': pkg.price_unit or 'per 4x4 jeep (up to 6 guests)',
        'mealPrice': str(pkg.mealPrice or '0'),
        'ticketPrice': str(pkg.ticketPrice or '0'),
        'childTicketPrice': str(pkg.childTicketPrice or '20'),
        'includes_tickets': bool(pkg.includes_tickets),
        'ticket_addon_price': pkg.ticket_addon_price or '',
        'includes_breakfast': bool(pkg.includes_breakfast),
        'breakfast_addon_price': pkg.breakfast_addon_price or '',
        'duration': pkg.duration or '5 Hours (05:30 AM – 10:30 AM)',
        'vehicle': pkg.vehicle or 'Private 4x4 Safari Jeep',
        'inclusions': pkg.inclusions or '',
        'exclusions': pkg.exclusions or '',
        'highlights': pkg.highlights or '',
        'featured': bool(pkg.featured),
        'updated_at': pkg.updated_at.isoformat() if getattr(pkg, 'updated_at', None) else '',
    }

def tour_to_dict(tour):
    return {
        'id': tour.id,
        'title': tour.title or '',
        'slug': tour.slug or '',
        'route': tour.route or '',
        'price': str(tour.price or '280'),
        'duration': tour.duration or '5 Days / 4 Nights',
        'imageUrl': tour.imageUrl or '',
        'isFeatured': bool(tour.isFeatured),
        'description': tour.description or '',
        'longDescription': tour.longDescription or '',
        'highlights': tour.highlights or '',
        'inclusions': tour.inclusions or '',
        'exclusions': tour.exclusions or '',
        'seoKeywords': tour.seoKeywords or '',
        'itinerary_json': tour.itinerary_json or '',
        'updated_at': tour.updated_at.isoformat() if getattr(tour, 'updated_at', None) else '',
    }

def blog_to_dict(blog):
    return {
        'id': blog.id,
        'title': blog.title or '',
        'slug': blog.slug or '',
        'category': blog.category or 'WILDLIFE LOG',
        'author': blog.author or 'Discoveryala Naturalist',
        'imageUrl': blog.imageUrl or '',
        'content': blog.content or '',
        'featured': bool(blog.featured),
        'updated_at': blog.updated_at.isoformat() if getattr(blog, 'updated_at', None) else '',
    }

def hero_to_dict(hero):
    return {
        'id': hero.id,
        'title': hero.title or 'WILD YALA SAFARIS',
        'subtitle': hero.subtitle or "Ceylon's premier 4x4 game drives & luxury glamping.",
        'badge_text': hero.badge_text or '🌿 YALA LEOPARD TRACKS',
        'imageUrl': hero.imageUrl or '',
        'button_primary_text': hero.button_primary_text or 'EXPLORE PACKAGES',
        'button_primary_url': hero.button_primary_url or '/packages/',
        'button_secondary_text': hero.button_secondary_text or 'BOOK SAFARI',
        'button_secondary_url': hero.button_secondary_url or '/contact/',
        'is_active': bool(hero.is_active),
        'updated_at': hero.updated_at.isoformat() if getattr(hero, 'updated_at', None) else '',
    }

def review_to_dict(rev):
    return {
        'id': rev.id,
        'category': rev.category or 'leopard',
        'name': rev.name or '',
        'origin': rev.origin or 'London, UK',
        'date': rev.date or 'August 2026',
        'package': rev.package or 'Yala Block 1 Morning Leopard Game Drive',
        'rating': int(rev.rating or 5),
        'comment': rev.comment or '',
        'verified': bool(rev.verified),
        'avatar_url': rev.avatar_url or '',
        'photo_url': rev.photo_url or '',
        'source': rev.source or 'Google Maps',
    }

def booking_to_dict(b):
    return {
        'id': b.id,
        'package_title': b.package_title or '',
        'full_name': b.full_name or '',
        'country': b.country or '',
        'email': b.email or '',
        'phone_code': b.phone_code or '+94',
        'phone_number': b.phone_number or '',
        'safari_date': str(b.safari_date) if b.safari_date else '',
        'guests': int(b.guests or 2),
        'adult_guests': int(b.adult_guests or 2),
        'child_guests': int(b.child_guests or 0),
        'under6_guests': int(b.under6_guests or 0),
        'include_meals': bool(b.include_meals),
        'meal_count': int(b.meal_count or 0),
        'meals_price_total': str(b.meals_price_total or '0'),
        'include_tickets': bool(b.include_tickets),
        'tickets_price_total': str(b.tickets_price_total or '0'),
        'base_price': str(b.base_price or '0'),
        'total_price': str(b.total_price or '0'),
        'message': b.message or '',
        'status': b.status or 'Pending',
    }

# ==============================================================================
# Real-Time MongoDB CRUD Operations (Triggered on Django Admin actions)
# ==============================================================================

def sync_model_to_mongo(instance):
    """
    Called whenever an instance is created or updated in Django Admin.
    Upserts the corresponding document in MongoDB Atlas by primary key (id).
    Ensures zero duplicate records and immediate persistence.
    """
    global _mongo_client
    import time
    for attempt in range(2):
        try:
            db = get_mongo_db()
            if db is None:
                time.sleep(0.5)
                continue
            model_name = instance.__class__.__name__
            doc_id = instance.id
            if model_name == 'SafariPackage':
                doc = package_to_dict(instance)
                db.core_safaripackage.replace_one({'id': doc_id}, doc, upsert=True)
                db.packages.replace_one({'id': doc_id}, doc, upsert=True)
            elif model_name == 'Tour':
                doc = tour_to_dict(instance)
                db.core_tour.replace_one({'id': doc_id}, doc, upsert=True)
            elif model_name == 'BlogPost':
                doc = blog_to_dict(instance)
                db.core_blogpost.replace_one({'id': doc_id}, doc, upsert=True)
            elif model_name == 'HeroSection':
                doc = hero_to_dict(instance)
                db.core_herosection.replace_one({'id': doc_id}, doc, upsert=True)
            elif model_name == 'GuestReview':
                doc = review_to_dict(instance)
                db.core_guestreview.replace_one({'id': doc_id}, doc, upsert=True)
            elif model_name == 'SafariBooking':
                doc = booking_to_dict(instance)
                db.core_safaribooking.replace_one({'id': doc_id}, doc, upsert=True)
            return True
        except Exception as e:
            logger.error(f"Error syncing {instance.__class__.__name__} to MongoDB Atlas (attempt {attempt+1}): {e}")
            _mongo_client = None
            time.sleep(0.5)
    return False

def delete_model_from_mongo(instance):
    """
    Called whenever an instance is deleted in Django Admin.
    Deletes the corresponding document from MongoDB Atlas in real time.
    """
    try:
        db = get_mongo_db()
        if db is None:
            return False
        model_name = instance.__class__.__name__
        doc_id = instance.id
        doc_slug = getattr(instance, 'slug', None)

        # Match by ID or slug (if slug exists) to eliminate any duplicate or orphaned docs
        if doc_slug:
            filter_query = {'$or': [{'id': doc_id}, {'slug': str(doc_slug).strip()}]}
        else:
            filter_query = {'id': doc_id}

        if model_name == 'SafariPackage':
            db.core_safaripackage.delete_many(filter_query)
            db.packages.delete_many(filter_query)
        elif model_name == 'Tour':
            db.core_tour.delete_many(filter_query)
        elif model_name == 'BlogPost':
            db.core_blogpost.delete_many(filter_query)
        elif model_name == 'HeroSection':
            db.core_herosection.delete_many({'id': doc_id})
        elif model_name == 'GuestReview':
            db.core_guestreview.delete_many({'id': doc_id})
        elif model_name == 'SafariBooking':
            db.core_safaribooking.delete_many({'id': doc_id})

        logger.info(f"Successfully deleted {model_name} (id={doc_id}) from MongoDB Atlas")
        return True
    except Exception as e:
        logger.error(f"Error deleting {instance.__class__.__name__} from MongoDB Atlas: {e}")
        return False

# ==============================================================================
# Bi-Directional Database Hydration (Cold-Start & Seeding)
# ==============================================================================

def _parse_timestamp(val):
    if not val:
        return 0.0
    from datetime import datetime, date
    if isinstance(val, (datetime, date)):
        if isinstance(val, datetime):
            return val.timestamp()
        return datetime.combine(val, datetime.min.time()).timestamp()
    if isinstance(val, str):
        try:
            clean_val = val.replace('Z', '+00:00')
            return datetime.fromisoformat(clean_val).timestamp()
        except Exception:
            return 0.0
    return 0.0

_LAST_BLOG_SYNC = 0

def sync_blogs_from_mongo_to_sqlite(force=False):
    """
    Ultra-fast (<2s) dedicated sync for BlogPost models between MongoDB Atlas and SQLite.
    Fetches blog metadata without heavy text content, identifies missing or deleted blogs,
    and bulk-inserts or deletes them in SQLite.
    Throttled to run at most once every 30 seconds unless force=True.
    """
    global _LAST_BLOG_SYNC
    import time
    now = time.time()
    if not force and (now - _LAST_BLOG_SYNC < 30):
        return True

    try:
        db = get_mongo_db()
        if db is None:
            return False

        from .models import BlogPost
        from django.db import transaction

        raw_blogs = list(db.core_blogpost.find({}, {'id': 1, 'slug': 1, 'updated_at': 1, 'title': 1, 'imageUrl': 1, 'category': 1, 'author': 1, 'featured': 1}))
        if not raw_blogs:
            return False

        mongo_ids = {b['id'] for b in raw_blogs if 'id' in b and b['id'] is not None}
        if not mongo_ids:
            return False

        with disable_mongo_sync():
            with transaction.atomic():
                # Prune SQLite blog posts that no longer exist in MongoDB Atlas
                deleted_count, _ = BlogPost.objects.exclude(id__in=mongo_ids).delete()
                if deleted_count > 0:
                    logger.info(f"Pruned {deleted_count} deleted blog post(s) from SQLite that no longer exist in MongoDB Atlas")

                existing_map = {bg.id: bg for bg in BlogPost.objects.all()}
                missing_ids = [b_id for b_id in mongo_ids if b_id not in existing_map]

                # Fetch full documents only for missing blogs (e.g. newly created ones)
                if missing_ids:
                    full_docs = list(db.core_blogpost.find({'id': {'$in': missing_ids}}))
                    new_items = []
                    for doc in full_docs:
                        new_items.append(BlogPost(
                            id=doc.get('id'),
                            title=str(doc.get('title') or ''),
                            slug=str(doc.get('slug') or '').strip(),
                            category=str(doc.get('category') or 'WILDLIFE LOG'),
                            author=str(doc.get('author') or 'Discoveryala Naturalist'),
                            imageUrl=str(doc.get('imageUrl') or ''),
                            content=str(doc.get('content') or ''),
                            featured=bool(doc.get('featured')),
                        ))
                    if new_items:
                        BlogPost.objects.bulk_create(new_items, ignore_conflicts=True)
                        logger.info(f"Imported {len(new_items)} new blog post(s) into SQLite: {missing_ids}")

                # Update modified metadata on existing blogs
                for b in raw_blogs:
                    b_id = b.get('id')
                    if b_id in existing_map:
                        bg_obj = existing_map[b_id]
                        m_img = str(b.get('imageUrl') or '')
                        m_title = str(b.get('title') or '')
                        m_slug = str(b.get('slug') or '').strip()
                        m_featured = bool(b.get('featured'))
                        if (bg_obj.imageUrl != m_img or 
                            bg_obj.title != m_title or 
                            bg_obj.slug != m_slug or 
                            bg_obj.featured != m_featured):
                            bg_obj.imageUrl = m_img
                            bg_obj.title = m_title
                            bg_obj.slug = m_slug
                            bg_obj.featured = m_featured
                            bg_obj.save()

        _LAST_BLOG_SYNC = now
        return True
    except Exception as e:
        logger.error(f"Error in sync_blogs_from_mongo_to_sqlite: {e}")
        return False

def sync_all_from_mongo_to_sqlite():
    """
    Loads latest documents from MongoDB Atlas into SQLite so Django Admin
    always displays the true live database content upon cold start.
    MongoDB Atlas is treated as the authoritative master cloud store.
    Optimized for fast execution (<1s) without blocking requests or timing out.
    """
    try:
        db = get_mongo_db()
        if db is None:
            return False

        from django.db import transaction
        from .models import SafariPackage, Tour, BlogPost, HeroSection, GuestReview, SafariBooking
        from datetime import datetime, date

        with disable_mongo_sync():
            with transaction.atomic():
                # 1. Sync Safari Packages (Deduplicate by ID)
                raw_pkgs = list(db.core_safaripackage.find()) or list(db.packages.find())
                if raw_pkgs:
                    # Deduplicate in memory keeping latest
                    pkgs_map = {}
                    for d in raw_pkgs:
                        pkg_id = d.get('id')
                        if pkg_id is not None:
                            pkgs_map[pkg_id] = d

                    # Prune SQLite packages that no longer exist in MongoDB Atlas
                    if pkgs_map:
                        SafariPackage.objects.exclude(id__in=pkgs_map.keys()).delete()

                    for pkg_id, d in pkgs_map.items():
                        slug_val = str(d.get('slug') or '').strip()
                        defaults = {
                            'title': str(d.get('title') or ''),
                            'subtitle': str(d.get('subtitle') or ''),
                            'slug': slug_val,
                            'imageUrl': str(d.get('imageUrl') or ''),
                            'image_urls': str(d.get('image_urls') or ''),
                            'description': str(d.get('description') or ''),
                            'category': str(d.get('category') or 'half-day'),
                            'category_label': str(d.get('category_label') or 'HALF-DAY GAME DRIVE'),
                            'tag_class': str(d.get('tag_class') or 'tag-sage'),
                            'price_type': str(d.get('price_type') or 'jeep_only'),
                            'price': str(d.get('price') or '$120'),
                            'price_unit': str(d.get('price_unit') or 'per 4x4 jeep (up to 6 guests)'),
                            'mealPrice': str(d.get('mealPrice') or '0'),
                            'ticketPrice': str(d.get('ticketPrice') or '0'),
                            'childTicketPrice': str(d.get('childTicketPrice') or '20'),
                            'includes_tickets': bool(d.get('includes_tickets')),
                            'ticket_addon_price': str(d.get('ticket_addon_price') or ''),
                            'includes_breakfast': bool(d.get('includes_breakfast')),
                            'breakfast_addon_price': str(d.get('breakfast_addon_price') or ''),
                            'duration': str(d.get('duration') or '5 Hours'),
                            'vehicle': str(d.get('vehicle') or 'Private 4x4 Jeep'),
                            'inclusions': str(d.get('inclusions') or ''),
                            'exclusions': str(d.get('exclusions') or ''),
                            'highlights': str(d.get('highlights') or ''),
                            'featured': bool(d.get('featured')),
                        }
                        pkg_obj = SafariPackage.objects.filter(id=pkg_id).first()
                        if not pkg_obj and slug_val:
                            pkg_obj = SafariPackage.objects.filter(slug=slug_val).first()

                        if pkg_obj:
                            changed = False
                            for k, v in defaults.items():
                                if getattr(pkg_obj, k) != v:
                                    setattr(pkg_obj, k, v)
                                    changed = True
                            if changed:
                                pkg_obj.save()
                        else:
                            defaults['id'] = pkg_id
                            SafariPackage.objects.create(**defaults)

                # 2. Sync Tours (Deduplicate by ID)
                raw_tours = list(db.core_tour.find())
                if raw_tours:
                    tours_map = {}
                    for t in raw_tours:
                        t_id = t.get('id')
                        if t_id is not None:
                            # If duplicate, choose the one with newer updated_at
                            if t_id in tours_map:
                                old_ts = _parse_timestamp(tours_map[t_id].get('updated_at'))
                                new_ts = _parse_timestamp(t.get('updated_at'))
                                if new_ts >= old_ts:
                                    tours_map[t_id] = t
                            else:
                                tours_map[t_id] = t

                    # Prune SQLite tours that no longer exist in MongoDB Atlas
                    if tours_map:
                        Tour.objects.exclude(id__in=tours_map.keys()).delete()

                    for t_id, t in tours_map.items():
                        slug_val = str(t.get('slug') or '').strip()
                        defaults = {
                            'title': str(t.get('title') or ''),
                            'slug': slug_val,
                            'route': str(t.get('route') or ''),
                            'price': str(t.get('price') or '280'),
                            'duration': str(t.get('duration') or '5 Days / 4 Nights'),
                            'imageUrl': str(t.get('imageUrl') or ''),
                            'isFeatured': bool(t.get('isFeatured', True)),
                            'description': str(t.get('description') or ''),
                            'longDescription': str(t.get('longDescription') or ''),
                            'highlights': str(t.get('highlights') or ''),
                            'inclusions': str(t.get('inclusions') or ''),
                            'exclusions': str(t.get('exclusions') or ''),
                            'seoKeywords': str(t.get('seoKeywords') or ''),
                            'itinerary_json': str(t.get('itinerary_json') or ''),
                        }
                        tour_obj = Tour.objects.filter(id=t_id).first()
                        if not tour_obj and slug_val:
                            tour_obj = Tour.objects.filter(slug=slug_val).first()

                        if tour_obj:
                            changed = False
                            for k, v in defaults.items():
                                if getattr(tour_obj, k) != v:
                                    setattr(tour_obj, k, v)
                                    changed = True
                            if changed:
                                tour_obj.save()
                        else:
                            defaults['id'] = t_id
                            Tour.objects.create(**defaults)

                # 3. Sync Hero Sections (Deduplicate by ID)
                raw_heroes = list(db.core_herosection.find())
                if raw_heroes:
                    heroes_map = {}
                    for h in raw_heroes:
                        h_id = h.get('id', 1)
                        heroes_map[h_id] = h

                    # Prune SQLite hero sections that no longer exist in MongoDB Atlas
                    if heroes_map:
                        HeroSection.objects.exclude(id__in=heroes_map.keys()).delete()

                    for h_id, h in heroes_map.items():
                        defaults = {
                            'title': str(h.get('title') or 'WILD YALA SAFARIS'),
                            'subtitle': str(h.get('subtitle') or "Ceylon's premier 4x4 game drives & luxury glamping."),
                            'badge_text': str(h.get('badge_text') or '🌿 YALA LEOPARD TRACKS'),
                            'imageUrl': str(h.get('imageUrl') or h.get('bg_image_url') or ''),
                            'button_primary_text': str(h.get('button_primary_text') or 'EXPLORE PACKAGES'),
                            'button_primary_url': str(h.get('button_primary_url') or '/packages/'),
                            'button_secondary_text': str(h.get('button_secondary_text') or 'BOOK SAFARI'),
                            'button_secondary_url': str(h.get('button_secondary_url') or '/contact/'),
                            'is_active': bool(h.get('is_active', True)),
                        }
                        hero_obj = HeroSection.objects.filter(id=h_id).first()
                        if hero_obj:
                            changed = False
                            for k, v in defaults.items():
                                if getattr(hero_obj, k) != v:
                                    setattr(hero_obj, k, v)
                                    changed = True
                            if changed:
                                hero_obj.save()
                        else:
                            defaults['id'] = h_id
                            HeroSection.objects.create(**defaults)

                # 4. Sync Blog Posts (Fast incremental hydration + Pruning deleted)
                sync_blogs_from_mongo_to_sqlite(force=True)

                # 5. Sync Guest Reviews (Prune deleted & sync new)
                mongo_revs = list(db.core_guestreview.find())
                if mongo_revs:
                    revs_map = {r.get('id'): r for r in mongo_revs if r.get('id') is not None}
                    if revs_map:
                        GuestReview.objects.exclude(id__in=revs_map.keys()).delete()

                    existing_rev_ids = set(GuestReview.objects.values_list('id', flat=True))
                    new_revs = [r for r_id, r in revs_map.items() if r_id not in existing_rev_ids]
                    if new_revs:
                        rev_items = []
                        for r in new_revs:
                            rev_items.append(GuestReview(
                                id=r.get('id'),
                                category=str(r.get('category') or 'leopard'),
                                name=str(r.get('name') or ''),
                                origin=str(r.get('origin') or 'London, UK'),
                                date=str(r.get('date') or 'August 2026'),
                                package=str(r.get('package') or 'Yala Block 1 Morning Leopard Game Drive'),
                                rating=int(r.get('rating') or 5),
                                comment=str(r.get('comment') or ''),
                                verified=bool(r.get('verified', True)),
                                avatar_url=str(r['avatar_url']) if r.get('avatar_url') else None,
                                photo_url=str(r['photo_url']) if r.get('photo_url') else None,
                                source=str(r.get('source') or 'Google Maps'),
                            ))
                        GuestReview.objects.bulk_create(rev_items, batch_size=300, ignore_conflicts=True)

                # 6. Sync Safari Bookings (Prune deleted & sync updates)
                mongo_books = list(db.core_safaribooking.find())
                if mongo_books:
                    books_map = {bk.get('id'): bk for bk in mongo_books if bk.get('id') is not None}
                    if books_map:
                        SafariBooking.objects.exclude(id__in=books_map.keys()).delete()

                    existing_booking_count = SafariBooking.objects.count()
                    if existing_booking_count == 0:
                        book_items = []
                        for bk in mongo_books:
                            raw_date = bk.get('safari_date')
                            if isinstance(raw_date, str) and raw_date:
                                try:
                                    s_date = datetime.strptime(raw_date[:10], '%Y-%m-%d').date()
                                except Exception:
                                    s_date = date.today()
                            elif isinstance(raw_date, (datetime, date)):
                                s_date = raw_date if isinstance(raw_date, date) else raw_date.date()
                            else:
                                s_date = date.today()

                            bk_id = bk.get('id') if isinstance(bk.get('id'), int) else None
                            book_items.append(SafariBooking(
                                id=bk_id,
                                package_title=str(bk.get('package_title') or ''),
                                full_name=str(bk.get('full_name') or ''),
                                country=str(bk.get('country') or ''),
                                email=str(bk.get('email') or ''),
                                phone_code=str(bk.get('phone_code') or '+94'),
                                phone_number=str(bk.get('phone_number') or ''),
                                safari_date=s_date,
                                guests=int(bk.get('guests') or 2),
                                adult_guests=int(bk.get('adult_guests') or 2),
                                child_guests=int(bk.get('child_guests') or 0),
                                under6_guests=int(bk.get('under6_guests') or 0),
                                include_meals=bool(bk.get('include_meals')),
                                meal_count=int(bk.get('meal_count') or 0),
                                meals_price_total=str(bk.get('meals_price_total') or '0.00'),
                                include_tickets=bool(bk.get('include_tickets')),
                                tickets_price_total=str(bk.get('tickets_price_total') or '0.00'),
                                base_price=str(bk.get('base_price') or '0.00'),
                                total_price=str(bk.get('total_price') or '0.00'),
                                message=str(bk.get('message') or ''),
                                status=str(bk.get('status') or 'Pending'),
                            ))
                        SafariBooking.objects.bulk_create(book_items, batch_size=100, ignore_conflicts=True)
                    else:
                        for bk in mongo_books:
                            bk_id = bk.get('id') if isinstance(bk.get('id'), int) else None
                            if bk_id:
                                bk_obj = SafariBooking.objects.filter(id=bk_id).first()
                                if bk_obj and bk_obj.status != str(bk.get('status') or 'Pending'):
                                    bk_obj.status = str(bk.get('status') or 'Pending')
                                    bk_obj.save()

        return True
    except Exception as e:
        logger.error(f"Error hydrating SQLite from MongoDB Atlas: {e}")
        return False



def sync_all_from_sqlite_to_mongo():
    """
    Pushes all existing Django models from SQLite to MongoDB Atlas.
    """
    try:
        db = get_mongo_db()
        if db is None:
            return False

        from .models import SafariPackage, Tour, BlogPost, HeroSection, GuestReview, SafariBooking

        for pkg in SafariPackage.objects.all():
            sync_model_to_mongo(pkg)
        for tour in Tour.objects.all():
            sync_model_to_mongo(tour)
        for blog in BlogPost.objects.all():
            sync_model_to_mongo(blog)
        for hero in HeroSection.objects.all():
            sync_model_to_mongo(hero)
        for rev in GuestReview.objects.all():
            sync_model_to_mongo(rev)
        for book in SafariBooking.objects.all():
            sync_model_to_mongo(book)
        return True
    except Exception as e:
        logger.error(f"Error seeding MongoDB Atlas from SQLite: {e}")
        return False

# ==============================================================================
# MongoDB Fetch Helpers (For Views)
# ==============================================================================

def fetch_mongo_packages():
    db = get_mongo_db()
    if db is None:
        return None
    try:
        docs = list(db.core_safaripackage.find())
        if not docs:
            docs = list(db.packages.find())
        return docs
    except Exception as e:
        logger.error(f"Error fetching packages from MongoDB: {e}")
        return None

def fetch_mongo_package_by_slug(slug):
    db = get_mongo_db()
    if db is None:
        return None
    try:
        doc = db.core_safaripackage.find_one({'slug': slug})
        if not doc and slug.isdigit():
            doc = db.core_safaripackage.find_one({'id': int(slug)})
        if not doc:
            doc = db.packages.find_one({'slug': slug})
        return MongoPackageModel(doc) if doc else None
    except Exception as e:
        logger.error(f"Error fetching package by slug {slug} from MongoDB: {e}")
        return None

def fetch_mongo_tours():
    db = get_mongo_db()
    if db is None:
        return None
    try:
        return list(db.core_tour.find())
    except Exception as e:
        logger.error(f"Error fetching tours from MongoDB: {e}")
        return None

def fetch_mongo_tour_by_slug(slug):
    db = get_mongo_db()
    if db is None:
        return None
    try:
        doc = db.core_tour.find_one({'slug': slug})
        if not doc and slug.isdigit():
            doc = db.core_tour.find_one({'id': int(slug)})
        return MongoTourModel(doc) if doc else None
    except Exception as e:
        logger.error(f"Error fetching tour by slug {slug} from MongoDB: {e}")
        return None

def fetch_mongo_blogs():
    db = get_mongo_db()
    if db is None:
        return None
    try:
        return list(db.core_blogpost.find())
    except Exception as e:
        logger.error(f"Error fetching blogs from MongoDB: {e}")
        return None

def fetch_mongo_blog_by_slug(slug):
    db = get_mongo_db()
    if db is None:
        return None
    try:
        doc = db.core_blogpost.find_one({'slug': slug})
        if not doc and slug.isdigit():
            doc = db.core_blogpost.find_one({'id': int(slug)})
        return MongoBlogModel(doc) if doc else None
    except Exception as e:
        logger.error(f"Error fetching blog by slug {slug} from MongoDB: {e}")
        return None

def fetch_mongo_reviews(limit=50):
    db = get_mongo_db()
    if db is None:
        return None
    try:
        return list(db.core_guestreview.find().limit(limit))
    except Exception as e:
        logger.error(f"Error fetching reviews from MongoDB: {e}")
        return None

def fetch_mongo_heroes():
    db = get_mongo_db()
    if db is None:
        return None
    try:
        docs = list(db.core_herosection.find())
        return [MongoHeroModel(d) for d in docs] if docs else None
    except Exception as e:
        logger.error(f"Error fetching hero sections from MongoDB: {e}")
        return None
