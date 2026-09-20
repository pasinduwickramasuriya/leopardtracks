from django.db import models

def optimize_cloudinary_url(url, width=None):
    if not url or not isinstance(url, str):
        return url
    url = url.strip()
    if 'res.cloudinary.com' not in url or '/image/upload/' not in url:
        return url
    if 'f_auto' in url or 'q_auto' in url:
        return url
    transform = f"f_auto,q_auto,w_{width}/" if width else "f_auto,q_auto/"
    return url.replace('/image/upload/', f'/image/upload/{transform}')


class SafariPackage(models.Model):
    CATEGORY_CHOICES = [
        ('half-day', 'Half-Day Game Drive'),
        ('full-day', 'Full-Day Expedition'),
        ('luxury-camp', 'Luxury Tented Camp Package'),
        ('photography', 'Photography Special'),
        ('shared-safari', 'Shared Safari Tour'),
    ]

    PRICE_TYPE_CHOICES = [
        ('jeep_only', 'Jeep-Only Private Drive (Add-ons Optional)'),
        ('per_person', 'Per-Person All-Inclusive (Shared / Glamping)'),
    ]

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True, default='')
    slug = models.CharField(max_length=200, blank=True, default='', help_text="URL friendly slug identifier e.g. bundala-tour-7-hours")
    
    # Dual Image Options: Local File Upload or Cloudinary URL link
    image_file = models.ImageField(upload_to='packages/', blank=True, null=True, help_text="Upload image file from local device (auto-uploads to Cloudinary if configured) OR paste direct URL in Image URL field below")
    imageUrl = models.CharField(max_length=500, blank=True, default='', help_text="Primary Cloudinary or image URL (Auto-filled when uploading local image file)")
    image_urls = models.TextField(blank=True, null=True, default='', help_text="Additional image URLs / Cloudinary URLs for gallery (Separate multiple URLs with newlines)")
    
    description = models.TextField(blank=True, default='', help_text="Detailed description of the safari package experience")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='half-day')
    category_label = models.CharField(max_length=100, default='HALF-DAY GAME DRIVE')
    tag_class = models.CharField(max_length=50, default='tag-sage')
    
    # Pricing Structure & Add-on Controls
    price_type = models.CharField(max_length=30, choices=PRICE_TYPE_CHOICES, default='jeep_only')
    price = models.CharField(max_length=50, default='$120', help_text="Primary price string shown on card (e.g. $62.99 or $49)")
    price_unit = models.CharField(max_length=100, default='per 4x4 jeep (up to 6 guests)')
    
    mealPrice = models.CharField(max_length=50, default='0', blank=True, help_text="Meal price e.g. 10 or 0")
    ticketPrice = models.CharField(max_length=50, default='0', blank=True, help_text="Adult ticket price e.g. 46 or 30")
    childTicketPrice = models.CharField(max_length=50, default='20', blank=True, help_text="Child ticket price (age 6-16) e.g. 20 or 10")
    
    # Optional Add-on Toggles & Pricing
    includes_tickets = models.BooleanField(default=False, help_text="Check if Yala entrance tickets are included in base price")
    ticket_addon_price = models.CharField(max_length=100, blank=True, default='$46 Adult (16+) | $20 Child (6-16) | Under 6 Free')
    
    includes_breakfast = models.BooleanField(default=False, help_text="Check if breakfast is included in base price")
    breakfast_addon_price = models.CharField(max_length=100, blank=True, default='+$10 USD / Person (Optional Add-on)')
    
    duration = models.CharField(max_length=100, default='5 Hours (05:30 AM – 10:30 AM)')
    vehicle = models.CharField(max_length=200, default='Private 4x4 Safari Jeep')
    
    inclusions = models.TextField(blank=True, default='', help_text="Items included (Separate with newlines)")
    exclusions = models.TextField(blank=True, default='', help_text="Items NOT included (Separate with newlines e.g. Park Tickets, Tips)")
    highlights = models.TextField(blank=True, default='', help_text="Key safari attraction points (Separate with newlines)")
    
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            from django.utils.text import slugify
            self.slug = slugify(self.title)

        # Handle local device file upload -> Cloudinary or local media storage
        if self.image_file and not getattr(self.image_file, '_committed', True):
            try:
                from django.conf import settings
                cloud_name = getattr(settings, 'CLOUDINARY_CLOUD_NAME', '')
                cloud_url = getattr(settings, 'CLOUDINARY_URL', '')

                if cloud_name or cloud_url:
                    import cloudinary.uploader
                    if hasattr(self.image_file, 'seek'):
                        self.image_file.seek(0)
                    res = cloudinary.uploader.upload(self.image_file, folder="leopardtracks/packages")
                    if res and 'secure_url' in res:
                        self.imageUrl = res['secure_url']
                        self.image_file._committed = True
                elif hasattr(self.image_file, 'url'):
                    self.imageUrl = self.image_file.url
            except Exception:
                if hasattr(self.image_file, 'url'):
                    try:
                        self.imageUrl = self.image_file.url
                    except Exception:
                        pass

        try:
            super().save(*args, **kwargs)
        except OSError:
            if self.image_file:
                self.image_file._committed = True
            super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_inclusions_list(self):
        if not self.inclusions:
            return []
        return [inc.strip() for inc in self.inclusions.split('\n') if inc.strip()]

    def get_exclusions_list(self):
        if not self.exclusions:
            return []
        return [exc.strip() for exc in self.exclusions.split('\n') if exc.strip()]

    def get_highlights_list(self):
        if not self.highlights:
            return []
        return [hl.strip() for hl in self.highlights.split('\n') if hl.strip()]

    def get_clean_price(self):
        if not self.price:
            return "120"
        p = str(self.price).strip().replace('$', '').replace('USD', '').replace('usd', '').strip()
        return p if p else "120"

    def get_image_urls_list(self):
        urls = []
        if self.imageUrl:
            urls.append(self.imageUrl.strip())
        if self.image_urls:
            extra = [u.strip() for u in self.image_urls.split('\n') if u.strip()]
            for e in extra:
                if e not in urls:
                    urls.append(e)
        return urls


class SafariBooking(models.Model):
    package_title = models.CharField(max_length=200)
    full_name = models.CharField(max_length=200)
    country = models.CharField(max_length=100, blank=True, default='')
    email = models.EmailField()
    phone_code = models.CharField(max_length=10, default='+94')
    phone_number = models.CharField(max_length=50, blank=True, default='')
    
    safari_date = models.DateField()
    guests = models.IntegerField(default=2)
    adult_guests = models.IntegerField(default=2)
    child_guests = models.IntegerField(default=0, help_text="Age 6-16 ($20 USD)")
    under6_guests = models.IntegerField(default=0, help_text="Under 6 (FREE)")
    
    include_meals = models.BooleanField(default=False)
    meal_count = models.IntegerField(default=0)
    meals_price_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    include_tickets = models.BooleanField(default=False)
    tickets_price_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    message = models.TextField(blank=True, default='')
    status = models.CharField(max_length=30, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.package_title} ({self.safari_date})"


class BlogPost(models.Model):
    title = models.CharField(max_length=250)
    slug = models.CharField(max_length=250, blank=True, default='', help_text="URL slug identifier e.g. Yala-National-Park-The-Wildlife-Paradise-of-Sri-Lanka")
    category = models.CharField(max_length=100, default='WILDLIFE LOG')
    author = models.CharField(max_length=100, default='Discoveryala Naturalist')
    
    # Dual Image: Local Device File Upload or Cloudinary URL link
    image_file = models.ImageField(upload_to='blogs/', blank=True, null=True, help_text="Upload image file from local device (auto-uploads to Cloudinary) OR paste Cloudinary URL below")
    imageUrl = models.CharField(max_length=500, blank=True, default='', help_text="Cloudinary or image URL")
    
    content = models.TextField(blank=True, default='', help_text="Full blog post story & article content")
    featured = models.BooleanField(default=False, help_text="Check if this blog post should be highlighted as Featured Hero story")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            from django.utils.text import slugify
            self.slug = slugify(self.title)

        # Handle local device file upload -> Cloudinary or local media storage
        if self.image_file and not getattr(self.image_file, '_committed', True):
            try:
                from django.conf import settings
                cloud_name = getattr(settings, 'CLOUDINARY_CLOUD_NAME', '')
                cloud_url = getattr(settings, 'CLOUDINARY_URL', '')

                if cloud_name or cloud_url:
                    import cloudinary.uploader
                    if hasattr(self.image_file, 'seek'):
                        self.image_file.seek(0)
                    res = cloudinary.uploader.upload(self.image_file, folder="leopardtracks/blogs")
                    if res and 'secure_url' in res:
                        self.imageUrl = res['secure_url']
                        self.image_file._committed = True
                elif hasattr(self.image_file, 'url'):
                    self.imageUrl = self.image_file.url
            except Exception:
                if hasattr(self.image_file, 'url'):
                    try:
                        self.imageUrl = self.image_file.url
                    except Exception:
                        pass

        try:
            super().save(*args, **kwargs)
        except OSError:
            if self.image_file:
                self.image_file._committed = True
            super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_paragraphs(self):
        if not self.content:
            return []
        parts = [p.strip() for p in self.content.replace('\r\n', '\n').split('\n\n') if p.strip()]
        return parts


class HeroSection(models.Model):
    title = models.CharField(max_length=200, default="WILD YALA SAFARIS", help_text="Main Hero Title e.g. WILD YALA SAFARIS")
    subtitle = models.CharField(max_length=300, default="Ceylon's premier 4x4 game drives & luxury glamping.", help_text="Hero Subtitle / Description")
    badge_text = models.CharField(max_length=100, default="🌿 YALA LEOPARD TRACKS", blank=True, help_text="Pill Badge Tag text e.g. 🌿 YALA LEOPARD TRACKS")
    
    # Hero Background Image Options (Local Device Upload or Cloudinary URL)
    image_file = models.ImageField(upload_to='hero/', blank=True, null=True, help_text="Upload hero image file from local device (auto-uploads to Cloudinary if configured) OR paste direct URL below")
    imageUrl = models.CharField(max_length=500, blank=True, default="https://res.cloudinary.com/dkfnpmzpv/image/upload/v1786355872/blogs/amvi8vrath9rtjzrk01m.jpg", help_text="Hero background image Cloudinary or static URL")
    
    # CTA Buttons
    button_primary_text = models.CharField(max_length=100, default="EXPLORE PACKAGES")
    button_primary_url = models.CharField(max_length=200, default="/packages/")
    
    button_secondary_text = models.CharField(max_length=100, default="BOOK SAFARI")
    button_secondary_url = models.CharField(max_length=200, default="/contact/")
    
    is_active = models.BooleanField(default=True, help_text="Check if this Hero Section configuration is active on the homepage")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Hero Section'
        verbose_name_plural = 'Hero Sections'

    def save(self, *args, **kwargs):
        # Handle local device file upload -> Cloudinary or local media storage
        if self.image_file and not getattr(self.image_file, '_committed', True):
            try:
                from django.conf import settings
                cloud_name = getattr(settings, 'CLOUDINARY_CLOUD_NAME', '')
                cloud_url = getattr(settings, 'CLOUDINARY_URL', '')

                if cloud_name or cloud_url:
                    import cloudinary.uploader
                    if hasattr(self.image_file, 'seek'):
                        self.image_file.seek(0)
                    res = cloudinary.uploader.upload(self.image_file, folder="leopardtracks/hero")
                    if res and 'secure_url' in res:
                        self.imageUrl = res['secure_url']
                        self.image_file._committed = True
                elif hasattr(self.image_file, 'url'):
                    self.imageUrl = self.image_file.url
            except Exception:
                if hasattr(self.image_file, 'url'):
                    try:
                        self.imageUrl = self.image_file.url
                    except Exception:
                        pass

        try:
            super().save(*args, **kwargs)
        except OSError:
            if self.image_file:
                self.image_file._committed = True
            super().save(*args, **kwargs)

    def get_hero_image_url(self):
        url = ""
        if self.imageUrl and self.imageUrl.strip():
            url = self.imageUrl.strip()
        elif self.image_file:
            try:
                url = self.image_file.url
            except Exception:
                pass
        if not url:
            url = "https://res.cloudinary.com/dkfnpmzpv/image/upload/v1784094600/hero_sections/kgazrufqbqrk6mumlbsm.jpg"
        return optimize_cloudinary_url(url, 1200)

    def get_hero_image_mobile_url(self):
        url = ""
        if self.imageUrl and self.imageUrl.strip():
            url = self.imageUrl.strip()
        elif self.image_file:
            try:
                url = self.image_file.url
            except Exception:
                pass
        if not url:
            url = "https://res.cloudinary.com/dkfnpmzpv/image/upload/v1784094600/hero_sections/kgazrufqbqrk6mumlbsm.jpg"
        return optimize_cloudinary_url(url, 640)

    def __str__(self):
        return f"{self.title} ({'Active' if self.is_active else 'Inactive'})"


class Tour(models.Model):
    title = models.CharField(max_length=250)
    slug = models.CharField(max_length=250, blank=True, default='', help_text="URL friendly slug identifier e.g. 5-day-sri-lanka-escape")
    route = models.CharField(max_length=500, blank=True, default='', help_text="Tour route overview e.g. Colombo → Sigiriya → Kandy → Ella → Colombo")
    price = models.CharField(max_length=50, default="280", help_text="Tour price string e.g. 280 or $280")
    duration = models.CharField(max_length=100, default="5 Days / 4 Nights", help_text="Tour duration e.g. 5 Days / 4 Nights")
    
    # Tour Cover Image Options (Local Device Upload or Cloudinary URL)
    image_file = models.ImageField(upload_to='tours/', blank=True, null=True, help_text="Upload tour image file from local device")
    imageUrl = models.CharField(max_length=500, blank=True, default='', help_text="Cloudinary or direct image URL")
    
    isFeatured = models.BooleanField(default=False, help_text="Check if this tour should be highlighted on the tours page")
    description = models.TextField(blank=True, default='', help_text="Short description overview")
    longDescription = models.TextField(blank=True, default='', help_text="Detailed journey overview story")
    
    highlights = models.TextField(blank=True, default='', help_text="Key highlights (Separate multiple points with newlines)")
    inclusions = models.TextField(blank=True, default='', help_text="Service inclusions (Separate multiple points with newlines)")
    exclusions = models.TextField(blank=True, default='', help_text="Service exclusions (Separate multiple points with newlines)")
    seoKeywords = models.TextField(blank=True, default='', help_text="SEO keywords separated by commas")
    
    # Store day-by-day itinerary formatted as JSON
    itinerary_json = models.TextField(blank=True, default='', help_text="JSON string array of day-by-day itinerary items")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Tour Package'
        verbose_name_plural = 'Tour Packages'

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            from django.utils.text import slugify
            self.slug = slugify(self.title)

        # Handle local device file upload -> Cloudinary or local media storage
        if self.image_file and not getattr(self.image_file, '_committed', True):
            try:
                from django.conf import settings
                cloud_name = getattr(settings, 'CLOUDINARY_CLOUD_NAME', '')
                cloud_url = getattr(settings, 'CLOUDINARY_URL', '')

                if cloud_name or cloud_url:
                    import cloudinary.uploader
                    if hasattr(self.image_file, 'seek'):
                        self.image_file.seek(0)
                    res = cloudinary.uploader.upload(self.image_file, folder="leopardtracks/tours")
                    if res and 'secure_url' in res:
                        self.imageUrl = res['secure_url']
                        self.image_file._committed = True
                elif hasattr(self.image_file, 'url'):
                    self.imageUrl = self.image_file.url
            except Exception:
                if hasattr(self.image_file, 'url'):
                    try:
                        self.imageUrl = self.image_file.url
                    except Exception:
                        pass

        try:
            super().save(*args, **kwargs)
        except OSError:
            if self.image_file:
                self.image_file._committed = True
            super().save(*args, **kwargs)

    def get_tour_image_url(self):
        url = ""
        if self.imageUrl and self.imageUrl.strip():
            url = self.imageUrl.strip()
        elif self.image_file:
            try:
                url = self.image_file.url
            except Exception:
                pass
        if not url:
            url = "https://res.cloudinary.com/dkfnpmzpv/image/upload/v1780047686/tours/yltrwtcjetsweu307nhc.jpg"
        return optimize_cloudinary_url(url, 800)

    def get_highlights_list(self):
        if not self.highlights:
            return []
        return [h.strip() for h in self.highlights.split('\n') if h.strip()]

    def get_inclusions_list(self):
        if not self.inclusions:
            return []
        return [inc.strip() for inc in self.inclusions.split('\n') if inc.strip()]

    def get_exclusions_list(self):
        if not self.exclusions:
            return []
        return [exc.strip() for exc in self.exclusions.split('\n') if exc.strip()]

    def get_itinerary_list(self):
        if not self.itinerary_json:
            return []
        import json
        try:
            return json.loads(self.itinerary_json)
        except Exception:
            return []

    def get_clean_price(self):
        if not self.price:
            return "280"
        p = str(self.price).strip().replace('$', '').replace('USD', '').replace('usd', '').strip()
        return p if p else "280"

    def __str__(self):
        return self.title


class GuestReview(models.Model):
    category = models.CharField(max_length=50, default='leopard', choices=[
        ('leopard', 'Leopard Sightings'),
        ('drives', 'Game Drives'),
        ('camp', 'Luxury Camp Stays'),
        ('photo', 'Wildlife Photography'),
    ])
    name = models.CharField(max_length=150)
    origin = models.CharField(max_length=150, default='London, UK')
    date = models.CharField(max_length=50, default='August 2026')
    package = models.CharField(max_length=200, default='Yala Block 1 Morning Leopard Game Drive')
    rating = models.IntegerField(default=5)
    comment = models.TextField(blank=True, default='')
    verified = models.BooleanField(default=True)
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    photo_url = models.URLField(max_length=500, blank=True, null=True)
    source = models.CharField(max_length=50, default='Google Maps')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Guest Review'
        verbose_name_plural = 'Guest Reviews'

    def __str__(self):
        return f"{self.name} - {self.package} ({self.rating} Stars)"
