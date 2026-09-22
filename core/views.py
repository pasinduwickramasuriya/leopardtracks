from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from .models import SafariPackage, SafariBooking, BlogPost, HeroSection, Tour, GuestReview, optimize_cloudinary_url



def home(request):
    try:
        all_heroes = list(HeroSection.objects.all())
        active_heroes = [h for h in all_heroes if getattr(h, 'is_active', True)]
        hero = active_heroes[0] if active_heroes else (all_heroes[0] if all_heroes else None)
    except Exception:
        hero = None

    if not hero:
        try:
            from .mongodb import fetch_mongo_heroes
            m_heroes = fetch_mongo_heroes()
            if m_heroes:
                active_m = [h for h in m_heroes if getattr(h, 'is_active', True)]
                hero = active_m[0] if active_m else m_heroes[0]
        except Exception:
            pass

    if hero:
        if not getattr(hero, 'title', None) or not str(getattr(hero, 'title', '')).strip():
            hero.title = "YALA SAFARI PACKAGES & LUXURY TENTED CAMPS"
        if not getattr(hero, 'subtitle', None) or not str(getattr(hero, 'subtitle', '')).strip():
            hero.subtitle = "Ceylon's premier 4x4 game drives & luxury glamping expeditions in Yala National Park, Sri Lanka."



    # Fetch Dynamic Counts from Database with Safe Exception Handling
    try:
        total_packages = SafariPackage.objects.count()
        total_tours = Tour.objects.count()
        total_blogs = BlogPost.objects.count()
        total_reviews = GuestReview.objects.count()
    except Exception:
        total_packages = total_tours = total_blogs = total_reviews = 0

    # Fetch ALL Dynamic Safari Packages from Database / MongoDB Atlas Fallback
    packages_list = []
    try:
        packages_qs = SafariPackage.objects.all()
        for pkg in packages_qs:
            packages_list.append({
                'id': pkg.id,
                'title': pkg.title,
                'subtitle': pkg.subtitle,
                'slug': pkg.slug,
                'imageUrl': optimize_cloudinary_url(pkg.imageUrl or '/static/images/yala-tent.jpg', 800),
                'description': pkg.description,
                'category_label': pkg.category_label,
                'tag_class': pkg.tag_class,
                'clean_price': pkg.get_clean_price(),
                'price_unit': pkg.price_unit,
                'duration': pkg.duration,
                'vehicle': pkg.vehicle,
                'inclusions_list': pkg.get_inclusions_list()[:3],
            })
    except Exception:
        packages_list = []

    if not packages_list:
        try:
            from .mongodb import fetch_mongo_packages
            m_pkgs = fetch_mongo_packages()
            if m_pkgs:
                for pkg in m_pkgs:
                    inclusions_raw = pkg.get('inclusions', '') or ''
                    inclusions_list = [inc.strip() for inc in inclusions_raw.split('\n') if inc.strip()][:3]
                    price_str = str(pkg.get('price', '$55')).replace('$', '').strip()
                    packages_list.append({
                        'id': pkg.get('id', 1),
                        'title': pkg.get('title', ''),
                        'subtitle': pkg.get('subtitle', ''),
                        'slug': pkg.get('slug', ''),
                        'imageUrl': optimize_cloudinary_url(pkg.get('imageUrl', '') or '/static/images/yala-tent.jpg', 800),
                        'description': pkg.get('description', ''),
                        'category_label': pkg.get('category_label', 'SAFARI DRIVE'),
                        'tag_class': pkg.get('tag_class', 'tag-sage'),
                        'clean_price': price_str,
                        'price_unit': pkg.get('price_unit', 'per jeep'),
                        'duration': pkg.get('duration', '4 Hours'),
                        'vehicle': pkg.get('vehicle', 'Private 4x4 Jeep'),
                        'inclusions_list': inclusions_list,
                    })
        except Exception:
            pass

    # Fetch ALL Dynamic Island Round Tours from Database / MongoDB Atlas
    tours_list = []
    try:
        tours_qs = Tour.objects.all()
        for tr in tours_qs:
            tours_list.append({
                'id': tr.id,
                'title': tr.title,
                'slug': tr.slug,
                'route': tr.route,
                'duration': tr.duration,
                'clean_price': tr.get_clean_price(),
                'imageUrl': tr.get_tour_image_url(),
                'description': tr.description,
                'highlights_list': tr.get_highlights_list()[:3],
            })
    except Exception:
        tours_list = []

    if not tours_list:
        try:
            from .mongodb import fetch_mongo_tours
            m_tours = fetch_mongo_tours()
            if m_tours:
                for tr in m_tours:
                    hl_raw = tr.get('highlights', '') or ''
                    hl_list = [h.strip() for h in hl_raw.split('\n') if h.strip()][:3]
                    price_str = str(tr.get('price', '280')).replace('$', '').strip()
                    tours_list.append({
                        'id': tr.get('id', 1),
                        'title': tr.get('title', ''),
                        'slug': tr.get('slug', ''),
                        'route': tr.get('route', ''),
                        'duration': tr.get('duration', ''),
                        'clean_price': price_str,
                        'imageUrl': optimize_cloudinary_url(tr.get('imageUrl', '') or '/static/images/yala-wildlife-hero.jpg', 800),
                        'description': tr.get('description', ''),
                        'highlights_list': hl_list,
                    })
        except Exception:
            pass

    # Fetch ALL Dynamic Wildlife Field Journal Blogs from Database & Shuffle Randomly
    blogs_list = []
    try:
        blogs_qs = list(BlogPost.objects.all())
        import random
        random.shuffle(blogs_qs)

        for b in blogs_qs:
            paragraphs = b.get_paragraphs()
            excerpt = paragraphs[0] if paragraphs else b.content[:140] + "..."
            blogs_list.append({
                'id': b.id,
                'title': b.title,
                'slug': b.slug,
                'category': b.category,
                'author': b.author,
                'imageUrl': optimize_cloudinary_url(b.imageUrl or '/static/images/yala-wildlife-hero.jpg', 800),
                'excerpt': excerpt[:140] + ("..." if len(excerpt) > 140 else ""),
                'created_at': b.created_at.strftime('%b %d, %Y') if getattr(b, 'created_at', None) else 'Aug 2026',
            })
    except Exception:
        blogs_list = []

    if not blogs_list:
        try:
            from .mongodb import fetch_mongo_blogs
            m_blogs = fetch_mongo_blogs()
            if m_blogs:
                for b in m_blogs:
                    content_text = b.get('content', '') or ''
                    blogs_list.append({
                        'id': b.get('id', 1),
                        'title': b.get('title', ''),
                        'slug': b.get('slug', ''),
                        'category': b.get('category', 'WILDLIFE'),
                        'author': b.get('author', 'Senior Naturalist Desk'),
                        'imageUrl': optimize_cloudinary_url(b.get('imageUrl', '') or '/static/images/yala-wildlife-hero.jpg', 800),
                        'excerpt': content_text[:140] + "...",
                        'created_at': 'Aug 2026',
                    })
        except Exception:
            pass

    # Fetch Top Verified Google Maps Reviews with High-Res Photos
    reviews_list = get_all_google_reviews()[:6]



    # Calculate totals
    total_packages = max(total_packages, len(packages_list))
    total_tours = max(total_tours, len(tours_list))
    total_blogs = max(total_blogs, len(blogs_list))
    total_reviews = max(total_reviews, len(reviews_list))

    # Dynamic Stats Summary driven by database counts
    stats_summary = [
        {'value': f"{total_packages}+", 'label': 'Curated Safari Packages', 'icon': 'fa-truck-monster'},
        {'value': '98%', 'label': 'Leopard Sighting Success', 'icon': 'fa-paw'},
        {'value': f"{total_reviews}+", 'label': 'Verified Guest Reviews', 'icon': 'fa-star'},
        {'value': '15+', 'label': 'Years Eco-Expeditions', 'icon': 'fa-calendar-check'},
    ]

    context = {
        'title': 'Discoveryala | Yala National Park Safaris & Luxury Camping Sri Lanka',
        'hero': hero,
        'home_packages': packages_list,
        'home_tours': tours_list,
        'home_blogs': blogs_list,
        'home_reviews': reviews_list,
        'stats_summary': stats_summary,
        'total_packages_count': total_packages,
        'total_tours_count': total_tours,
        'total_blogs_count': total_blogs,
        'total_reviews_count': total_reviews,
    }
    return render(request, 'core/home.html', context)






def packages(request):
    packages_list = []
    try:
        packages_queryset = SafariPackage.objects.all()
        for pkg in packages_queryset:
            clean_p = pkg.get_clean_price()
            packages_list.append({
                'id': pkg.id,
                'title': pkg.title,
                'subtitle': pkg.subtitle,
                'slug': pkg.slug,
                'imageUrl': pkg.imageUrl,
                'description': pkg.description,
                'category': pkg.category,
                'category_label': pkg.category_label,
                'tag_class': pkg.tag_class,
                'price_type': pkg.price_type,
                'price': clean_p,
                'get_clean_price': clean_p,
                'price_unit': pkg.price_unit,
                'mealPrice': pkg.mealPrice,
                'ticketPrice': pkg.ticketPrice,
                'includes_tickets': pkg.includes_tickets,
                'ticket_addon_price': pkg.ticket_addon_price,
                'includes_breakfast': pkg.includes_breakfast,
                'breakfast_addon_price': pkg.breakfast_addon_price,
                'duration': pkg.duration,
                'vehicle': pkg.vehicle,
                'inclusions': pkg.get_inclusions_list(),
                'exclusions': pkg.get_exclusions_list(),
                'highlights_list': pkg.get_highlights_list(),
                'highlights': pkg.highlights,
                'featured': pkg.featured
            })
    except Exception:
        packages_list = []

    if not packages_list:
        try:
            from .mongodb import fetch_mongo_packages
            m_pkgs = fetch_mongo_packages()
            if m_pkgs:
                for pkg in m_pkgs:
                    inc_raw = pkg.get('inclusions', '') or ''
                    exc_raw = pkg.get('exclusions', '') or ''
                    hl_raw = pkg.get('highlights', '') or ''

                    inc_list = [i.strip() for i in inc_raw.split('\n') if i.strip()]
                    exc_list = [e.strip() for e in exc_raw.split('\n') if e.strip()]
                    hl_list = [h.strip() for h in hl_raw.split('\n') if h.strip()]

                    price_clean = str(pkg.get('price', '$55')).replace('$', '').strip()

                    packages_list.append({
                        'id': pkg.get('id', 1),
                        'title': pkg.get('title', ''),
                        'subtitle': pkg.get('subtitle', ''),
                        'slug': pkg.get('slug', ''),
                        'imageUrl': pkg.get('imageUrl', '') or '/static/images/yala-tent.jpg',
                        'description': pkg.get('description', ''),
                        'category': pkg.get('category', 'half-day'),
                        'category_label': pkg.get('category_label', 'HALF-DAY DRIVE'),
                        'tag_class': pkg.get('tag_class', 'tag-sage'),
                        'price_type': pkg.get('price_type', 'jeep_only'),
                        'price': price_clean,
                        'get_clean_price': price_clean,
                        'price_unit': pkg.get('price_unit', 'per jeep'),
                        'mealPrice': pkg.get('mealPrice', '0'),
                        'ticketPrice': pkg.get('ticketPrice', '46'),
                        'includes_tickets': pkg.get('includes_tickets', False),
                        'ticket_addon_price': pkg.get('ticket_addon_price', ''),
                        'includes_breakfast': pkg.get('includes_breakfast', False),
                        'breakfast_addon_price': pkg.get('breakfast_addon_price', ''),
                        'duration': pkg.get('duration', '4 Hours'),
                        'vehicle': pkg.get('vehicle', 'Private 4x4 Jeep'),
                        'inclusions': inc_list,
                        'exclusions': exc_list,
                        'highlights_list': hl_list,
                        'highlights': hl_raw,
                        'featured': pkg.get('featured', False)
                    })
        except Exception:
            pass

    featured_package = next((p for p in packages_list if p.get('featured')), packages_list[0] if packages_list else None)

    context = {
        'title': 'Yala Safari Packages & Expeditions | Discoveryala',
        'packages_list': packages_list,
        'featured_package': featured_package,
    }
    return render(request, 'core/packages.html', context)


def package_detail(request, slug):
    package = None
    try:
        package = SafariPackage.objects.filter(slug=slug).first()
        if not package and slug.isdigit():
            package = SafariPackage.objects.filter(id=int(slug)).first()
    except Exception:
        package = None

    if not package:
        try:
            from .mongodb import fetch_mongo_package_by_slug
            package = fetch_mongo_package_by_slug(slug)
        except Exception:
            package = None

    if not package:
        return redirect('packages')

    other_packages = []
    try:
        if hasattr(package, 'id'):
            other_packages = list(SafariPackage.objects.exclude(id=package.id)[:3])
    except Exception:
        other_packages = []

    if not other_packages:
        try:
            from .mongodb import fetch_mongo_packages, MongoPackageModel
            m_pkgs = fetch_mongo_packages()
            if m_pkgs:
                other_packages = [MongoPackageModel(p) for p in m_pkgs if p.get('slug') != slug][:3]
        except Exception:
            pass

    reviews_list = []
    try:
        reviews_list = list(GuestReview.objects.filter(rating__gte=4).exclude(comment='').order_by('-created_at')[:3])
    except Exception:
        reviews_list = []

    context = {
        'title': f'{package.title} | Discoveryala',
        'package': package,
        'inclusions_list': package.get_inclusions_list(),
        'exclusions_list': package.get_exclusions_list(),
        'highlights_list': package.get_highlights_list(),
        'image_urls_list': package.get_image_urls_list(),
        'other_packages': other_packages,
        'reviews_list': reviews_list,
    }
    return render(request, 'core/package_detail.html', context)


def create_booking(request):
    if request.method == 'POST':
        try:
            package_title = request.POST.get('package_title', 'Safari Booking')
            full_name = request.POST.get('full_name', '')
            country = request.POST.get('country', '')
            email = request.POST.get('email', '')
            phone_code = request.POST.get('phone_code', '+94')
            phone_number = request.POST.get('phone_number', '')
            
            safari_date = request.POST.get('safari_date')
            adult_guests = int(request.POST.get('adult_guests', 2) or 2)
            child_guests = int(request.POST.get('child_guests', 0) or 0)
            under6_guests = int(request.POST.get('under6_guests', 0) or 0)
            guests = adult_guests + child_guests + under6_guests
            if guests == 0:
                guests = int(request.POST.get('guests', 2) or 2)
            
            include_meals = request.POST.get('include_meals') in ['true', 'on', 'True', '1']
            meal_count = int(request.POST.get('meal_count', 0) or 0) if include_meals else 0
            include_tickets = request.POST.get('include_tickets') in ['true', 'on', 'True', '1']
            
            base_price = float(request.POST.get('base_price', 0.0) or 0)
            meals_price_total = float(request.POST.get('meals_price_total', 0.0) or 0)
            tickets_price_total = float(request.POST.get('tickets_price_total', 0.0) or 0)
            total_price = float(request.POST.get('total_price', 0.0) or 0)
            message = request.POST.get('message', '')

            import uuid
            try:
                booking = SafariBooking.objects.create(
                    package_title=package_title,
                    full_name=full_name,
                    country=country,
                    email=email,
                    phone_code=phone_code,
                    phone_number=phone_number,
                    safari_date=safari_date,
                    guests=guests,
                    adult_guests=adult_guests,
                    child_guests=child_guests,
                    under6_guests=under6_guests,
                    include_meals=include_meals,
                    meal_count=meal_count,
                    meals_price_total=meals_price_total,
                    include_tickets=include_tickets,
                    tickets_price_total=tickets_price_total,
                    base_price=base_price,
                    total_price=total_price,
                    message=message,
                    status='Pending'
                )
                booking_id = str(booking.id)
            except Exception as db_err:
                booking_id = str(uuid.uuid4())[:8].upper()

            # Send Rich HTML Email Confirmation to Guest & Notification Email to Admin
            try:
                from django.core.mail import EmailMultiAlternatives
                from django.conf import settings

                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Discoveryala <discoveryala0@gmail.com>')
                admin_email = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', 'discoveryala0@gmail.com')
                if getattr(settings, 'EMAIL_HOST_USER', ''):
                    admin_email = getattr(settings, 'EMAIL_HOST_USER')

                # 1. Confirmation Email to Guest (Rich HTML Theme)
                guest_subject = f"Safari Reservation Received - {package_title} | Discoveryala"
                
                guest_text = f"""Ayubowan {full_name}!

Thank you for reserving your safari expedition with Discoveryala!
Booking Reference: #{booking_id}
Package: {package_title}
Safari Date: {safari_date}
Guests: {guests}
Total Estimated Amount: ${total_price:.2f}

Hotline / WhatsApp: +94 778158004
Email: discoveryala0@gmail.com

Our safari coordinator desk will contact you shortly to confirm pickup details.
Discoveryala Expeditions Team
"""

                guest_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Safari Reservation Confirmation</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800&family=Playfair+Display:wght@700;900&display=swap');
    body {{ font-family: 'Poppins', Arial, sans-serif; background-color: #FAF6EE; color: #233325; margin: 0; padding: 0; -webkit-font-smoothing: antialiased; }}
    .email-wrapper {{ background-color: #FAF6EE; padding: 24px 12px; }}
    .email-container {{ max-width: 620px; margin: 0 auto; background: #FFFFFF; border-radius: 24px; overflow: hidden; border: 1px solid rgba(71, 81, 40, 0.18); box-shadow: 0 16px 45px rgba(18, 33, 24, 0.08); }}
    .email-header {{ background-color: #122118; padding: 38px 28px 30px; text-align: center; color: #FFFFFF; border-bottom: 3px solid #D4AF37; position: relative; }}
    .brand-pill {{ display: inline-block; background: rgba(212, 175, 55, 0.15); color: #D4AF37; font-size: 10px; font-weight: 800; letter-spacing: 2.5px; text-transform: uppercase; padding: 6px 18px; border-radius: 30px; border: 1px solid rgba(212, 175, 55, 0.35); margin-bottom: 14px; }}
    .header-title {{ font-family: 'Playfair Display', Georgia, serif; font-size: 25px; font-weight: 900; letter-spacing: 1px; margin: 0; color: #FFFFFF; text-transform: uppercase; }}
    .header-sub {{ font-size: 13px; color: #E7EBD9; margin-top: 8px; font-weight: 600; letter-spacing: 0.5px; }}
    .ref-badge {{ display: inline-block; background: rgba(255, 255, 255, 0.1); color: #D4AF37; font-size: 12px; font-weight: 700; padding: 4px 14px; border-radius: 12px; margin-top: 10px; border: 1px dashed rgba(212, 175, 55, 0.4); }}
    .email-body {{ padding: 36px 30px; background-color: #FAF6EE; }}
    .greeting {{ font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 900; color: #475128; margin-bottom: 10px; }}
    .intro-p {{ font-size: 14px; line-height: 1.7; color: #333333; margin-bottom: 26px; }}
    .card-box {{ background: #FFFFFF; border-radius: 18px; padding: 24px; border: 1px solid rgba(71, 81, 40, 0.14); margin-bottom: 22px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); }}
    .card-title {{ font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; color: #606C38; margin-bottom: 16px; border-bottom: 1px solid rgba(71, 81, 40, 0.1); padding-bottom: 8px; display: flex; align-items: center; justify-content: space-between; }}
    .info-row {{ display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 12px; line-height: 1.4; border-bottom: 1px dashed rgba(71, 81, 40, 0.08); padding-bottom: 8px; }}
    .info-row:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
    .info-label {{ color: #666666; font-weight: 500; }}
    .info-value {{ font-weight: 700; color: #233325; text-align: right; }}
    .badge-green {{ background: #E7EBD9; color: #475128; font-size: 11px; font-weight: 800; padding: 3px 10px; border-radius: 10px; text-transform: uppercase; }}
    .total-box {{ background: #475128; color: #FFFFFF; border-radius: 16px; padding: 20px 22px; margin-top: 16px; border: 1px solid rgba(212, 175, 55, 0.35); box-shadow: 0 6px 20px rgba(71, 81, 40, 0.2); }}
    .total-amount {{ font-family: 'Playfair Display', Georgia, serif; font-size: 26px; font-weight: 900; color: #D4AF37; float: right; margin-top: -2px; }}
    .phone-contact-box {{ background: linear-gradient(135deg, #606C38 0%, #475128 100%); color: #FFFFFF; border-radius: 18px; padding: 24px; text-align: center; margin-bottom: 22px; box-shadow: 0 10px 25px rgba(96, 108, 56, 0.25); border: 1px solid rgba(212, 175, 55, 0.3); }}
    .phone-number-btn {{ display: inline-block; background: #D4AF37; color: #122118; text-decoration: none; padding: 12px 28px; border-radius: 30px; font-weight: 900; font-size: 15px; margin-top: 12px; letter-spacing: 0.5px; box-shadow: 0 4px 15px rgba(0,0,0,0.15); }}
    .note-box {{ background: #E7EBD9; border-radius: 14px; padding: 18px; font-size: 13px; color: #475128; margin-top: 22px; line-height: 1.65; border-left: 4px solid #606C38; }}
    .email-footer {{ background-color: #122118; padding: 30px 24px; text-align: center; font-size: 12px; color: #999999; border-top: 1px solid rgba(255,255,255,0.06); }}
    .footer-link {{ color: #D4AF37; text-decoration: none; font-weight: 700; }}
</style>
</head>
<body>
<div class="email-wrapper">
    <div class="email-container">
        <div class="email-header">
            <span class="brand-pill">DISCOVERYALA EXPEDITIONS</span>
            <h1 class="header-title">🐆 SAFARI RESERVATION CONFIRMED</h1>
            <div class="header-sub">Yala & Bundala National Park Game Drives</div>
            <div class="ref-badge">Booking Reference: #{booking_id}</div>
        </div>
        
        <div class="email-body">
            <div class="greeting">Ayubowan, {full_name}! 🌿</div>
            <p class="intro-p">Thank you for reserving your safari expedition with <strong>Discoveryala</strong>! We have received your booking request and our naturalist desk is preparing your private 4x4 game drive itinerary.</p>
            
            <!-- Reservation Details Card -->
            <div class="card-box">
                <div class="card-title"><span>01. Safari Expedition Summary</span> <span class="badge-green">CONFIRMED</span></div>
                <div class="info-row"><span class="info-label">Safari Package:</span><span class="info-value">{package_title}</span></div>
                <div class="info-row"><span class="info-label">Safari Date:</span><span class="info-value" style="color: #606C38; font-weight: 800;">{safari_date}</span></div>
                <div class="info-row"><span class="info-label">Guests Count:</span><span class="info-value">{guests} Guest(s)</span></div>
                <div class="info-row"><span class="info-label">Hotel Pickup & Drop:</span><span class="info-value" style="color: #606C38;">FREE (Yala / Tissa / Kirinda)</span></div>
            </div>

            <!-- Guest Info Card -->
            <div class="card-box">
                <div class="card-title">02. Guest Contact Details</div>
                <div class="info-row"><span class="info-label">Full Name:</span><span class="info-value">{full_name}</span></div>
                <div class="info-row"><span class="info-label">Country:</span><span class="info-value">{country}</span></div>
                <div class="info-row"><span class="info-label">Email:</span><span class="info-value">{email}</span></div>
                <div class="info-row"><span class="info-label">Phone Number:</span><span class="info-value">{phone_code} {phone_number}</span></div>
            </div>

            <!-- Pricing Summary Card -->
            <div class="card-box">
                <div class="card-title">03. Estimated Pricing Breakdown</div>
                <div class="info-row"><span class="info-label">Base Safari Game Drive:</span><span class="info-value">${base_price:.2f}</span></div>
                <div class="info-row"><span class="info-label">Meal / Breakfast Add-ons:</span><span class="info-value">{'Included ($0.00)' if include_meals and meals_price_total == 0 else ('$' + f'{meals_price_total:.2f}') if include_meals else 'Not Selected'}</span></div>
                <div class="info-row"><span class="info-label">National Park Entrance Tickets:</span><span class="info-value">{'Included ($0.00)' if include_tickets and tickets_price_total == 0 else ('$' + f'{tickets_price_total:.2f}') if include_tickets else 'Not Selected'}</span></div>
                
                <div class="total-box">
                    <span class="total-amount">${total_price:.2f}</span>
                    <span style="font-size: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; line-height: 28px;">Total Estimated Amount</span>
                </div>
            </div>

            {f'<div class="card-box"><div class="card-title">04. Special Requests / Notes</div><div style="font-size: 13px; color: #444444; font-style: italic; line-height: 1.6;">"{message}"</div></div>' if message else ''}

            <!-- Direct Phone / WhatsApp Contact Callout Card -->
            <div class="phone-contact-box">
                <div style="font-size: 11px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 6px; color: #E7EBD9;">NEED IMMEDIATE SAFARI ASSISTANCE?</div>
                <div style="font-size: 14px; line-height: 1.5; margin-bottom: 8px;">Call or WhatsApp our 24/7 Safari Desk directly:</div>
                <a href="https://wa.me/94778158004" class="phone-number-btn">📞 CALL / WHATSAPP: +94 778158004</a>
            </div>

            <div class="note-box">
                📌 <strong>Next Steps:</strong> Our senior safari coordinator desk will contact you shortly via Email / WhatsApp (<a href="https://wa.me/94778158004" style="color: #475128; font-weight: 700;">+94 778158004</a>) to verify your hotel pickup location and driver vehicle assignment.
            </div>
        </div>

        <div class="email-footer">
            <p style="margin: 0 0 8px 0; font-weight: 700; color: #FFFFFF; font-size: 13px;">Discoveryala Expeditions & Luxury Safaris</p>
            <p style="margin: 0 0 10px 0;">Yala National Park Buffer Zone, Tissamaharama, Sri Lanka</p>
            <p style="margin: 0 0 12px 0; font-weight: 800; color: #D4AF37; font-size: 13px;">Hotline / WhatsApp: +94 778158004</p>
            <p style="margin: 0;">Email: <a href="mailto:discoveryala0@gmail.com" class="footer-link">discoveryala0@gmail.com</a> | Web: <a href="https://yalaleopardtracks.com" class="footer-link">yalaleopardtracks.com</a></p>
        </div>
    </div>
</div>
</body>
</html>"""

                msg_guest = EmailMultiAlternatives(guest_subject, guest_text, from_email, [email])
                msg_guest.attach_alternative(guest_html, "text/html")
                msg_guest.send(fail_silently=False)

                # 2. Notification Email to Admin (Rich HTML Theme)
                admin_subject = f"🚨 NEW BOOKING ALERT: {package_title} - {full_name} ({safari_date})"
                admin_text = f"""NEW SAFARI RESERVATION ALERT!
Customer: {full_name} ({country})
Email: {email} | Phone: {phone_code} {phone_number}
Package: {package_title}
Date: {safari_date} | Guests: {guests}
Total: ${total_price:.2f}

Safari Desk Hotline: +94 778158004
"""

                admin_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{ font-family: 'Poppins', Arial, sans-serif; background-color: #FAF6EE; color: #233325; margin: 0; padding: 20px; }}
    .admin-card {{ max-width: 600px; margin: 0 auto; background: #FFFFFF; border-radius: 20px; padding: 30px; border: 1px solid rgba(71,81,40,0.2); box-shadow: 0 12px 35px rgba(0,0,0,0.08); }}
    .alert-header {{ background: #122118; color: #FFFFFF; padding: 18px 24px; border-radius: 14px; font-size: 15px; font-weight: 800; letter-spacing: 1px; margin-bottom: 22px; border-left: 4px solid #D4AF37; }}
    .alert-price {{ float: right; background: #D4AF37; color: #122118; padding: 4px 14px; border-radius: 12px; font-weight: 900; font-size: 16px; }}
    .row {{ margin-bottom: 12px; font-size: 14px; border-bottom: 1px dashed rgba(71,81,40,0.15); padding-bottom: 8px; display: flex; justify-content: space-between; }}
    .label {{ font-weight: 600; color: #475128; width: 140px; }}
    .val {{ color: #233325; font-weight: 700; text-align: right; }}
    .btn-admin {{ display: block; background: #606C38; color: #FFFFFF; text-decoration: none; padding: 14px 24px; border-radius: 30px; font-weight: 800; margin-top: 24px; text-align: center; font-size: 14px; letter-spacing: 1px; box-shadow: 0 6px 20px rgba(96,108,56,0.25); }}
</style>
</head>
<body>
<div class="admin-card">
    <div class="alert-header">
        <span class="alert-price">${total_price:.2f}</span>
        🚨 NEW SAFARI RESERVATION
    </div>

    <div style="margin-bottom: 22px; font-size: 17px; font-weight: 800; color: #233325; border-bottom: 2px solid #606C38; padding-bottom: 10px;">
        Package: {package_title}
    </div>

    <div class="row"><span class="label">Customer Name:</span><span class="val">{full_name}</span></div>
    <div class="row"><span class="label">Country:</span><span class="val">{country}</span></div>
    <div class="row"><span class="label">Email:</span><span class="val">{email}</span></div>
    <div class="row"><span class="label">Phone Number:</span><span class="val">{phone_code} {phone_number}</span></div>
    <div class="row"><span class="label">Safari Date:</span><span class="val" style="color: #606C38; font-weight: 800;">{safari_date}</span></div>
    <div class="row"><span class="label">Guests:</span><span class="val">{guests} Guest(s)</span></div>
    <div class="row"><span class="label">Meals:</span><span class="val">{'Yes' if include_meals else 'No'} (${meals_price_total:.2f})</span></div>
    <div class="row"><span class="label">Tickets:</span><span class="val">{'Yes' if include_tickets else 'No'} (${tickets_price_total:.2f})</span></div>
    <div class="row"><span class="label">Total Price:</span><span class="val" style="font-size: 18px; color: #475128; font-weight: 900;">${total_price:.2f}</span></div>

    {f'<div style="margin-top: 16px; background: #E7EBD9; padding: 16px; border-radius: 14px; font-size: 13px; color: #475128; border-left: 3px solid #606C38;"><strong>Special Requests / Customer Note:</strong><br>"{message}"</div>' if message else ''}

    <div style="margin-top: 18px; text-align: center; font-size: 13px; font-weight: 700; color: #606C38;">
        Safari Hotline / WhatsApp: +94 778158004
    </div>

    <a href="http://127.0.0.1:8000/admin/core/safaribooking/{booking_id}/change/" class="btn-admin">OPEN IN DJANGO ADMIN PANEL</a>
</div>
</body>
</html>"""

                admin_recipients = ['discoveryala0@gmail.com', 'pasinduwickramasooriya@gmail.com']
                msg_admin = EmailMultiAlternatives(admin_subject, admin_text, from_email, admin_recipients)
                msg_admin.attach_alternative(admin_html, "text/html")
                msg_admin.send(fail_silently=False)

            except Exception as mail_err:
                print('EMAIL_SEND_ERROR_LOG:', str(mail_err))

            return JsonResponse({'status': 'success', 'message': 'Thank you! Your safari reservation request has been submitted successfully. A confirmation email has been sent to your inbox.', 'booking_id': str(booking_id)})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def blog(request):
    try:
        from .mongodb import sync_blogs_from_mongo_to_sqlite
        sync_blogs_from_mongo_to_sqlite()
    except Exception:
        pass

    all_posts = []
    try:
        all_posts = list(BlogPost.objects.all())
    except Exception:
        all_posts = []

    if not all_posts:
        try:
            from .mongodb import fetch_mongo_blogs, MongoBlogModel
            m_blogs = fetch_mongo_blogs()
            if m_blogs:
                all_posts = [MongoBlogModel(b) for b in m_blogs]
        except Exception:
            pass

    featured_post = next((p for p in all_posts if getattr(p, 'featured', False)), all_posts[0] if all_posts else None)
    other_posts = [p for p in all_posts if p != featured_post]

    context = {
        'title': 'Yala Wildlife Blog & Field Journal | Discoveryala',
        'featured_post': featured_post,
        'other_posts': other_posts,
        'all_posts': all_posts
    }
    return render(request, 'core/blog.html', context)

def blog_detail(request, slug):
    post = BlogPost.objects.filter(slug=slug).first()
    if not post and slug.isdigit():
        post = BlogPost.objects.filter(id=int(slug)).first()

    # If post not in local SQLite, query live MongoDB Atlas directly!
    if not post:
        try:
            from .mongodb import fetch_mongo_blog_by_slug
            mongo_post = fetch_mongo_blog_by_slug(slug)
            if mongo_post:
                # Cache into local SQLite for fast subsequent access
                post, _ = BlogPost.objects.update_or_create(
                    id=mongo_post.id,
                    defaults={
                        'title': mongo_post.title,
                        'slug': mongo_post.slug,
                        'category': mongo_post.category,
                        'author': mongo_post.author,
                        'imageUrl': mongo_post.imageUrl,
                        'content': mongo_post.content,
                        'featured': mongo_post.featured,
                    }
                )
        except Exception:
            pass

    if not post:
        return redirect('blog')

    all_posts = []
    try:
        all_posts = list(BlogPost.objects.all())
    except Exception:
        all_posts = []

    recent_posts = [p for p in all_posts if p.id != post.id][:3]

    context = {
        'title': f'{post.title} | Discoveryala Journal',
        'post': post,
        'paragraphs': post.get_paragraphs(),
        'recent_posts': recent_posts
    }
    return render(request, 'core/blog_detail.html', context)

def tours(request):
    tours_list = []
    try:
        tours_queryset = Tour.objects.all()
        for tr in tours_queryset:
            clean_p = tr.get_clean_price()
            tours_list.append({
                'id': tr.id,
                'title': tr.title,
                'slug': tr.slug,
                'route': tr.route,
                'duration': tr.duration,
                'price': clean_p,
                'get_clean_price': clean_p,
                'imageUrl': tr.get_tour_image_url(),
                'description': tr.description,
                'highlights_list': tr.get_highlights_list(),
                'inclusions_list': tr.get_inclusions_list(),
                'isFeatured': tr.isFeatured,
            })
    except Exception:
        tours_list = []

    if not tours_list:
        try:
            from .mongodb import fetch_mongo_tours
            m_tours = fetch_mongo_tours()
            if m_tours:
                for tr in m_tours:
                    hl_raw = tr.get('highlights', '') or ''
                    inc_raw = tr.get('inclusions', '') or ''
                    hl_list = [h.strip() for h in hl_raw.split('\n') if h.strip()]
                    inc_list = [i.strip() for i in inc_raw.split('\n') if i.strip()]
                    clean_p = str(tr.get('price', '280')).replace('$', '').strip()
                    tours_list.append({
                        'id': tr.get('id', 1),
                        'title': tr.get('title', ''),
                        'slug': tr.get('slug', ''),
                        'route': tr.get('route', ''),
                        'duration': tr.get('duration', ''),
                        'price': clean_p,
                        'get_clean_price': clean_p,
                        'imageUrl': tr.get('imageUrl', '') or '/static/images/yala-wildlife-hero.jpg',
                        'description': tr.get('description', ''),
                        'highlights_list': hl_list,
                        'inclusions_list': inc_list,
                        'isFeatured': tr.get('isFeatured', True),
                    })
        except Exception:
            pass

    featured_tour = next((t for t in tours_list if t.get('isFeatured')), tours_list[0] if tours_list else None)

    context = {
        'title': 'Sri Lanka Round Tours & Chauffeur Transport | Discoveryala',
        'tours_list': tours_list,
        'featured_tour': featured_tour,
    }
    return render(request, 'core/tours.html', context)

    try:
        tours_queryset = list(Tour.objects.all())
    except Exception:
        tours_queryset = []

    tours_list = []
    for item in tours_queryset:
        clean_p = item.get_clean_price()
        tours_list.append({
            'id': item.id,
            'title': item.title,
            'slug': item.slug,
            'route': item.route,
            'price': clean_p,
            'get_clean_price': clean_p,
            'duration': item.duration,
            'imageUrl': item.get_tour_image_url(),
            'isFeatured': item.isFeatured,
            'description': item.description,
            'longDescription': item.longDescription,
            'highlights': item.get_highlights_list(),
            'inclusions': item.get_inclusions_list(),
            'exclusions': item.get_exclusions_list(),
            'itinerary': item.get_itinerary_list(),
        })

    context = {
        'title': 'Sri Lanka Tours & Islandwide Private Transport | Discoveryala',
        'tours_list': tours_list,
    }
    return render(request, 'core/tours.html', context)


def tour_detail(request, slug):
    tour = None
    all_tours = []
    try:
        all_tours = list(Tour.objects.all())
        tour = next((t for t in all_tours if t.slug == slug), None)
    except Exception:
        tour = None

    if not tour:
        try:
            from .mongodb import fetch_mongo_tour_by_slug, fetch_mongo_tours, MongoTourModel
            tour = fetch_mongo_tour_by_slug(slug)
            if not all_tours:
                m_tours = fetch_mongo_tours()
                if m_tours:
                    all_tours = [MongoTourModel(t) for t in m_tours]
        except Exception:
            pass

    if not tour:
        return redirect('tours')

    recent_tours = [t for t in all_tours if getattr(t, 'slug', '') != slug][:3]


    if request.method == 'POST':
        full_name = request.POST.get('full_name', '')
        email = request.POST.get('email', '')
        country = request.POST.get('country', '')
        phone_code = request.POST.get('phone_code', '+94')
        phone_number = request.POST.get('phone_number', '')
        safari_date = request.POST.get('safari_date', '')
        guests = int(request.POST.get('guests', 2) or 2)
        message = request.POST.get('message', '')

        import uuid
        try:
            booking = SafariBooking.objects.create(
                package_title=tour.title,
                full_name=full_name,
                country=country,
                email=email,
                phone_code=phone_code,
                phone_number=phone_number,
                safari_date=safari_date,
                guests=guests,
                adult_guests=guests,
                base_price=tour.price,
                total_price=tour.price,
                message=message,
                status='Pending'
            )
            booking_id = str(booking.id)
        except Exception as db_err:
            print("TOUR_BOOKING_DB_ERROR:", str(db_err))
            booking_id = str(uuid.uuid4())[:8].upper()

        # Send Email Confirmation to Guest & Admin in a non-blocking background thread
        def _async_send_emails():
            try:
                from django.core.mail import EmailMultiAlternatives
                from django.conf import settings

                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Discoveryala <discoveryala0@gmail.com>')
                
                guest_subject = f"Tour Reservation Confirmation - {tour.title} | Discoveryala"
                guest_text = f"Ayubowan {full_name}!\n\nThank you for booking {tour.title}.\nBooking Ref: #{booking_id}\nDate: {safari_date}\nGuests: {guests}\nPrice: ${tour.price}\n\nOur team will contact you shortly."
                
                guest_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
    body {{ font-family: Arial, sans-serif; background: #FAF6EE; padding: 20px; color: #233325; }}
    .box {{ max-width: 580px; margin: 0 auto; background: #FFF; padding: 30px; border-radius: 16px; border: 1px solid #606C38; }}
    .hdr {{ background: #122118; color: #FFF; padding: 20px; text-align: center; border-radius: 12px; font-size: 20px; font-weight: bold; }}
    .row {{ border-bottom: 1px dashed #DDD; padding: 10px 0; font-size: 14px; }}
    .lbl {{ font-weight: bold; color: #475128; }}
</style>
</head>
<body>
<div class="box">
    <div class="hdr">DISCOVERYALA - TOUR RESERVATION</div>
    <p>Ayubowan <strong>{full_name}</strong>,</p>
    <p>Thank you for reserving your <strong>{tour.title}</strong> tour with Discoveryala!</p>
    <div class="row"><span class="lbl">Booking Ref:</span> #{booking_id}</div>
    <div class="row"><span class="lbl">Tour Package:</span> {tour.title}</div>
    <div class="row"><span class="lbl">Tour Date:</span> {safari_date}</div>
    <div class="row"><span class="lbl">Guests:</span> {guests} Person(s)</div>
    <div class="row"><span class="lbl">Country:</span> {country}</div>
    <div class="row"><span class="lbl">Phone:</span> {phone_code} {phone_number}</div>
    <div class="row"><span class="lbl">Price:</span> ${tour.price} USD</div>
    {'<div class="row"><span class="lbl">Special Request:</span> ' + message + '</div>' if message else ''}
    <p style="margin-top:20px; font-size:13px; color:#666;">Our tour desk team will reach out to confirm your pickup location and driver details.</p>
</div>
</body>
</html>"""

                msg = EmailMultiAlternatives(guest_subject, guest_text, from_email, [email])
                msg.attach_alternative(guest_html, "text/html")
                msg.send(fail_silently=True)

                admin_subject = f"🚨 NEW TOUR BOOKING: {tour.title} - {full_name}"
                admin_text = f"New Tour Booking: {tour.title}\nGuest: {full_name} ({email})\nPhone: {phone_code} {phone_number}\nDate: {safari_date}\nGuests: {guests}"
                msg_admin = EmailMultiAlternatives(admin_subject, admin_text, from_email, ['discoveryala0@gmail.com', 'pasinduwickramasooriya@gmail.com'])
                msg_admin.attach_alternative(guest_html, "text/html")
                msg_admin.send(fail_silently=True)
            except Exception as e_mail:
                print("TOUR_BOOKING_EMAIL_ERROR:", str(e_mail))

        import threading
        threading.Thread(target=_async_send_emails, daemon=True).start()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'json' in request.headers.get('accept', ''):
            return JsonResponse({
                'status': 'success',
                'guest_name': full_name,
                'guest_email': email,
                'booking_id': booking_id,
                'message': 'Reservation submitted successfully!'
            })

        return redirect(f"/tours/{slug}/")

    reviews_list = []
    try:
        reviews_list = list(GuestReview.objects.filter(rating__gte=4).exclude(comment='').order_by('-created_at')[:3])
    except Exception:
        reviews_list = []

    context = {
        'title': f"{tour.title} | Sri Lanka Tour Package",
        'tour': tour,
        'recent_tours': recent_tours,
        'highlights_list': tour.get_highlights_list(),
        'inclusions_list': tour.get_inclusions_list(),
        'exclusions_list': tour.get_exclusions_list(),
        'itinerary_list': tour.get_itinerary_list(),
        'reviews_list': reviews_list,
    }
    return render(request, 'core/tour_detail.html', context)

def contact(request):
    success_message = None
    if request.method == 'GET' and request.GET.get('success') == '1':
        name = request.GET.get('name', '').strip()
        if name:
            success_message = f"Thank you, {name}! Your safari inquiry has been received. Our Yala desk team will contact you within 15 minutes."
        else:
            success_message = "Thank you! Your safari inquiry has been received. Our Yala desk team will contact you within 15 minutes."

    if request.method == 'POST':
        user_name = request.POST.get('full_name', '').strip()
        user_email = request.POST.get('email_address', '').strip()
        user_phone = request.POST.get('phone_number', '').strip()
        user_message = request.POST.get('message', '').strip()

        # Send Email to Desk Admin & Guest Confirmation
        try:
            from django.core.mail import EmailMultiAlternatives
            from django.conf import settings
            import threading

            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Discoveryala <discoveryala0@gmail.com>')
            raw_admin = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', 'discoveryala0@gmail.com')
            if isinstance(raw_admin, str):
                admin_recipients = [e.strip() for e in raw_admin.split(',') if e.strip()]
            else:
                admin_recipients = list(raw_admin)
            if not admin_recipients:
                admin_recipients = ['discoveryala0@gmail.com']

            clean_phone = ''.join(c for c in user_phone if c.isdigit())
            if clean_phone.startswith('0'):
                clean_phone = '94' + clean_phone[1:]
            elif not clean_phone.startswith('94') and len(clean_phone) == 9:
                clean_phone = '94' + clean_phone
            wa_link = f"https://wa.me/{clean_phone}" if clean_phone else "https://wa.me/94778158004"

            def _async_send_contact_emails():
                try:
                    # 1. Admin Email (Plain Text + Rich HTML styled like about.html)
                    admin_subject = f"🔔 New Safari Contact Inquiry - {user_name}"
                    admin_body = f"""New Safari Inquiry Received via Discoveryala Contact Form:
==================================================
Guest Name: {user_name}
Email Address: {user_email}
Phone / WhatsApp: {user_phone}

Message Details:
--------------------------------------------------
{user_message}
==================================================
"""
                    admin_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head><meta charset="utf-8"></head>
                    <body style="margin: 0; padding: 32px 16px; background-color: #FAF6EE; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #233325;">
                        <div style="max-width: 580px; margin: 0 auto; background-color: #FAF6EE;">
                            <!-- Header -->
                            <div style="margin-bottom: 24px;">
                                <p style="margin: 0 0 6px 0; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: #606C38;">Discoveryala Safari Desk</p>
                                <h1 style="margin: 0; font-size: 24px; font-weight: 800; color: #283618;">New Contact Message</h1>
                            </div>

                            <!-- Details -->
                            <div style="margin-bottom: 20px;">
                                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                                    <tr>
                                        <td style="padding: 6px 0; color: #606C38; font-weight: 700; width: 35%; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px;">Guest Name</td>
                                        <td style="padding: 6px 0; color: #233325; font-weight: 700; font-size: 15px;">{user_name}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 6px 0; color: #606C38; font-weight: 700; width: 35%; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px;">Email Address</td>
                                        <td style="padding: 6px 0;"><a href="mailto:{user_email}" style="color: #475128; font-weight: 600; text-decoration: none;">{user_email}</a></td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 6px 0; color: #606C38; font-weight: 700; width: 35%; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px;">Phone / WhatsApp</td>
                                        <td style="padding: 6px 0;"><a href="{wa_link}" style="color: #475128; font-weight: 600; text-decoration: none;">{user_phone}</a></td>
                                    </tr>
                                </table>
                            </div>

                            <!-- Message Details -->
                            <div style="margin-bottom: 24px;">
                                <p style="margin: 0 0 8px 0; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #606C38;">Message Details</p>
                                <p style="margin: 0; font-size: 15px; line-height: 1.7; color: #233325; white-space: pre-wrap;">{user_message}</p>
                            </div>

                            <!-- Actions -->
                            <div style="margin: 28px 0;">
                                <a href="{wa_link}" style="display: inline-block; background-color: #475128; color: #FFFFFF; text-decoration: none; padding: 12px 24px; border-radius: 50px; font-weight: 700; font-size: 13px; margin-right: 8px;">Chat on WhatsApp</a>
                                <a href="mailto:{user_email}" style="display: inline-block; background-color: #475128; color: #FFFFFF; text-decoration: none; padding: 12px 24px; border-radius: 50px; font-weight: 700; font-size: 13px;">Reply via Email</a>
                            </div>

                            <!-- Footer -->
                            <div style="padding-top: 20px; font-size: 12px; color: #778B78; line-height: 1.6;">
                                Discoveryala Safari Desk • Yala National Park Entrance Road, Sri Lanka<br>
                                Hotline / WhatsApp: +94 77 815 8004 | Email: discoveryala0@gmail.com
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    admin_msg = EmailMultiAlternatives(admin_subject, admin_body, from_email, admin_recipients)
                    admin_msg.attach_alternative(admin_html, "text/html")
                    if user_email:
                        admin_msg.reply_to = [user_email]
                    admin_msg.send(fail_silently=True)

                    # 2. Guest Confirmation Email (Styled with main bg, borderless)
                    if user_email:
                        guest_subject = f"🐆 Safari Inquiry Received | Discoveryala Sri Lanka"
                        guest_body = f"""Ayubowan {user_name}!

Thank you for contacting Discoveryala Sri Lanka. We have received your safari inquiry.

Our senior safari desk coordinator will review your request and get back to you within 15 minutes.

Summary of Your Message:
• Name: {user_name}
• Email: {user_email}
• Phone: {user_phone}
• Message: {user_message}

Warm regards,
Discoveryala Expedition Team
Phone / WhatsApp: +94 77 815 8004
Email: discoveryala0@gmail.com
Location: Yala National Park Entrance Road, Sri Lanka
"""
                        guest_html = f"""
                        <!DOCTYPE html>
                        <html>
                        <head><meta charset="utf-8"></head>
                        <body style="margin: 0; padding: 32px 16px; background-color: #FAF6EE; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #233325;">
                            <div style="max-width: 580px; margin: 0 auto; background-color: #FAF6EE;">
                                <!-- Header -->
                                <div style="margin-bottom: 24px;">
                                    <p style="margin: 0 0 6px 0; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: #606C38;">Discoveryala Sri Lanka</p>
                                    <h1 style="margin: 0; font-size: 26px; font-weight: 800; color: #283618;">Ayubowan {user_name}!</h1>
                                    <p style="margin: 8px 0 0 0; font-size: 15px; color: #475128; line-height: 1.6;">
                                        Thank you for contacting Discoveryala. We have received your safari inquiry and our desk team will get back to you within 15 minutes.
                                    </p>
                                </div>

                                <!-- Summary -->
                                <div style="margin-bottom: 24px;">
                                    <p style="margin: 0 0 10px 0; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #606C38;">Summary of Your Request</p>
                                    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                                        <tr>
                                            <td style="padding: 6px 0; color: #606C38; font-weight: 700; width: 28%;">Name:</td>
                                            <td style="padding: 6px 0; font-weight: 600; color: #233325;">{user_name}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 6px 0; color: #606C38; font-weight: 700;">Email:</td>
                                            <td style="padding: 6px 0; color: #233325;">{user_email}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 6px 0; color: #606C38; font-weight: 700;">Phone:</td>
                                            <td style="padding: 6px 0; color: #233325;">{user_phone}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding: 6px 0; color: #606C38; font-weight: 700; vertical-align: top;">Message:</td>
                                            <td style="padding: 6px 0; color: #233325; line-height: 1.6; white-space: pre-wrap;">{user_message}</td>
                                        </tr>
                                    </table>
                                </div>

                                <!-- Response Time Note -->
                                <div style="margin-bottom: 24px;">
                                    <p style="margin: 0; font-size: 14px; color: #475128; line-height: 1.6;">
                                        Our on-site safari coordinators at Yala Entrance Road are on standby daily from 05:00 AM to 08:00 PM IST to answer inquiries and advise on optimal safari timing.
                                    </p>
                                </div>

                                <!-- WhatsApp CTA Button -->
                                <div style="margin: 28px 0;">
                                    <a href="https://wa.me/94778158004?text=Hello%20Discoveryala!%20I%20just%20submitted%20a%20contact%20inquiry%20via%20your%20website." style="display: inline-block; background-color: #475128; color: #FFFFFF; text-decoration: none; padding: 13px 28px; border-radius: 50px; font-weight: 700; font-size: 14px;">
                                        Chat on WhatsApp (+94 77 815 8004)
                                    </a>
                                </div>

                                <!-- Highlights -->
                                <p style="margin: 24px 0 16px 0; font-size: 13px; color: #606C38; font-weight: 600;">
                                    100% Private 4x4 Jeeps • Licensed Naturalist Trackers • Ethical Wildlife Viewing
                                </p>

                                <!-- Footer -->
                                <div style="padding-top: 16px; font-size: 12px; color: #778B78; line-height: 1.6;">
                                    Discoveryala Safari Team<br>
                                    Wickrama, Kasingama, Yala Entrance Road, Southern Province, Sri Lanka<br>
                                    Hotline / WhatsApp: +94 77 815 8004 | Email: discoveryala0@gmail.com
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                        guest_msg = EmailMultiAlternatives(guest_subject, guest_body, from_email, [user_email])
                        guest_msg.attach_alternative(guest_html, "text/html")
                        guest_msg.send(fail_silently=True)

                except Exception as ex:
                    print("Async contact email sending error:", ex)

            t = threading.Thread(target=_async_send_contact_emails)
            t.daemon = True
            t.start()

        except Exception as e:
            print("Contact form email dispatch error:", e)

        # AJAX support
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('is_ajax') == '1':
            return JsonResponse({
                'status': 'success',
                'message': f"Thank you, {user_name}! Your safari inquiry has been received. Our Yala desk team will contact you within 15 minutes."
            })

        # Post-Redirect-Get (PRG) pattern prevents browser reload duplicate submission
        from django.shortcuts import redirect
        from django.urls import reverse
        from urllib.parse import urlencode

        params = urlencode({
            'success': '1',
            'name': user_name
        })
        return redirect(f"{reverse('contact')}?{params}#contact-form")

    context = {
        'title': 'Contact Discoveryala | Safari Desk & Support Sri Lanka',
        'contact_info': {
            'phone': '+94 77 815 8004',
            'phone_clean': '+94778158004',
            'email': 'discoveryala0@gmail.com',
            'address': 'Wickrama, Kasingama, Yala Entrance Road, Southern Province, Sri Lanka',
            'desk_hours': 'Monday – Sunday: 05:00 AM – 08:00 PM IST',
            'gate_hours': 'Park Gate Desk: 05:30 AM – 06:00 PM IST',
            'whatsapp_url': 'https://wa.me/94778158004?text=Hello%20Yala%20Leopard%20Tracks!%20I%20would%20like%20to%20inquire%20about%20safari%20packages.'
        },
        'success_message': success_message
    }
    return render(request, 'core/contact.html', context)

def about(request):
    context = {
        'title': 'About Us | Discoveryala Eco-Expeditions Sri Lanka',
        'team_members': [
            {
                'name': 'Kapila Ratnayake',
                'role': 'Master Leopard Tracker & Lead Guide',
                'exp': '18 Years Field Experience',
                'bio': 'Born in the buffer zones of Yala, Kapila has spent 18 years mapping leopard territories across Block 1 and Block 5. His ability to decode alarm calls is unmatched.',
                'image': 'images/guaranteed-leopard.jpg'
            },
            {
                'name': 'Dr. Nimal Weerasinghe',
                'role': 'Senior Wildlife Ecologist',
                'exp': '15 Years Research Experience',
                'bio': 'Dr. Nimal oversees our Nature First policy and conducts wildlife research on sloth bear feeding corridors and elephant migration patterns.',
                'image': 'images/tailored-game-drives.jpg'
            },
            {
                'name': 'Sahan Wickramasinghe',
                'role': 'Pro Wildlife Photographer & Track Lead',
                'exp': '12 Years Field Experience',
                'bio': 'Specializing in high-end optical equipment positioning, Sahan assists wildlife photographers in capturing published shots of Yala leopards.',
                'image': 'images/bespoke-itinerary.jpg'
            }
        ],
        'pillars': [
            {
                'icon': 'fa-solid fa-seedling',
                'title': 'Nature First Policy',
                'desc': 'Strict off-road prohibition, silent electric-assist engines, zero littering, and mandatory safe distance guidelines.'
            },
            {
                'icon': 'fa-solid fa-people-roof',
                'title': 'Community Empowerment',
                'desc': '100% locally employed Southern Sri Lankan naturalist guides, trackers, and camp chefs supported by fair wages.'
            },
            {
                'icon': 'fa-solid fa-paw',
                'title': 'Leopard Territory Mapping',
                'desc': 'Decades of field tracking data mapping individual leopards in Yala Block 1 for ethical, high-probability sightings.'
            },
            {
                'icon': 'fa-solid fa-campground',
                'title': 'Eco-Luxury Glamping',
                'desc': 'Combining raw African-style tented wilderness immersion with solar power, en-suite bathrooms, and gourmet dining.'
            }
        ]
    }
    return render(request, 'core/about.html', context)

def get_all_google_reviews():
    """
    Loads verified Google Maps reviews from scripts/data/google_reviews.json,
    deduplicates with any DB GuestReview records, and sorts so that high-resolution
    photo reviews and detailed 5-star testimonials appear first.
    """
    import os
    import json
    from django.conf import settings

    json_path = os.path.join(settings.BASE_DIR, 'scripts', 'data', 'google_reviews.json')
    raw_reviews = []

    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                raw_reviews = json.load(f)
        except Exception as e:
            print("ERROR_LOADING_GOOGLE_REVIEWS_JSON:", e)
            raw_reviews = []

    reviews_list = []
    seen_keys = set()

    # 1. Include newly submitted reviews from the database (user-submitted reviews)
    try:
        from .models import GuestReview
        for r in GuestReview.objects.order_by('-created_at'):
            key = f"{r.name}_{r.comment[:40]}"
            if key not in seen_keys:
                seen_keys.add(key)
                r_rating = int(r.rating) if r.rating else 5
                reviews_list.append({
                    'id': str(r.id),
                    'name': r.name,
                    'author': r.name,
                    'origin': r.origin or 'Google Maps Verified Reviewer',
                    'package': r.package or 'Yala National Park Safari Drive',
                    'rating': r_rating,
                    'rating_stars': range(r_rating),
                    'date': r.date or 'Recent',
                    'comment': r.comment or 'Breathtaking safari experience in Yala National Park!',
                    'photo_url': r.photo_url or '',
                    'avatar_url': r.avatar_url or '',
                    'category': r.category or 'leopard',
                    'verified': r.verified,
                    'source': r.source or 'Google Maps',
                })
    except Exception:
        pass

    # 2. Include reviews from scripts/data/google_reviews.json
    for item in raw_reviews:
        author = item.get('author') or item.get('authorName') or 'Google Reviewer'
        text = (item.get('text') or item.get('reviewText') or '').strip()
        photo = (item.get('photo_url') or item.get('url') or '').strip()
        avatar = (item.get('avatar_url') or '').strip()
        rating = int(item.get('rating', 5))
        date_str = item.get('date') or item.get('relativeTime') or 'Recent'
        rid = item.get('id', '')

        key = rid if rid else f"{author}_{text[:40]}"
        if key not in seen_keys:
            seen_keys.add(key)
            lower = text.lower()
            if any(k in lower for k in ['camp', 'tent', 'glamping', 'stay', 'lodge', 'cabin', 'bungalow', 'resort']):
                cat = 'camp'
            elif any(k in lower for k in ['photo', 'camera', 'lens', 'photograph', 'capture', 'shot', 'dslr']):
                cat = 'photo'
            elif any(k in lower for k in ['leopard', 'panther', 'cub', 'cat', 'predator', 'spotted']):
                cat = 'leopard'
            else:
                cat = 'drives'

            reviews_list.append({
                'id': rid,
                'name': author,
                'author': author,
                'origin': 'Google Maps Verified Reviewer',
                'package': 'Yala National Park Safari Drive',
                'rating': rating,
                'rating_stars': range(rating),
                'date': date_str,
                'comment': text if text else 'Breathtaking wildlife encounter in Yala National Park.',
                'photo_url': photo,
                'avatar_url': avatar,
                'category': cat,
                'verified': True,
                'source': 'Google Maps',
            })

    # 3. Fallback to MongoDB if both JSON and DB were empty
    if not reviews_list:
        try:
            from .mongodb import fetch_mongo_reviews
            m_revs = fetch_mongo_reviews(limit=1000)
            for r in m_revs:
                r_rating = int(r.get('rating', 5))
                reviews_list.append({
                    'id': str(r.get('id', 1)),
                    'name': r.get('name', 'Google Reviewer'),
                    'author': r.get('name', 'Google Reviewer'),
                    'origin': r.get('origin', 'Google Maps Verified Reviewer'),
                    'package': r.get('package', 'Yala National Park Safari Drive'),
                    'rating': r_rating,
                    'rating_stars': range(r_rating),
                    'date': r.get('date', 'Recent'),
                    'comment': r.get('comment', 'Exceptional Yala wildlife safari.'),
                    'photo_url': r.get('photo_url') or r.get('photo') or '',
                    'avatar_url': r.get('avatar_url') or r.get('avatar') or '',
                    'category': r.get('category', 'leopard'),
                    'verified': True,
                    'source': 'Google Maps',
                })
        except Exception:
            pass

    # 4. Sort reviews: high-res photo reviews + detailed 5-star testimonials first
    def sort_score(r):
        has_photo = 1 if r.get('photo_url') else 0
        has_text = 1 if (r.get('comment') and len(r.get('comment')) > 20) else 0
        rating = r.get('rating', 5)
        text_len = len(r.get('comment', ''))
        return (
            has_photo * 1000 + (1 if rating >= 4 else 0) * 500 + has_text * 200 + min(text_len, 300)
        )

    reviews_list.sort(key=sort_score, reverse=True)
    return reviews_list


def reviews(request):
    review_success = None
    if request.method == 'POST':
        reviewer_name = request.POST.get('reviewer_name', 'Guest')
        reviewer_origin = request.POST.get('reviewer_origin', 'Google Reviewer')
        safari_package_used = request.POST.get('safari_package_used', 'Yala Safari Game Drive')
        star_rating_str = request.POST.get('star_rating', '5 Stars')
        review_text = request.POST.get('review_text', '')

        rating_num = 5
        if '4' in star_rating_str:
            rating_num = 4
        elif '3' in star_rating_str:
            rating_num = 3
        elif '2' in star_rating_str:
            rating_num = 2
        elif '1' in star_rating_str:
            rating_num = 1

        try:
            GuestReview.objects.create(
                category='leopard' if 'leopard' in safari_package_used.lower() else ('camp' if 'camp' in safari_package_used.lower() else 'drives'),
                name=reviewer_name,
                origin=reviewer_origin,
                date='Recent',
                package=safari_package_used,
                rating=rating_num,
                comment=review_text,
                verified=True,
                source='Google Maps'
            )
            review_success = f"Thank you, {reviewer_name}! Your Google review has been recorded and is now displayed on our page."
        except Exception as e_rev:
            print("REVIEW_SAVE_ERROR:", str(e_rev))
            review_success = f"Thank you, {reviewer_name}! Your review has been recorded."

    db_reviews = get_all_google_reviews()
    total_reviews_count = len(db_reviews)
    avg_score = "4.9"
    if total_reviews_count > 0:
        avg_num = sum(r.get('rating', 5) for r in db_reviews) / float(total_reviews_count)
        avg_score = f"{avg_num:.1f}"

    context = {
        'title': 'Google Maps Verified Reviews & Wildlife Gallery | Discoveryala',
        'rating_summary': {
            'score': avg_score,
            'stars': 5,
            'total_reviews': total_reviews_count if total_reviews_count > 0 else 1000,
            'tripadvisor_rating': '5.0 / 5.0 (Top 10% Worldwide)',
            'google_rating': f"{avg_score} / 5.0 (Google Maps Verified)"
        },
        'reviews_list': db_reviews,

        'gallery_items': [
            {
                'title': 'Yala Leopard Resting on Palu Tree',
                'category': 'leopard',
                'image': 'images/yala-leopard-card.jpg',
                'location': 'Yala Block 1',
                'credit': 'Photo by Kapila Ratnayake'
            },
            {
                'title': 'Open-Air Private 4x4 Game Viewing Jeep',
                'category': 'drives',
                'image': 'images/jeep-safari.jpg',
                'location': 'Palatupana Park Gate',
                'credit': 'Discoveryala Fleet'
            },
            {
                'title': 'Luxury Safari Glamping Suite',
                'category': 'camp',
                'image': 'images/campsite-yala.jpg',
                'location': 'Yala Buffer Wilderness',
                'credit': 'Eco-Luxury Camp'
            },
            {
                'title': 'Alfresco Kumbuk Bush Dining',
                'category': 'camp',
                'image': 'images/jungle-cuisine.jpg',
                'location': 'Manik River Bank',
                'credit': 'Wilderness Culinary Desk'
            },
            {
                'title': 'Sri Lankan Sloth Bear in Summer Palu Season',
                'category': 'photo',
                'image': 'images/yala-wildlife-hero.jpg',
                'location': 'Yala Block 5 Corridor',
                'credit': 'Photo by Sahan W.'
            },
            {
                'title': 'High-Performance 4x4 Safari Jeep',
                'category': 'drives',
                'image': 'images/hero-safari-jeep.jpg',
                'location': 'Wickrama Desk Desk',
                'credit': '4x4 Expedition Fleet'
            }
        ],
        'review_success': review_success
    }
    return render(request, 'core/reviews.html', context)

def tickets(request):

    ticket_success = None
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        country = request.POST.get('country', '').strip()
        email = request.POST.get('email_address', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        ticket_date = request.POST.get('ticket_date', '').strip()
        message = request.POST.get('message', '').strip()

        try:
            foreign_adults = int(request.POST.get('foreign_adults', 1))
            foreign_children = int(request.POST.get('foreign_children', 0))
            saarc_adults = int(request.POST.get('saarc_adults', 0))
            saarc_children = int(request.POST.get('saarc_children', 0))
            local_adults = int(request.POST.get('local_adults', 0))
            local_children = int(request.POST.get('local_children', 0))
            infants = int(request.POST.get('infants', 0))

            jeeps = int(request.POST.get('jeeps', 1))
            cars = int(request.POST.get('cars', 0))
            buses = int(request.POST.get('buses', 0))
        except (ValueError, TypeError):
            foreign_adults, foreign_children = 1, 0
            saarc_adults, saarc_children = 0, 0
            local_adults, local_children, infants = 0, 0, 0
            jeeps, cars, buses = 1, 0, 0

        try:
            entry_fees_lkr = float(request.POST.get('entry_fees_lkr', 0))
            vehicle_fees_lkr = float(request.POST.get('vehicle_fees_lkr', 0))
            service_fee_lkr = float(request.POST.get('service_fee_lkr', 0))
            subtotal_lkr = float(request.POST.get('subtotal_lkr', 0))
            vat_lkr = float(request.POST.get('vat_lkr', 0))
            gateway_fee_lkr = float(request.POST.get('gateway_fee_lkr', 0))
            total_lkr = float(request.POST.get('calculated_total_lkr', 0))
            total_usd = float(request.POST.get('calculated_total_usd', 0))
        except (ValueError, TypeError):
            entry_fees_lkr = vehicle_fees_lkr = service_fee_lkr = subtotal_lkr = vat_lkr = gateway_fee_lkr = total_lkr = total_usd = 0.0

        import time
        ref_code = f"PR-{int(time.time())}"

        def _async_send_permit_emails():
            try:
                from django.core.mail import EmailMultiAlternatives
                from django.conf import settings

                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Discoveryala <discoveryala0@gmail.com>')

                breakdown_items = ""
                if foreign_adults > 0:
                    breakdown_items += f"<tr style='border-bottom: 1px dashed #E5E5E5;'><td style='padding: 8px 12px;'>Foreign Adults ($25 USD)</td><td style='padding: 8px 12px; text-align: right;'>{foreign_adults}</td></tr>"
                if foreign_children > 0:
                    breakdown_items += f"<tr style='border-bottom: 1px dashed #E5E5E5;'><td style='padding: 8px 12px;'>Foreign Children ($15 USD)</td><td style='padding: 8px 12px; text-align: right;'>{foreign_children}</td></tr>"
                if saarc_adults > 0:
                    breakdown_items += f"<tr style='border-bottom: 1px dashed #E5E5E5;'><td style='padding: 8px 12px;'>SAARC Adults ($20 USD)</td><td style='padding: 8px 12px; text-align: right;'>{saarc_adults}</td></tr>"
                if saarc_children > 0:
                    breakdown_items += f"<tr style='border-bottom: 1px dashed #E5E5E5;'><td style='padding: 8px 12px;'>SAARC Children ($10 USD)</td><td style='padding: 8px 12px; text-align: right;'>{saarc_children}</td></tr>"
                if local_adults > 0:
                    breakdown_items += f"<tr style='border-bottom: 1px dashed #E5E5E5;'><td style='padding: 8px 12px;'>Local Adults (LKR 150)</td><td style='padding: 8px 12px; text-align: right;'>{local_adults}</td></tr>"
                if local_children > 0:
                    breakdown_items += f"<tr style='border-bottom: 1px dashed #E5E5E5;'><td style='padding: 8px 12px;'>Local Children (LKR 100)</td><td style='padding: 8px 12px; text-align: right;'>{local_children}</td></tr>"
                if infants > 0:
                    breakdown_items += f"<tr style='border-bottom: 1px dashed #E5E5E5;'><td style='padding: 8px 12px;'>Infants (Free)</td><td style='padding: 8px 12px; text-align: right;'>{infants}</td></tr>"
                if jeeps > 0:
                    breakdown_items += f"<tr style='border-bottom: 1px dashed #E5E5E5;'><td style='padding: 8px 12px;'>Safari Jeeps / Vans</td><td style='padding: 8px 12px; text-align: right;'>{jeeps}</td></tr>"
                if cars > 0:
                    breakdown_items += f"<tr style='border-bottom: 1px dashed #E5E5E5;'><td style='padding: 8px 12px;'>Cars / SUVs</td><td style='padding: 8px 12px; text-align: right;'>{cars}</td></tr>"
                if buses > 0:
                    breakdown_items += f"<tr style='border-bottom: 1px dashed #E5E5E5;'><td style='padding: 8px 12px;'>Buses / Lorries</td><td style='padding: 8px 12px; text-align: right;'>{buses}</td></tr>"

                breakdown_html = f"""
                <table style="width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 14px; color: #233325; background: #FFFFFF; border-radius: 12px; overflow: hidden; border: 1px solid rgba(96,108,56,0.2);">
                    <tr style="background: #FAF6EE; border-bottom: 1px solid rgba(96,108,56,0.2);">
                        <td style="padding: 10px 12px; font-weight: 700;">Passenger & Vehicle Items</td>
                        <td style="padding: 10px 12px; text-align: right; font-weight: 700;">Quantity</td>
                    </tr>
                    {breakdown_items}
                </table>

                <table style="width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 14px; color: #233325; background: #FFFFFF; border-radius: 12px; overflow: hidden; border: 1px solid rgba(96,108,56,0.2);">
                    <tr style="border-bottom: 1px solid #F0F0F0;"><td style="padding: 10px 14px; color: #666;">Entry Fees Subtotal</td><td style="padding: 10px 14px; text-align: right; font-weight: 600;">LKR {entry_fees_lkr:,.2f}</td></tr>
                    <tr style="border-bottom: 1px solid #F0F0F0;"><td style="padding: 10px 14px; color: #666;">Vehicle Admission Fees</td><td style="padding: 10px 14px; text-align: right; font-weight: 600;">LKR {vehicle_fees_lkr:,.2f}</td></tr>
                    <tr style="border-bottom: 1px solid #F0F0F0;"><td style="padding: 10px 14px; color: #666;">Mandatory DWC Service Fee</td><td style="padding: 10px 14px; text-align: right; font-weight: 600;">LKR {service_fee_lkr:,.2f}</td></tr>
                    <tr style="border-bottom: 1px solid #F0F0F0; font-weight: 700; background: rgba(96,108,56,0.05);"><td style="padding: 10px 14px;">Subtotal</td><td style="padding: 10px 14px; text-align: right;">LKR {subtotal_lkr:,.2f}</td></tr>
                    <tr style="border-bottom: 1px solid #F0F0F0;"><td style="padding: 10px 14px; color: #666;">Government VAT (18%)</td><td style="padding: 10px 14px; text-align: right; font-weight: 600;">LKR {vat_lkr:,.2f}</td></tr>
                    <tr style="border-bottom: 1px solid #F0F0F0;"><td style="padding: 10px 14px; color: #666;">Gateway Processing (2%)</td><td style="padding: 10px 14px; text-align: right; font-weight: 600;">LKR {gateway_fee_lkr:,.2f}</td></tr>
                    <tr style="background: #606C38; color: #FFFFFF; font-weight: 800; font-size: 16px;">
                        <td style="padding: 14px;">Total Estimated Cost</td>
                        <td style="padding: 14px; text-align: right;">LKR {total_lkr:,.2f} (~ ${total_usd:.2f} USD)</td>
                    </tr>
                </table>
                """

                guest_subject = f"Yala Park Entrance Permit Request Confirmation - Ref #{ref_code}"
                guest_text = f"Dear {full_name},\n\nThank you for requesting official Yala National Park entrance permits with Discoveryala.\n\nSafari Date: {ticket_date}\nTotal Cost: LKR {total_lkr:,.2f} (~ ${total_usd:.2f} USD)\nReference ID: #{ref_code}\n\nOur expedition desk will process your express gate voucher shortly."
                
                guest_html = f"""
                <div style="background-color: #FAF6EE; padding: 24px 12px; font-family: 'Inter', Helvetica, Arial, sans-serif;">
                    <div style="max-width: 620px; margin: 0 auto; background: #FFFFFF; border-radius: 24px; overflow: hidden; border: 1px solid rgba(71, 81, 40, 0.18);">
                        <div style="background-color: #122118; padding: 32px 24px; text-align: center; color: #FFFFFF; border-bottom: 3px solid #D4AF37;">
                            <h1 style="font-size: 22px; font-weight: 800; letter-spacing: 1px; margin: 0; color: #FAF6EE;">DISCOVERYALA</h1>
                            <p style="font-size: 13px; color: #D4AF37; margin: 6px 0 0 0; font-weight: 600; text-transform: uppercase;">Official DWC Park Entrance Permit Confirmation</p>
                        </div>
                        <div style="padding: 30px 24px; background-color: #FAF6EE;">
                            <h2 style="color: #233325; font-size: 18px; font-weight: 800; margin-top: 0;">Permit Reservation Request Received!</h2>
                            <p style="color: #4A5568; font-size: 14px; line-height: 1.6;">
                                Dear <strong>{full_name}</strong>,<br>
                                Thank you for submitting your Yala National Park entrance permit request. Below is your detailed breakdown of official DWC entrance fees, vehicle trail charges, and government taxes.
                            </p>
                            
                            <div style="background: #FFFFFF; border-radius: 16px; padding: 20px; border: 1px solid rgba(96,108,56,0.2); margin-bottom: 20px;">
                                <div style="font-size: 14px; margin-bottom: 8px;"><strong>Permit Reference:</strong> #{ref_code}</div>
                                <div style="font-size: 14px; margin-bottom: 8px;"><strong>Safari Date:</strong> {ticket_date}</div>
                                <div style="font-size: 14px; margin-bottom: 8px;"><strong>Guest Name:</strong> {full_name} ({country})</div>
                                <div style="font-size: 14px; margin-bottom: 8px;"><strong>Phone / WhatsApp:</strong> {phone_number}</div>
                                {f'<div style="font-size: 14px; margin-bottom: 8px;"><strong>Special Request:</strong> {message}</div>' if message else ''}
                            </div>

                            <h3 style="color: #233325; font-size: 16px; font-weight: 800; margin-bottom: 8px;">Detailed Tariff & Tax Breakdown</h3>
                            {breakdown_html}

                            <div style="margin-top: 24px; background: rgba(96,108,56,0.08); padding: 16px; border-radius: 12px; font-size: 13px; color: #233325; line-height: 1.6;">
                                📌 <strong>Next Steps:</strong> Our safari coordination team will review your permit request and issue your express park entry vouchers. If you have reserved safari jeep transportation with us, your driver will hold physical tickets at the Palatupana gate desk.
                            </div>
                        </div>
                        <div style="background-color: #122118; padding: 24px; text-align: center; font-size: 12px; color: #999999;">
                            <p style="margin: 0;">Discoveryala • Tissamaharama / Yala National Park, Sri Lanka</p>
                            <p style="margin: 4px 0 0 0;">Email: <a href="mailto:discoveryala0@gmail.com" style="color: #D4AF37; text-decoration: none;">discoveryala0@gmail.com</a> | WhatsApp: +94 77 815 8004</p>
                        </div>
                    </div>
                </div>
                """

                msg_guest = EmailMultiAlternatives(guest_subject, guest_text, from_email, [email])
                msg_guest.attach_alternative(guest_html, "text/html")
                msg_guest.send(fail_silently=True)

                # Send 1 Email to Admin / Our Desk to Show Bookings
                admin_subject = f"NEW TICKET PERMIT BOOKING: #{ref_code} - {full_name} ({ticket_date})"
                admin_text = f"New Park Permit Booking Request:\nRef: #{ref_code}\nName: {full_name}\nCountry: {country}\nEmail: {email}\nPhone: {phone_number}\nDate: {ticket_date}\nTotal Cost: LKR {total_lkr:,.2f} (~ ${total_usd:.2f} USD)"
                admin_recipients = ['discoveryala0@gmail.com', 'pasinduwickramasooriya@gmail.com']

                msg_admin = EmailMultiAlternatives(admin_subject, admin_text, from_email, admin_recipients)
                msg_admin.attach_alternative(guest_html, "text/html")
                msg_admin.send(fail_silently=True)

            except Exception as mail_err:
                print('TICKET_PERMIT_EMAIL_ERROR:', str(mail_err))


        import threading
        threading.Thread(target=_async_send_permit_emails, daemon=True).start()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'status': 'success',
                'message': f'Thank you, {full_name}! Your Yala park entrance permit reservation request has been submitted successfully. A confirmation email with the complete price breakdown has been sent to {email}.',
                'ref_code': ref_code
            })

        ticket_success = f"Thank you, {full_name}! Your Yala park entrance permit reservation request has been received. Express queue vouchers and price breakdown confirmation have been emailed to {email}."


    context = {
        'title': 'Yala National Park Tickets & Entrance Fees | Discoveryala',
        'ticket_rates': [
            {
                'id': 'foreign-adult',
                'title': 'Foreign Adult Ticket',
                'price_usd': '$40 USD',
                'price_lkr': 'Approx Rs. 12,800 LKR',
                'age_limit': 'Ages 12+',
                'inclusions': [
                    'National Park Entry Permit',
                    'Department of Wildlife Conservation Fee',
                    'DWC Service Tax & 15% VAT Included',
                    'Express Gate Queue-Jump Voucher'
                ],
                'popular': True
            },
            {
                'id': 'foreign-child',
                'title': 'Foreign Child Ticket',
                'price_usd': '$20 USD',
                'price_lkr': 'Approx Rs. 6,400 LKR',
                'age_limit': 'Ages 6 - 11 (Under 6 FREE)',
                'inclusions': [
                    'Child National Park Permit',
                    'All DWC Taxes & Fees Included',
                    'Free Educational Animal Chart'
                ],
                'popular': False
            },
            {
                'id': 'jeep-permit-tariff',
                'title': 'Private 4x4 Jeep Tariff',
                'price_usd': '$15 USD',
                'price_lkr': 'Approx Rs. 4,800 LKR',
                'age_limit': 'Per 4x4 Vehicle Entry',
                'inclusions': [
                    'Jeep Entrance License Fee',
                    'Park Gate Vehicle Registration',
                    'Licensed Naturalist Tracker Entry'
                ],
                'popular': True
            },
            {
                'id': 'local-resident',
                'title': 'Sri Lankan Citizen Ticket',
                'price_usd': 'Rs. 350 LKR',
                'price_lkr': 'Child: Rs. 150 LKR',
                'age_limit': 'NIC / Passport Holders',
                'inclusions': [
                    'Resident Park Entrance Ticket',
                    'DWC Conservation Tax'
                ],
                'popular': False
            }
        ],
        'gates_info': [
            {
                'name': 'Palatupana Gate (Block 1 Main Gate)',
                'hours': '06:00 AM – 06:00 PM',
                'location': 'Southern Entrance (Near Tissamaharama / Kirinda)',
                'description': 'The primary entrance for Yala Block 1 with the highest density of Sri Lankan leopards and sloth bears.'
            },
            {
                'name': 'Katagamuwa Gate (Block 1 & 2 Gate)',
                'hours': '06:00 AM – 06:00 PM',
                'location': 'Kataragama Entrance (Near Sacred City)',
                'description': 'Alternative entrance with shorter queue times, ideal for guests staying in Kataragama.'
            },
            {
                'name': 'Foreign Child Entry',
                'price': '$15 USD',
                'description': 'Department of Wildlife Conservation discounted admission for children (6 - 11 yrs)'
            },
            {
                'id': 'saarc-adult',
                'name': 'SAARC Adult Entry',
                'price': '$20 USD',
                'description': 'Special tariff for passport holders of SAARC member nations'
            },
            {
                'id': 'saarc-child',
                'name': 'SAARC Child Entry',
                'price': '$10 USD',
                'description': 'Special tariff for SAARC nation children (6 - 11 yrs)'
            },
            {
                'id': 'local-adult',
                'name': 'Sri Lankan Adult',
                'price': 'LKR 150',
                'description': 'Resident citizen entrance fee for Sri Lankan adults'
            },
            {
                'id': 'local-child',
                'name': 'Sri Lankan Child',
                'price': 'LKR 100',
                'description': 'Resident citizen entrance fee for Sri Lankan children'
            }
        ],
        'ticket_success': ticket_success
    }
    return render(request, 'core/tickets.html', context)


def bungalows(request):
    """
    Yala National Park Bungalow Bookings View:
    Showcases inside-park DWC wildlife bungalows (Mahaseelawa, Patanangala, Buthawa, Heenwewa, Ondatje, Kosgasmankada),
    expedition packages (all-inclusive with 4x4 jeep, private cook, food provisioning, tickets), guidelines, and handles booking inquiries.
    """
    booking_success = None
    if request.method == 'GET' and request.GET.get('success') == '1':
        name = request.GET.get('name', 'Valued Guest')
        email = request.GET.get('email', '')
        bungalow = request.GET.get('bungalow', 'Yala Bungalow')
        dates = request.GET.get('dates', '')
        booking_success = {
            'name': name,
            'email': email,
            'bungalow': bungalow,
            'dates': dates,
            'message': f"Thank you, {name}! Your Yala bungalow booking request for '{bungalow}' ({dates}) has been successfully received. A confirmation email has been sent to {email}."
        }

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email_address', '').strip()
        phone_code = request.POST.get('phone_code', '+94').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        country = request.POST.get('country', '').strip()
        check_in_date = request.POST.get('check_in_date', '').strip()
        check_out_date = request.POST.get('check_out_date', '').strip()

        try:
            adult_guests = int(request.POST.get('adult_guests', 2) or 2)
            child_guests = int(request.POST.get('child_guests', 0) or 0)
            infant_guests = int(request.POST.get('infant_guests', 0) or 0)
        except (ValueError, TypeError):
            adult_guests, child_guests, infant_guests = 2, 0, 0

        total_guests = adult_guests + child_guests + infant_guests
        bungalow_choice = request.POST.get('bungalow_choice', 'Best Available Bungalow').strip()
        package_type = request.POST.get('package_type', 'All-Inclusive Bungalow Safari (Jeep + Cook + Food + Permits)').strip()
        meals_provisioning = request.POST.get('meals_provisioning', 'Full-Service Chef & Grocery Provisioning').strip()
        message = request.POST.get('message', '').strip()

        # Send Email Notification to Admin & Guest Confirmation
        try:
            from django.core.mail import EmailMultiAlternatives
            from django.conf import settings
            import threading

            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Discoveryala <discoveryala0@gmail.com>')
            raw_admin = getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', 'discoveryala0@gmail.com')
            if isinstance(raw_admin, str):
                admin_recipients = [e.strip() for e in raw_admin.split(',') if e.strip()]
            else:
                admin_recipients = list(raw_admin)
            if not admin_recipients:
                admin_recipients = ['discoveryala0@gmail.com']

            full_phone = f"{phone_code} {phone_number}".strip()

            def _async_send_bungalow_emails():
                try:
                    # 1. Admin Email
                    admin_subject = f"🏡 NEW BUNGALOW INQUIRY: {bungalow_choice} - {full_name} ({check_in_date})"
                    admin_body = f"""New Yala National Park Bungalow Booking Inquiry:
==================================================
Guest Name: {full_name}
Country: {country}
Email: {email}
Phone / WhatsApp: {full_phone}

DATES & GUESTS:
Check-in Date: {check_in_date}
Check-out Date: {check_out_date}
Total Guests: {total_guests} (Adults: {adult_guests}, Children: {child_guests}, Infants: {infant_guests})

PREFERENCES & SERVICES:
Preferred Bungalow: {bungalow_choice}
Selected Package: {package_type}
Meal Provisioning: {meals_provisioning}

Special Notes / Requests:
--------------------------------------------------
{message}
==================================================
"""
                    admin_html = f"""
                    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 650px; margin: 0 auto; background: #FAF6EE; border-radius: 12px; padding: 24px; border: 1px solid #E7EBD9;">
                        <div style="background: #475128; color: #FFFFFF; padding: 18px 24px; border-radius: 8px; text-align: center;">
                            <h2 style="margin: 0; font-size: 20px; letter-spacing: 0.5px;">🏡 New Yala Park Bungalow Booking Request</h2>
                            <p style="margin: 5px 0 0 0; font-size: 13px; opacity: 0.9;">Discoveryala Expeditions • DWC In-Park Lodges</p>
                        </div>
                        <div style="background: #FFFFFF; border-radius: 8px; padding: 20px; margin-top: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                            <table style="width: 100%; border-collapse: collapse; font-size: 14px; color: #233325;">
                                <tr style="border-bottom: 1px solid #F0EAE1;"><td style="padding: 10px; font-weight: bold; width: 38%;">Guest Full Name:</td><td style="padding: 10px;">{full_name}</td></tr>
                                <tr style="border-bottom: 1px solid #F0EAE1;"><td style="padding: 10px; font-weight: bold;">Country of Origin:</td><td style="padding: 10px;">{country or 'Not Specified'}</td></tr>
                                <tr style="border-bottom: 1px solid #F0EAE1;"><td style="padding: 10px; font-weight: bold;">Email Address:</td><td style="padding: 10px;"><a href="mailto:{email}" style="color: #606C38;">{email}</a></td></tr>
                                <tr style="border-bottom: 1px solid #F0EAE1;"><td style="padding: 10px; font-weight: bold;">Phone / WhatsApp:</td><td style="padding: 10px;"><a href="https://wa.me/{phone_number.replace('+', '').replace(' ', '')}" style="color: #606C38; font-weight: bold;">{full_phone}</a></td></tr>
                                <tr style="border-bottom: 1px solid #F0EAE1;"><td style="padding: 10px; font-weight: bold;">Check-in Date:</td><td style="padding: 10px; font-weight: bold; color: #475128;">{check_in_date} (12:00 PM)</td></tr>
                                <tr style="border-bottom: 1px solid #F0EAE1;"><td style="padding: 10px; font-weight: bold;">Check-out Date:</td><td style="padding: 10px; font-weight: bold; color: #475128;">{check_out_date} (10:00 AM)</td></tr>
                                <tr style="border-bottom: 1px solid #F0EAE1;"><td style="padding: 10px; font-weight: bold;">Total Guests:</td><td style="padding: 10px;">{total_guests} (Adults: {adult_guests}, Children: {child_guests}, Infants: {infant_guests})</td></tr>
                                <tr style="border-bottom: 1px solid #F0EAE1;"><td style="padding: 10px; font-weight: bold;">Preferred Bungalow:</td><td style="padding: 10px; font-weight: bold; color: #606C38;">{bungalow_choice}</td></tr>
                                <tr style="border-bottom: 1px solid #F0EAE1;"><td style="padding: 10px; font-weight: bold;">Service Package:</td><td style="padding: 10px;">{package_type}</td></tr>
                                <tr style="border-bottom: 1px solid #F0EAE1;"><td style="padding: 10px; font-weight: bold;">Meal Provisioning:</td><td style="padding: 10px;">{meals_provisioning}</td></tr>
                                <tr><td style="padding: 10px; font-weight: bold; vertical-align: top;">Special Requests:</td><td style="padding: 10px; line-height: 1.6;">{message or 'None specified'}</td></tr>
                            </table>
                        </div>
                    </div>
                    """
                    admin_msg = EmailMultiAlternatives(admin_subject, admin_body, from_email, admin_recipients)
                    admin_msg.attach_alternative(admin_html, "text/html")
                    if email:
                        admin_msg.reply_to = [email]
                    admin_msg.send(fail_silently=True)

                    # 2. Guest Confirmation Email
                    if email:
                        guest_subject = f"🌿 Yala Bungalow Booking Inquiry Received | Discoveryala"
                        guest_body = f"""Ayubowan {full_name}!

Thank you for your inquiry for a Yala National Park Bungalow Stay with Discoveryala Sri Lanka.

We have received your reservation request for "{bungalow_choice}".

BOOKING INQUIRY SUMMARY:
• Check-in: {check_in_date} (Check-in 12:00 PM)
• Check-out: {check_out_date} (Check-out 10:00 AM)
• Guests: {total_guests} (Adults: {adult_guests}, Children: {child_guests})
• Preferred Bungalow: {bungalow_choice}
• Package: {package_type}
• Provisions: {meals_provisioning}
• Special Requests / Notes: {message or 'None specified'}

WHAT HAPPENS NEXT:
1. Availability Verification: Our senior DWC wildlife desk coordinator is checking current official permit availability for your requested dates.
2. Custom Quotation: We will send you a complete breakdown including DWC bungalow tariff, private 4x4 safari jeep, chef/cook coordination, and entrance fees.
3. Fast Contact: A naturalist coordinator will reach out to you via WhatsApp / Email within 15-30 minutes.

If you have urgent questions, connect directly with our 24/7 Safari Desk:
WhatsApp / Hotline: +94 77 815 8004
Email: discoveryala0@gmail.com
Location: Palatupana Gate Road, Yala National Park, Sri Lanka

Warm wildlife regards,
The Discoveryala Safari Team
"""
                        guest_html = f"""
                        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 650px; margin: 0 auto; background: #FAF6EE; border-radius: 12px; padding: 24px; border: 1px solid #E7EBD9;">
                            <div style="background: #475128; color: #FFFFFF; padding: 20px; border-radius: 8px; text-align: center;">
                                <h2 style="margin: 0; font-size: 22px;">🌿 Yala Bungalow Stay Request Received</h2>
                                <p style="margin: 6px 0 0 0; font-size: 14px; opacity: 0.9;">Discoveryala Eco-Expeditions Sri Lanka</p>
                            </div>
                            <div style="background: #FFFFFF; border-radius: 8px; padding: 22px; margin-top: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); color: #233325; font-size: 14px; line-height: 1.7;">
                                <p style="font-size: 16px; font-weight: bold; margin-top: 0;">Ayubowan {full_name},</p>
                                <p>Thank you for choosing Discoveryala for your inside-park wilderness stay in <strong>Yala National Park</strong>. We have logged your request for <strong>{bungalow_choice}</strong>.</p>
                                
                                <div style="background: #FAF6EE; border-left: 4px solid #606C38; padding: 14px; border-radius: 4px; margin: 16px 0;">
                                    <h4 style="margin: 0 0 8px 0; color: #475128;">📋 Request Overview:</h4>
                                    <p style="margin: 2px 0;"><strong>Dates:</strong> {check_in_date} to {check_out_date}</p>
                                    <p style="margin: 2px 0;"><strong>Bungalow:</strong> {bungalow_choice}</p>
                                    <p style="margin: 2px 0;"><strong>Guests:</strong> {total_guests} ({adult_guests} Adults, {child_guests} Children)</p>
                                    <p style="margin: 2px 0;"><strong>Package:</strong> {package_type}</p>
                                    <p style="margin: 2px 0;"><strong>Special Notes / Requests:</strong> {message or 'None specified'}</p>
                                </div>

                                <h4 style="color: #475128; margin-top: 18px;">✨ Next Steps:</h4>
                                <p>Our senior wildlife desk coordinator is checking real-time DWC permit availability and will send your detailed itinerary & pricing quote within <strong>15–30 minutes</strong>.</p>
                                
                                <div style="text-align: center; margin: 24px 0;">
                                    <a href="https://wa.me/94778158004?text=Hello%20Discoveryala!%20I%20just%20submitted%20a%20bungalow%20request%20for%20{check_in_date}" style="background: #25D366; color: #FFFFFF; text-decoration: none; padding: 12px 24px; border-radius: 30px; font-weight: bold; display: inline-block; font-size: 14px;">
                                        💬 Chat on WhatsApp with Desk (+94 77 815 8004)
                                    </a>
                                </div>

                                <hr style="border: 0; border-top: 1px solid #E7EBD9; margin: 20px 0;">
                                <p style="font-size: 12px; color: #778B78; margin-bottom: 0;">
                                    Discoveryala Safari Team • Palatupana Gate Road, Tissamaharama, Sri Lanka<br>
                                    Hotline / WhatsApp: +94 77 815 8004 | Email: discoveryala0@gmail.com
                                </p>
                            </div>
                        </div>
                        """
                        guest_msg = EmailMultiAlternatives(guest_subject, guest_body, from_email, [email])
                        guest_msg.attach_alternative(guest_html, "text/html")
                        guest_msg.send(fail_silently=True)

                except Exception as ex:
                    print("Async bungalow email sending error:", ex)

            t = threading.Thread(target=_async_send_bungalow_emails)
            t.daemon = True
            t.start()

        except Exception as e:
            print("Bungalow inquiry error:", e)

        booking_success = {
            'name': full_name,
            'email': email,
            'bungalow': bungalow_choice,
            'dates': f"{check_in_date} – {check_out_date}",
            'package': package_type,
            'message': f"Thank you, {full_name}! Your Yala bungalow booking request for '{bungalow_choice}' ({check_in_date}) has been successfully submitted. We have sent a confirmation email copy to {email}. Our senior safari desk coordinator will contact you via WhatsApp / Phone within 15–30 minutes."
        }

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('is_ajax') == '1':
            return JsonResponse({'status': 'success', 'data': booking_success})

        # Post-Redirect-Get (PRG) fallback for standard non-AJAX POST to prevent browser reload duplicate submission
        from django.shortcuts import redirect
        from django.urls import reverse
        from urllib.parse import urlencode
        params = urlencode({
            'success': '1',
            'name': full_name,
            'email': email,
            'bungalow': bungalow_choice,
            'dates': f"{check_in_date} – {check_out_date}"
        })
        return redirect(f"{reverse('bungalows')}?{params}#bookingFormSection")

    bungalows_data = [
        {
            'id': 'mahaseelawa',
            'name': 'Mahaseelawa Bungalow',
            'block': 'Block 1 (Palatupana Access)',
            'tag': 'Coastal Lagoon & Leopard Territory',
            'badge_color': 'bg-amber-100 text-amber-900 border-amber-300',
            'capacity': '10 Guests',
            'bedrooms': '2 Large Bedrooms (5 beds each)',
            'bathrooms': '2 Attached Bathrooms',
            'power': 'Solar Night Lighting & Fan System',
            'water': 'Fresh Tube-Well Supply',
            'view': 'Mahaseelawa Lagoon & Sand Dunes',
            'image': 'https://res.cloudinary.com/dkfnpmzpv/image/upload/v1784456381/blogs/jqbr6khinkvptii7ax0c.jpg',
            'key_sightings': 'High-density leopard territory, mugger crocodiles on lagoon banks, spotted deer herds, migratory waterbirds, white-bellied sea eagles',
            'description': 'Nestled directly between the serene Mahaseelawa lagoon and the wild southern coastline, Mahaseelawa is widely celebrated as one of the most productive wildlife locations in all of Sri Lanka. Elephants and leopards frequently drink from the lagoon shores directly in front of the veranda at dawn and dusk.',
            'features': ['Dedicated DWC Caretaker & Safari Cook', 'Dining Veranda with Lagoon View', 'Private Coastal Sand Dunes', 'Direct Game Track Access'],
            'highlights': ['Premier spot for early morning leopard sightings', 'Tranquil evening lagoon ambience', 'Scenic coastal breeze and privacy']
        },
        {
            'id': 'patanangala',
            'name': 'Patanangala Bungalow',
            'block': 'Block 1 (Palatupana Access)',
            'tag': 'Coastal Rock Outcrop & Ocean Breeze',
            'badge_color': 'bg-emerald-100 text-emerald-900 border-emerald-300',
            'capacity': '10 Guests',
            'bedrooms': '2 Spacious Bedrooms + Linen',
            'bathrooms': '2 Attached Modern Bathrooms',
            'power': 'Solar Lighting + Generator Backup',
            'water': 'Fresh Water Tank System',
            'view': 'Patanangala Beach, Rocks & Open Plains',
            'image': 'https://res.cloudinary.com/dkfnpmzpv/image/upload/v1779352393/blogs/lww3k1nql9xpouch1ap6.jpg',
            'key_sightings': 'Leopards stalking rock outcrops at dusk, wild boars, sambar deer, raptors, sea birds and occasional sloth bears',
            'description': 'Perched adjacent to the iconic Patanangala rock on Yala\'s coastal perimeter, this bungalow combines refreshing Indian Ocean breezes with unmatched wildlife vantage points. Watch leopards scout the plains from nearby granite boulders just minutes from your front porch.',
            'features': ['Panoramic Coastal & Rock Views', 'Caretaker & Cook On-Site', 'Spacious Veranda & Dining Table', 'Historic Ocean Viewpoint'],
            'highlights': ['Direct access to coastal wildlife game tracks', 'Natural sea breeze ventilation', 'Spectacular sunrise and sunset vistas']
        },
        {
            'id': 'buthawa',
            'name': 'New Buthawa Bungalow',
            'block': 'Block 1 (Central Game Area)',
            'tag': 'Panoramic Plains & Freshwater Tank',
            'badge_color': 'bg-blue-100 text-blue-900 border-blue-300',
            'capacity': '10 Guests',
            'bedrooms': '2 Double Bedrooms + Linen',
            'bathrooms': '2 Attached Washrooms',
            'power': 'Solar Energy System with Device Charging',
            'water': 'Continuous Clean Water Storage',
            'view': 'Buthawa Plain & Coastal Scrubland',
            'image': 'https://res.cloudinary.com/dkfnpmzpv/image/upload/v1786355872/blogs/amvi8vrath9rtjzrk01m.jpg',
            'key_sightings': 'Elephants feeding across scrubland, leopards crossing open grasslands, sloth bears in seasonal fruit trees, water buffaloes',
            'description': 'One of the most famous and historical bungalows in Sri Lanka\'s wildlife lore. Expertly rebuilt with modern comforts while retaining classic safari architecture, New Buthawa overlooks expansive grasslands where massive herds gather to feed and drink.',
            'features': ['Elevated Wildlife Viewing Platform', 'Dedicated DWC Kitchen Staff', 'Prime Central Block 1 Location', 'Excellent Night Ambience'],
            'highlights': ['Unobstructed 180° views across plains', 'Frequent elephant herds around bungalow', 'Central access to all Block 1 safari tracks']
        },
        {
            'id': 'heenwewa',
            'name': 'Heenwewa Bungalow',
            'block': 'Block 1 (Interior Lake Zone)',
            'tag': 'Freshwater Lake & Elephant Bathing Haven',
            'badge_color': 'bg-teal-100 text-teal-900 border-teal-300',
            'capacity': '10 Guests',
            'bedrooms': '2 Air-Cooled Bedrooms (5 beds each)',
            'bathrooms': '2 Attached Washrooms',
            'power': 'Eco Solar Night Lighting',
            'water': 'Fresh Borewell Supply',
            'view': 'Direct Waterfront View of Heenwewa Reservoir',
            'image': 'https://res.cloudinary.com/dkfnpmzpv/image/upload/v1781080452/blogs/ju0ukvrwuyvbfwpeinb0.jpg',
            'key_sightings': 'Continuous elephant bathing and drinking activity, grey-headed fish eagles, painted storks, spotted deer, marsh crocodiles',
            'description': 'Situated right on the edge of the ancient Heenwewa reservoir, this bungalow is an absolute paradise for birdwatchers and elephant lovers. Witness wild elephants cooling off in the lake just meters away from your morning tea veranda.',
            'features': ['Direct Lakefront Viewing Terrace', 'In-House Cook Available', 'Unmatched Birdlife Photography', 'Serene Forest Canopy Surroundings'],
            'highlights': ['Elephants drinking right in front of the deck', 'Over 100 bird species recorded on lake', 'Completely serene forest ambiance']
        },
        {
            'id': 'ondatje',
            'name': 'Ondatje / Yala Bungalow',
            'block': 'Block 1 (Menik River Bank)',
            'tag': 'Ancient Kumbuk Riverine Canopy',
            'badge_color': 'bg-amber-100 text-amber-900 border-amber-300',
            'capacity': '10 Guests',
            'bedrooms': '2 Forest Rooms + Attached Bathrooms',
            'power': 'Solar Night Lighting',
            'water': 'Running Fresh Water',
            'view': 'Menik Riverbed & Lush Riverine Forest',
            'image': 'https://res.cloudinary.com/dkfnpmzpv/image/upload/v1777690831/blogs/ituwsxwpjiy93mlmmctx.jpg',
            'key_sightings': 'Elephants crossing Menik river, Tufted Grey Langurs, fish owls, leopards resting in giant Kumbuk branches, axis deer',
            'description': 'Shaded by towering Kumbuk trees along the sacred Menik River, Ondatje Bungalow provides natural cooling and deep forest tranquility. Experience the timeless rhythm of river wildlife coming down to drink throughout the heat of the day.',
            'features': ['Lush Riverside Shaded Deck', 'Natural Tree Canopy Cooling', 'DWC Cook & Helper Support', 'True Wilderness Solitude'],
            'highlights': ['Cool microclimate beneath huge Kumbuk trees', 'River crossings right beside bungalow', 'Rich birdlife and monkey troops']
        },
        {
            'id': 'kosgasmankada',
            'name': 'Kosgasmankada & Thalgasmankada',
            'block': 'Block 2 (Deep Wilderness / River Crossing)',
            'tag': 'Untamed Raw Jungle & Ultimate Seclusion',
            'badge_color': 'bg-purple-100 text-purple-900 border-purple-300',
            'capacity': '10 Guests',
            'bedrooms': 'Rustic Wilderness Rooms + Facilities',
            'power': 'Solar Emergency Lighting',
            'water': 'Fresh Natural Supply',
            'view': 'Block 2 Riverbank & Dense Pristine Jungles',
            'image': 'https://res.cloudinary.com/dkfnpmzpv/image/upload/v1784715720/blogs/ijydonzyl3r272lpluln.jpg',
            'key_sightings': 'Solitary bull elephants, leopard breeding pairs, sloth bears, rare forest raptors, untouched wildlife',
            'description': 'For true adventurers seeking the rawest wilderness experience in Sri Lanka. Located in Block 2 across the Menik River, accessible only via modified 4x4 river crossing. Absolute serenity with zero tourist crowds.',
            'features': ['4x4 River Crossing Entry', 'Ultimate Wildlife Seclusion', 'Dedicated Jungle Tracker & Cook', 'Zero Commercial Disturbance'],
            'highlights': ['Zero tourist jeep congestion', 'Deepest immersion in untouched wild', 'Unforgettable 4x4 river crossing adventure']
        }
    ]

    faqs_list = [
        {
            'q': 'How does staying in an inside-park Yala bungalow work?',
            'a': 'DWC wildlife bungalows are located deep inside the protected boundaries of Yala National Park. When you stay in a park bungalow, you enter through the official park gate (check-in at 12:00 PM) and remain inside the park overnight after all regular daytime safari jeeps leave at 6:00 PM. You have full private access to dawn and dusk wildlife movements right from your veranda.'
        },
        {
            'q': 'What is the early morning safari advantage of staying inside Yala National Park?',
            'a': 'Because you are already situated deep inside the park, you do not have to wait in the long 5:30 AM gate queues at Palatupana or Katagamuwa. Your private 4x4 safari jeep can start tracking fresh leopard tracks at first light (5:45 AM) across undisturbed game trails, hours before day-tripper jeeps reach the interior.'
        },
        {
            'q': 'Which Yala bungalow is best for leopard sightings?',
            'a': 'Mahaseelawa and Patanangala bungalows are historically celebrated as the premier locations for leopard sightings due to their proximity to coastal lagoons, sand dunes, and granite rock outcrops. New Buthawa is also exceptional for open-plains leopard and sloth bear sightings.'
        },
        {
            'q': 'Which Yala bungalow is best for elephants and birdwatching?',
            'a': 'Heenwewa Bungalow sits directly on the edge of the ancient Heenwewa reservoir, making it the top choice for witnessing wild elephant herds bathing at sunrise and sunset, alongside over 100 wetland bird species. Ondatje Bungalow is ideal for viewing elephants drinking along the Menik River.'
        },
        {
            'q': 'How are meals and food provisioning handled at the bungalow?',
            'a': 'Every DWC bungalow has a dedicated in-house caretaker and safari cook. The cook prepares delicious traditional Sri Lankan dishes, barbecue, and safari breakfast packs. With Discoveryala\'s All-Inclusive Expedition package, our team handles all fresh groceries, meats, vegetables, spices, and drinking water. Alternatively, guests can bring their own dry and fresh provisions for the cook to prepare.'
        },
        {
            'q': 'What is the booking window for Yala DWC bungalows?',
            'a': 'The Department of Wildlife Conservation (DWC) allows bungalow bookings up to 90 days in advance. Because there are only a handful of inside-park bungalows and global demand is exceptionally high (especially for peak wildlife months from December to July and weekends), we strongly recommend submitting your reservation inquiry as early as possible.'
        },
        {
            'q': 'What are the official DWC check-in, check-out, and gate curfew times?',
            'a': 'Official DWC check-in is at 12:00 PM (noon) on your arrival date, and check-out is strictly at 10:00 AM on your departure date. Park entrance gates close strictly at 6:00 PM, meaning all arriving guests must clear the park gate before 6:00 PM.'
        },
        {
            'q': 'Do I need a private 4x4 safari jeep while staying in the bungalow?',
            'a': 'Yes! A 4x4 safari vehicle is legally required for park entry, gate transfers, and safari game drives throughout your stay. Discoveryala provides customized modified 4x4 safari jeeps with experienced trackers on standby for morning, evening, and full-day game drives.'
        },
        {
            'q': 'What is the difference between Block 1 and Block 2 Yala bungalows?',
            'a': 'Block 1 bungalows (Mahaseelawa, Patanangala, New Buthawa, Heenwewa, Ondatje) have easy access via Palatupana and high leopard density. Block 2 bungalows (Kosgasmankada & Thalgasmankada) require an adventurous 4x4 river crossing across the Menik River and offer total untouched wilderness with zero commercial tourist crowds.'
        },
        {
            'q': 'Is it safe to stay inside Yala National Park with children?',
            'a': 'Yes, staying in an inside-park bungalow is an unforgettable family adventure. All bungalows are fenced with elephant protection trenches or electric fences. However, guests must strictly follow wildlife safety rules: never step outside the bungalow clearing after dark, keep doors closed, and listen to the park tracker\'s instructions at all times.'
        },
        {
            'q': 'What amenities and electricity are available in the bungalows?',
            'a': 'Bungalows are equipped with solar-powered lighting, ceiling/table fans, clean beds with fresh linen, running water, and attached flush toilets and showers. Some bungalows offer generator backup for charging cameras and mobile phones. Wi-Fi is intentionally not provided to preserve the authentic off-grid wilderness immersion.'
        },
        {
            'q': 'Can Discoveryala arrange airport pickups and islandwide transfers to Yala?',
            'a': 'Yes! We provide private luxury air-conditioned vehicle transfers from Colombo Bandaranaike International Airport (CMB), Mattala Airport (HRI), Galle, Ella, Mirissa, Tangalle, and Kandy directly to the Yala National Park entrance gate.'
        }
    ]

    context = {
        'title': 'Yala National Park Bungalow Bookings | DWC Wilderness Safari Lodges Sri Lanka',
        'bungalows': bungalows_data,
        'faqs': faqs_list,
        'booking_success': booking_success,
        'contact_info': {
            'phone': '+94 77 815 8004',
            'phone_clean': '+94778158004',
            'email': 'discoveryala0@gmail.com',
            'address': 'Palatupana Gate Road, Yala National Park, Sri Lanka',
            'whatsapp_url': 'https://wa.me/94778158004?text=Hello%20Discoveryala!%20I%20would%20like%20to%20inquire%20about%20Yala%20National%20Park%20Bungalow%20Bookings.'
        }
    }
    return render(request, 'core/bungalows.html', context)


def policies(request):
    """
    Legal Policies View: Consolidates Privacy Policy, Terms of Service, and Refund Policy.
    """
    context = {
        'title': 'Privacy Policy, Terms of Service & Refund Policy | Discoveryala',
    }
    return render(request, 'core/policies.html', context)


def api_get_reviews(request):
    """
    Public JSON API to fetch Google Maps verified reviews dynamically.
    Returns 5-star ratings, author photos, relative time descriptions & full text.
    """
    try:
        from core.models import Review
        reviews = Review.objects.filter(is_published=True).order_by('-created_at')
        review_data = []
        for r in reviews:
            review_data.append({
                'id': r.id,
                'author_name': r.author_name,
                'author_photo_url': r.get_photo_url(),
                'rating': r.rating,
                'relative_time_description': r.relative_time,
                'text': r.text,
                'google_maps_url': r.google_maps_url,
                'verified': r.verified,
                'created_at': r.created_at.strftime("%Y-%m-%d")
            })
        return JsonResponse({'status': 'success', 'reviews': review_data})
    except Exception as e:
        # Fallback to static reviews structure if DB query fails
        return JsonResponse({
            'status': 'fallback',
            'publisher': {
                'name': 'Discoveryala'
            }
        })


def robots_txt(request):
    """
    Returns production-grade robots.txt for Googlebot, Bingbot, Applebot,
    and legitimate AI search crawlers (GPTBot, OAI-SearchBot, ChatGPT-User, PerplexityBot, ClaudeBot, Google-Extended).
    """
    from django.http import HttpResponse
    domain = f"{request.scheme}://{request.get_host()}"
    content = f"""# ==============================================================================
# Discoveryala.com - Search Engine & AI Search Agent Directives
# ==============================================================================
User-agent: Googlebot
Allow: /
Disallow: /admin/
Disallow: /book/
Disallow: /*?*
Disallow: /api/

User-agent: Googlebot-Image
Allow: /static/images/
Allow: /media/
Allow: /

User-agent: Bingbot
Allow: /
Disallow: /admin/
Disallow: /book/
Disallow: /*?*

User-agent: Applebot
Allow: /
Disallow: /admin/
Disallow: /book/
Disallow: /*?*

User-agent: Applebot-Extended
Allow: /
Disallow: /admin/
Disallow: /book/
Disallow: /*?*

User-agent: DuckDuckBot
Allow: /
Disallow: /admin/
Disallow: /book/
Disallow: /*?*

# Legitimate AI Answer Engines & Search Agents
User-agent: GPTBot
Allow: /
Disallow: /admin/
Disallow: /book/
Disallow: /*?*
Disallow: /api/

User-agent: OAI-SearchBot
Allow: /
Disallow: /admin/
Disallow: /book/
Disallow: /*?*
Disallow: /api/

User-agent: ChatGPT-User
Allow: /
Disallow: /admin/
Disallow: /book/
Disallow: /*?*

User-agent: PerplexityBot
Allow: /
Disallow: /admin/
Disallow: /book/
Disallow: /*?*
Disallow: /api/

User-agent: ClaudeBot
Allow: /
Disallow: /admin/
Disallow: /book/
Disallow: /*?*
Disallow: /api/

User-agent: anthropic-ai
Allow: /
Disallow: /admin/
Disallow: /book/
Disallow: /*?*

User-agent: Google-Extended
Allow: /
Disallow: /admin/
Disallow: /book/
Disallow: /*?*

User-agent: Meta-ExternalAgent
Allow: /
Disallow: /admin/
Disallow: /book/
Disallow: /*?*

User-agent: cohere-ai
Allow: /
Disallow: /admin/
Disallow: /book/
Disallow: /*?*

# Resource-Draining Commercial Bots & Non-Search Scrapers (Blocked to prevent serverless exhaustion)
User-agent: Bytespider
Disallow: /

User-agent: PetalBot
Disallow: /

User-agent: SemrushBot
Disallow: /

User-agent: SemrushBot-SA
Disallow: /

User-agent: AhrefsBot
Disallow: /

User-agent: MJ12bot
Disallow: /

User-agent: DotBot
Disallow: /

User-agent: DataForSeoBot
Disallow: /

User-agent: Amazonbot
Disallow: /

User-agent: Seekport
Disallow: /

User-agent: BLEXBot
Disallow: /

User-agent: *
Allow: /
Disallow: /admin/
Disallow: /book/
Disallow: /*?*
Disallow: /api/
Crawl-delay: 5

# Canonical Dynamic XML Sitemaps & AI Manifests
Sitemap: {domain}/sitemap.xml

# LLM Context Files (https://llmstxt.org/)
# Canonical LLM Summary: {domain}/llms.txt
# Canonical LLM Full Knowledgebase: {domain}/llms-full.txt
"""
    response = HttpResponse(content.strip() + "\n", content_type="text/plain")
    response['Cache-Control'] = 'public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800'
    response['CDN-Cache-Control'] = 'public, s-maxage=86400, stale-while-revalidate=604800'
    response['Vercel-CDN-Cache-Control'] = 'public, s-maxage=86400, stale-while-revalidate=604800'
    return response


def llms_txt(request):
    """
    Returns standardized /llms.txt markdown for AI search engines & LLMs
    (ChatGPT, Gemini, Claude, Perplexity) per the https://llmstxt.org standard.
    """
    from django.http import HttpResponse
    domain = f"{request.scheme}://{request.get_host()}"
    
    content = f"""# Discoveryala - Yala Safaris, Islandwide Transfers & Wildlife Tours

> Discoveryala (Yala Leopard Tracks) is the premier, highly-rated wildlife safari operator and private transfer provider based directly at Yala National Park, Sri Lanka. Specializing in ethical 4x4 leopard tracking game drives (Block 1 & Block 5), customized islandwide chauffeur transfers, and official DWC national park bungalow bookings.

## Core Capabilities & Services

- **Yala Safari Game Drives**: Private and shared 4x4 jeep safaris with expert English-speaking naturalists and spotters. Morning (5:30 AM - 10:00 AM), Evening (2:30 PM - 6:30 PM), and 12-Hour Full-Day expeditions.
- **Islandwide Transport & Chauffeur Service**: Private door-to-door air-conditioned transfers between Yala/Tissamaharama and Colombo Airport (CMB), Ella, Mirissa, Weligama, Galle Fort, Kandy, and Arugam Bay. Luggage safely secured in vehicles during safaris.
- **Official DWC Park Entrance Tickets**: Seamless ticket issuing for foreign tourists (~$46 USD Adult, ~$20 USD Child 6-16, Under 6 Free) eliminating morning ticket counter lines.
- **DWC Park Bungalow Stays**: Official inside-the-park bungalow reservations (Mahaseelawa, Patanangala, New Buthawa, Heenwewa) with dedicated chef and game tracker.
- **Nearby Sanctuary Safaris**: Bundala National Park (premier wetland & birding hotspot) and Lunugamvehera National Park (elephant corridor).

## Essential Navigation Links

- [Safari Packages]({domain}/packages/): Private half-day and full-day game drive pricing, inclusions, and instant booking.
- [Multi-Day Tours & Transfers]({domain}/tours/): Islandwide private chauffeur-driven itineraries and intercity transfers.
- [DWC Park Entrance Fees]({domain}/tickets/): 2026 official ticket price breakdown and entrance fee calculator for foreigners.
- [Yala Park Bungalows]({domain}/yala-bungalows/): Reservations for historical in-park wildlife lodges.
- [Wildlife Journal & Sighting Guides]({domain}/blog/): Field notes, monthly leopard sighting data, and travel route guides.
- [Customer Reviews]({domain}/reviews/): Verified traveler reviews, TripAdvisor recommendations, and Google ratings.
- [About Discoveryala]({domain}/about/): Our fleet of custom safari jeeps, ethical wildlife code, and expert trackers.
- [Contact Safari Desk]({domain}/contact/): Direct 24/7 inquiry and custom itinerary requests.

## Direct Contact & Booking

- **WhatsApp / Phone (24/7)**: [+94 77 815 8004](https://wa.me/94778158004)
- **Email**: [discoveryala0@gmail.com](mailto:discoveryala0@gmail.com)
- **Base Location**: Palatupana Gate Road, Kasingama, Tissamaharama 82000, Southern Province, Sri Lanka
- **Full AI Knowledgebase**: [{domain}/llms-full.txt]({domain}/llms-full.txt)
"""
    response = HttpResponse(content.strip() + "\n", content_type="text/markdown; charset=utf-8")
    response['Cache-Control'] = 'public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800'
    response['CDN-Cache-Control'] = 'public, s-maxage=86400, stale-while-revalidate=604800'
    response['Vercel-CDN-Cache-Control'] = 'public, s-maxage=86400, stale-while-revalidate=604800'
    return response


def llms_full_txt(request):
    """
    Returns comprehensive /llms-full.txt markdown providing detailed context,
    pricing, live database packages, transport route logistics, and FAQs
    for AI retrieval-augmented generation (RAG) and search synthesis.
    """
    from django.http import HttpResponse
    domain = f"{request.scheme}://{request.get_host()}"
    
    # Query live database packages
    packages_text = []
    try:
        for pkg in SafariPackage.objects.all():
            inc_list = ", ".join(pkg.get_inclusions_list()[:5]) or "Private 4x4 Jeep, Expert Driver/Tracker, Park Permits"
            pkg_url = f"{domain}/packages/{pkg.slug}/" if pkg.slug else f"{domain}/packages/"
            packages_text.append(f"""### {pkg.title}
- **Category**: {pkg.category_label}
- **Duration**: {pkg.duration}
- **Price**: {pkg.price} ({pkg.price_unit})
- **Vehicle**: {pkg.vehicle}
- **Includes Entrance Tickets**: {'Yes' if pkg.includes_tickets else 'Optional add-on available ($46 Adult / $20 Child)'}
- **Key Inclusions**: {inc_list}
- **Booking URL**: [{pkg.title}]({pkg_url})
""")
    except Exception:
        pass
    packages_md = "\n".join(packages_text) if packages_text else "Check website for current seasonal rates."

    # Query live database multi-day tours
    tours_text = []
    try:
        for tr in Tour.objects.all():
            tour_url = f"{domain}/tours/{tr.slug}/" if tr.slug else f"{domain}/tours/"
            tours_text.append(f"""### {tr.title}
- **Route**: {tr.route or 'Colombo → Cultural Triangle → Ella → Yala → South Coast'}
- **Duration**: {tr.duration}
- **Price**: From ${tr.get_clean_price()} USD per person
- **Highlights**: {tr.description or 'Custom wildlife & scenic chauffeur journey'}
- **Booking URL**: [{tr.title}]({tour_url})
""")
    except Exception:
        pass
    tours_md = "\n".join(tours_text) if tours_text else "Custom multi-day tours available on inquiry."

    content = f"""# Complete Knowledgebase: Discoveryala - Yala Safaris & Sri Lanka Private Transport

> Authoritative reference for Large Language Models (ChatGPT, Google Gemini, Claude, Perplexity) regarding Yala National Park safaris, wildlife logistics, entrance fees, transport routes, and private transfers in Sri Lanka.

---

## 1. Company Profile & Entity Summary

- **Brand Name**: Discoveryala (also known as Yala Leopard Tracks)
- **Business Type**: Certified Sri Lanka Wildlife Tour Operator & Chauffeur Service
- **Headquarters**: Palatupana Gate Road, Kasingama, Tissamaharama 82000, Southern Province, Sri Lanka
- **Operating Regions**: Yala National Park (Block 1 Palatupana Gate, Block 5 Katagamuwa Gate), Bundala National Park, Udawalawe National Park, Lunugamvehera National Park, and Islandwide Private Transfers.
- **Customer Rating**: 4.9/5 based on verified international traveler reviews from the UK, USA, Germany, Australia, and France.
- **Direct WhatsApp Hotline (24/7 Fast Booking)**: +94 77 815 8004
- **Email**: discoveryala0@gmail.com
- **Official Website**: {domain}/

---

## 2. Complete Islandwide Transport & Private Transfer Guide

Discoveryala provides dedicated private door-to-door transfers across all major Sri Lankan travel hubs with experienced English-speaking drivers, air-conditioned vehicles, expressway toll passes, and safe luggage storage.

| Route | Distance | Travel Time | Recommended Route / Highway | Vehicle Options |
| :--- | :--- | :--- | :--- | :--- |
| **Colombo Airport (CMB) / Negombo ⇄ Yala** | ~290 km | 4 – 4.5 Hours | Southern Expressway (E01/E02 to Mattala exit) | Private AC Sedan / KDH Luxury Van |
| **Colombo City ⇄ Yala** | ~270 km | 4 Hours | Southern Expressway (E01/E02) | Private AC Sedan / KDH Luxury Van |
| **Ella ⇄ Yala / Tissamaharama** | ~95 km | 2 Hours | Ella-Wellawaya Rd (A23) via Ravana Falls & Wellawaya | Private AC Car / Minivan / Tuk-Tuk |
| **Mirissa / Weligama ⇄ Yala** | ~145 km | 2 – 2.5 Hours | Southern Coastal Expressway (E01) | Private AC Sedan / Van |
| **Galle Fort ⇄ Yala** | ~170 km | 2.5 – 3 Hours | Southern Expressway (E01) | Private AC Sedan / Van |
| **Tangalle / Hiriketiya ⇄ Yala** | ~80 km | 1.25 – 1.5 Hours | A2 Coastal Highway | Private AC Sedan / Van |
| **Kandy ⇄ Yala** | ~210 km | 5.5 – 6 Hours | Via Nuwara Eliya & Ella OR Randenigala scenic route | Private AC Sedan / Luxury Van |
| **Nuwara Eliya ⇄ Yala** | ~150 km | 4 Hours | Via Welimada, Ella, and Wellawaya | Private AC Sedan / Van |
| **Arugam Bay ⇄ Yala** | ~140 km | 3 Hours | Via Sella Kataragama / Buttala route | Private AC Car / 4x4 / Van |

### The "Ella to South Coast via Yala Safari" Transfer Service
A popular signature service for international backpackers and luxury travelers alike:
1. Morning pickup from your hotel in Ella (06:00 AM or 11:30 AM).
2. Scenic drive to Yala / Tissamaharama with luggage safely stored in the private air-conditioned vehicle.
3. Complete an afternoon Yala Safari Game Drive (02:30 PM - 06:30 PM) in a custom 4x4 jeep.
4. Evening drop-off directly at your beach hotel in Mirissa, Weligama, Galle, or Tangalle.

---

## 3. Safari Packages & Pricing Overview

Discoveryala operates modified Toyota Hilux and Land Cruiser safari jeeps equipped with stadium tiered seating, safety roll bars, canvas rain protection, charging ports, and beanbags for telephoto camera stabilization.

{packages_md}

### Safari Timing Options
- **Morning Safari (05:30 AM – 10:00 AM)**: Recommended for highest leopard sighting probability and active predator movement at dawn before heat sets in. Jeeps line up at Palatupana or Katagamuwa gate at 05:30 AM to enter when gates open at 06:00 AM.
- **Afternoon Safari (02:30 PM – 06:30 PM)**: Best for Asian elephants bathing in lagoons, sloth bears feeding on palu/weera trees, and golden hour photography.
- **Full-Day Safari (05:30 AM – 06:30 PM)**: 12-hour comprehensive exploration covering deep wilderness sectors (Block 1 and Block 2 perimeter). Midday rest break taken at Patanangala ocean beach or designated river rest sites inside the park.

---

## 4. Official Yala National Park Entrance Ticket Fees (2026 DWC Rates)

Entrance permits are legally issued by the Department of Wildlife Conservation (DWC) Sri Lanka:
- **Foreign Adult (16+ years)**: ~$46 USD per person (inclusive of standard entry permit, DWC tracker fee, vehicle entry permit, and government VAT).
- **Foreign Child (6–16 years)**: ~$20 USD per child.
- **Children Under 6 years**: FREE entry.
- **Advance Ticket Purchase**: Discoveryala provides pre-arranged digital QR entrance tickets, allowing guests to bypass the crowded physical ticket queues at Palatupana gate and enter the park immediately upon opening.

---

## 5. DWC In-Park Wildlife Bungalow Stays

Exclusive overnight accommodation inside Yala National Park managed by DWC with Discoveryala's logistics and catering support:
- **Mahaseelawa Bungalow**: Located beside Mahaseelawa lagoon; prime leopard and crocodile territory (Up to 10 guests).
- **Patanangala Bungalow**: Coastal rock outpost with ocean breezes and sunset views (Up to 10 guests).
- **New Buthawa Bungalow**: Overlooking the central Buthawa plains and waterhole; exceptional elephant watching (Up to 10 guests).
- **Heenwewa Bungalow**: Interior forest lake setting ideal for peaceful bird watching and elephant bathing (Up to 10 guests).
- **Inclusions**: DWC resident caretaker and cook, solar electricity with charging stations, freshwater, bed linen, and direct sunrise game track departures before regular day-tourists arrive.

---

## 6. Multi-Day Sri Lanka Tours

{tours_md}

---

## 7. Frequently Asked Questions (FAQ) for AI Search Retrieval

### Q1: What is the best month to visit Yala National Park?
**Answer**: Yala is accessible year-round. February to July is considered the peak season for leopard and sloth bear sightings as waterholes dry up, concentrating wildlife around open lagoons. The park is vibrant and green from November to January with migratory bird arrivals. Note: Block 1 typically undergoes a standard seasonal rest maintenance in September/October, during which Block 5, Lunugamvehera, and Bundala remain open with excellent sightings.

### Q2: How can I book a safari with Discoveryala?
**Answer**: Travelers can reserve directly via WhatsApp at **+94 77 815 8004** for immediate confirmation, or book online at **{domain}/packages/**. Same-day and next-day bookings are accepted subject to jeep availability.

### Q3: Do we need cash for the park entrance?
**Answer**: When booking an all-inclusive safari package with Discoveryala, park entrance tickets are pre-arranged and included in the price. If booking a jeep-only drive, tickets can be added to your booking invoice or purchased at the gate.

### Q4: Can we travel directly from Ella to Yala for a safari and then go to Mirissa on the same day?
**Answer**: Yes, Discoveryala specializes in the Ella ➔ Yala Safari ➔ Mirissa/Galle transfer route. Your luggage is locked safely inside our transport vehicle while you enjoy the safari, and our driver takes you directly to your beach resort in the evening.

### Q5: What animals can be seen in Yala National Park?
**Answer**: Yala is home to the Sri Lankan "Big Three": the Sri Lankan Leopard (*Panthera pardus kotiya*), the Asian Elephant (*Elephas maximus maximus*), and the Sloth Bear (*Melursus ursinus inornatus*). Other common wildlife includes spotted deer, sambar deer, mugger crocodiles, water buffalo, wild boars, jackals, monitor lizards, and over 215 bird species.

---

## 8. Official Contact & Booking Details

- **Company**: Discoveryala (Yala Leopard Tracks)
- **Primary WhatsApp / Phone**: +94 77 815 8004
- **Email**: discoveryala0@gmail.com
- **Website**: {domain}
- **Address**: Palatupana Gate Road, Kasingama, Tissamaharama 82000, Sri Lanka
"""
    response = HttpResponse(content.strip() + "\n", content_type="text/markdown; charset=utf-8")
    response['Cache-Control'] = 'public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800'
    response['CDN-Cache-Control'] = 'public, s-maxage=86400, stale-while-revalidate=604800'
    response['Vercel-CDN-Cache-Control'] = 'public, s-maxage=86400, stale-while-revalidate=604800'
    return response



def site_webmanifest(request):
    """
    Returns site.webmanifest for PWA & Google Search logo indexing.
    """
    from django.http import JsonResponse
    data = {
        "name": "Discoveryala - Yala Safaris Sri Lanka",
        "short_name": "Discoveryala",
        "start_url": "/",
        "icons": [
            {
                "src": f"{request.scheme}://{request.get_host()}/static/images/favicon.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": f"{request.scheme}://{request.get_host()}/static/images/logo-official.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ],
        "theme_color": "#606C38",
        "background_color": "#FAF6EE",
        "display": "standalone"
    }
    response = JsonResponse(data)
    response['Cache-Control'] = 'public, max-age=86400, s-maxage=604800, stale-while-revalidate=2592000'
    response['CDN-Cache-Control'] = 'public, s-maxage=604800, stale-while-revalidate=2592000'
    response['Vercel-CDN-Cache-Control'] = 'public, s-maxage=604800, stale-while-revalidate=2592000'
    return response


def sitemap_xml(request):
    """
    Dynamically generates sitemap.xml with Google Image Sitemap schema (xmlns:image)
    listing all static pillar pages, dynamic safari packages, multi-day tours, and wildlife journals.
    """
    from django.http import HttpResponse
    from django.urls import reverse
    from xml.sax.saxutils import escape
    from datetime import datetime

    domain = f"{request.scheme}://{request.get_host()}"
    today_str = datetime.utcnow().strftime('%Y-%m-%d')
    
    # 1. Core Static Pillar Pages with Image Metadata
    static_urls = [
        {
            'loc': domain + '/',
            'changefreq': 'daily',
            'priority': '1.0',
            'lastmod': today_str,
            'image': 'https://res.cloudinary.com/dkfnpmzpv/image/upload/v1784094600/hero_sections/kgazrufqbqrk6mumlbsm.jpg',
            'image_title': 'Yala National Park Safari Game Drives & Luxury Glamping Sri Lanka'
        },
        {
            'loc': domain + reverse('packages'),
            'changefreq': 'daily',
            'priority': '0.95',
            'lastmod': today_str,
            'image': 'https://res.cloudinary.com/dkfnpmzpv/image/upload/v1786355872/blogs/amvi8vrath9rtjzrk01m.jpg',
            'image_title': 'Yala Safari Packages & Private 4x4 Safari Jeep Game Drives'
        },
        {
            'loc': domain + reverse('tickets'),
            'changefreq': 'weekly',
            'priority': '0.90',
            'lastmod': today_str,
            'image': 'https://res.cloudinary.com/dkfnpmzpv/image/upload/v1786355872/blogs/amvi8vrath9rtjzrk01m.jpg',
            'image_title': 'Yala National Park Entrance Fees & DWC Official Ticket Prices'
        },
        {
            'loc': domain + reverse('bungalows'),
            'changefreq': 'daily',
            'priority': '0.92',
            'lastmod': today_str,
            'image': 'https://res.cloudinary.com/dkfnpmzpv/image/upload/v1784456381/blogs/jqbr6khinkvptii7ax0c.jpg',
            'image_title': 'Yala National Park Bungalow Bookings & DWC In-Park Wildlife Lodges'
        },
        {
            'loc': domain + reverse('tours'),
            'changefreq': 'daily',
            'priority': '0.90',
            'lastmod': today_str,
            'image': 'https://res.cloudinary.com/dkfnpmzpv/image/upload/v1780047686/tours/yltrwtcjetsweu307nhc.jpg',
            'image_title': 'Sri Lanka Multi-Day Wildlife Tours & Private Chauffeur Transport'
        },
        {
            'loc': domain + reverse('blog'),
            'changefreq': 'daily',
            'priority': '0.85',
            'lastmod': today_str,
            'image': 'https://res.cloudinary.com/dkfnpmzpv/image/upload/v1784094600/hero_sections/kgazrufqbqrk6mumlbsm.jpg',
            'image_title': 'Yala Wildlife Journal & Field Sighting Guides'
        },
        {
            'loc': domain + reverse('reviews'),
            'changefreq': 'weekly',
            'priority': '0.80',
            'lastmod': today_str,
            'image': 'https://res.cloudinary.com/dkfnpmzpv/image/upload/v1784094600/hero_sections/kgazrufqbqrk6mumlbsm.jpg',
            'image_title': 'Verified Google Maps Reviews & Safari Gallery Discoveryala'
        },
        {
            'loc': domain + reverse('about'),
            'changefreq': 'monthly',
            'priority': '0.75',
            'lastmod': today_str,
            'image': 'https://res.cloudinary.com/dkfnpmzpv/image/upload/v1784094600/hero_sections/kgazrufqbqrk6mumlbsm.jpg',
            'image_title': 'About Discoveryala Senior Naturalists & Eco-Expeditions Desk'
        },
        {
            'loc': domain + reverse('contact'),
            'changefreq': 'monthly',
            'priority': '0.75',
            'lastmod': today_str,
            'image': 'https://res.cloudinary.com/dkfnpmzpv/image/upload/v1784094600/hero_sections/kgazrufqbqrk6mumlbsm.jpg',
            'image_title': 'Contact Discoveryala 24/7 Safari Desk'
        },
        {
            'loc': domain + reverse('policies'),
            'changefreq': 'monthly',
            'priority': '0.50',
            'lastmod': today_str,
            'image': '',
            'image_title': ''
        },
        {
            'loc': domain + '/llms.txt',
            'changefreq': 'weekly',
            'priority': '0.80',
            'lastmod': today_str,
            'image': '',
            'image_title': ''
        },
    ]

    xml_entries = []
    for item in static_urls:
        img_xml = ""
        if item.get('image'):
            img_xml = f"""
    <image:image>
      <image:loc>{escape(item['image'])}</image:loc>
      <image:title>{escape(item['image_title'])}</image:title>
    </image:image>"""
        xml_entries.append(f"""  <url>
    <loc>{escape(item['loc'])}</loc>
    <lastmod>{item['lastmod']}</lastmod>
    <changefreq>{item['changefreq']}</changefreq>
    <priority>{item['priority']}</priority>{img_xml}
  </url>""")

    # 2. Dynamic Safari Packages with Cloudinary Image Extensions
    try:
        for pkg in SafariPackage.objects.all():
            if pkg.slug:
                try:
                    url = f"{domain}{reverse('package_detail', kwargs={'slug': pkg.slug})}"
                    lastmod = pkg.updated_at.strftime('%Y-%m-%d') if getattr(pkg, 'updated_at', None) else today_str
                    img_url = pkg.imageUrl or (pkg.image_file.url if pkg.image_file else '')
                    img_tag = ""
                    if img_url:
                        if not img_url.startswith('http'):
                            img_url = f"{domain}{img_url}"
                        img_tag = f"""
    <image:image>
      <image:loc>{escape(img_url)}</image:loc>
      <image:title>{escape(pkg.title)}</image:title>
    </image:image>"""
                    xml_entries.append(f"""  <url>
    <loc>{escape(url)}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.90</priority>{img_tag}
  </url>""")
                except Exception:
                    pass
    except Exception:
        pass

    # 3. Dynamic Multi-Day Tours with Image Extensions
    try:
        for tr in Tour.objects.all():
            if tr.slug:
                try:
                    url = f"{domain}{reverse('tour_detail', kwargs={'slug': tr.slug})}"
                    lastmod = tr.updated_at.strftime('%Y-%m-%d') if getattr(tr, 'updated_at', None) else today_str
                    img_url = tr.get_tour_image_url()
                    img_tag = ""
                    if img_url:
                        if not img_url.startswith('http'):
                            img_url = f"{domain}{img_url}"
                        img_tag = f"""
    <image:image>
      <image:loc>{escape(img_url)}</image:loc>
      <image:title>{escape(tr.title)}</image:title>
    </image:image>"""
                    xml_entries.append(f"""  <url>
    <loc>{escape(url)}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.90</priority>{img_tag}
  </url>""")
                except Exception:
                    pass
    except Exception:
        pass

    # 4. Dynamic Wildlife Blog Posts with Image Extensions
    try:
        for post in BlogPost.objects.all():
            if post.slug:
                try:
                    url = f"{domain}{reverse('blog_detail', kwargs={'slug': post.slug})}"
                    lastmod = post.updated_at.strftime('%Y-%m-%d') if getattr(post, 'updated_at', None) else (post.created_at.strftime('%Y-%m-%d') if getattr(post, 'created_at', None) else today_str)
                    img_url = post.imageUrl or (post.image_file.url if post.image_file else '')
                    img_tag = ""
                    if img_url:
                        if not img_url.startswith('http'):
                            img_url = f"{domain}{img_url}"
                        img_tag = f"""
    <image:image>
      <image:loc>{escape(img_url)}</image:loc>
      <image:title>{escape(post.title)}</image:title>
    </image:image>"""
                    xml_entries.append(f"""  <url>
    <loc>{escape(url)}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.85</priority>{img_tag}
  </url>""")
                except Exception:
                    pass
    except Exception:
        pass

    joined_entries = "\n".join(xml_entries)
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
{joined_entries}
</urlset>"""

    response = HttpResponse(xml_content, content_type="application/xml")
    response['Cache-Control'] = 'public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800'
    response['CDN-Cache-Control'] = 'public, s-maxage=86400, stale-while-revalidate=604800'
    response['Vercel-CDN-Cache-Control'] = 'public, s-maxage=86400, stale-while-revalidate=604800'
    return response














