from urllib.parse import quote_plus

from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Category, Product


CATALOG_VERSION_KEY = 'products:catalog:version'
MISSING_PRODUCT_SENTINEL = '__missing_product__'
CATEGORY_ICON_MAP = {
    'medicines': 'fa-pills',
    'vitamins': 'fa-apple-alt',
    'diabetes': 'fa-tint',
    'devices': 'fa-heartbeat',
    'ayurveda': 'fa-leaf',
    'baby-care': 'fa-baby-carriage',
}


def _cache_timeout(setting_name, default):
    return getattr(settings, setting_name, default)


def _catalog_version():
    version = cache.get(CATALOG_VERSION_KEY)
    if version is None:
        cache.add(CATALOG_VERSION_KEY, 1, timeout=None)
        version = cache.get(CATALOG_VERSION_KEY) or 1
    return version


def _cache_key(*parts):
    safe_parts = [quote_plus(str(part if part not in (None, '') else 'all')) for part in parts]
    return ':'.join(['products', str(_catalog_version()), *safe_parts])


def _display_image_url(product):
    if product.image:
        try:
            return product.image.url
        except ValueError:
            pass
    return product.image_url or ''


def _category_icon(slug):
    return CATEGORY_ICON_MAP.get(slug, 'fa-capsules')


def _serialize_category(category):
    return {
        'id': category.id,
        'name': category.name,
        'slug': category.slug,
        'description': category.description,
        'icon_class': _category_icon(category.slug),
    }


def _serialize_product(product):
    return {
        'id': product.id,
        'slug': product.slug,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'stock': product.stock,
        'requires_prescription': product.requires_prescription,
        'display_image_url': _display_image_url(product),
        'category_name': product.category.name,
    }


def invalidate_product_catalog_cache():
    try:
        cache.incr(CATALOG_VERSION_KEY)
    except ValueError:
        cache.set(CATALOG_VERSION_KEY, _catalog_version() + 1, timeout=None)


def get_homepage_payload():
    cache_key = _cache_key('home')
    payload = cache.get(cache_key)
    if payload is not None:
        return payload

    all_products = list(
        Product.objects.filter(active=True).select_related('category').order_by('-created_at')
    )

    featured_products = []
    seen_categories = set()

    for product in all_products:
        if product.category_id not in seen_categories:
            featured_products.append(product)
            seen_categories.add(product.category_id)
            if len(featured_products) == 6:
                break

    if len(featured_products) < 6:
        for product in all_products:
            if product not in featured_products:
                featured_products.append(product)
                if len(featured_products) == 6:
                    break

    payload = {
        'featured_products': [_serialize_product(product) for product in featured_products],
        'categories': [
            _serialize_category(category)
            for category in Category.objects.order_by('name')[:6]
        ],
    }
    cache.set(cache_key, payload, timeout=_cache_timeout('PRODUCT_CACHE_TTL', 300))
    return payload


def get_product_list_payload(query=None, category_slug=None, page_number=None, per_page=50):
    normalized_query = (query or '').strip()
    normalized_category = (category_slug or '').strip()
    normalized_page = page_number or 1
    cache_key = _cache_key('list', normalized_query.lower(), normalized_category.lower(), normalized_page)
    payload = cache.get(cache_key)
    if payload is not None:
        return payload

    products = Product.objects.filter(active=True).select_related('category').order_by('-created_at')

    if normalized_query:
        products = products.filter(
            Q(name__icontains=normalized_query) |
            Q(description__icontains=normalized_query)
        )

    if normalized_category:
        products = products.filter(category__slug=normalized_category)

    paginator = Paginator(products, per_page)
    page_obj = paginator.get_page(normalized_page)

    payload = {
        'products': [_serialize_product(product) for product in page_obj.object_list],
        'has_next': page_obj.has_next(),
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        'query': normalized_query,
        'selected_category': normalized_category,
    }
    cache.set(cache_key, payload, timeout=_cache_timeout('PRODUCT_CACHE_TTL', 300))
    return payload


def get_product_detail_payload(slug):
    normalized_slug = (slug or '').strip()
    cache_key = _cache_key('detail', normalized_slug)
    payload = cache.get(cache_key)
    if payload == MISSING_PRODUCT_SENTINEL:
        return None
    if payload is not None:
        return payload

    product = (
        Product.objects.filter(active=True)
        .select_related('category')
        .filter(slug=normalized_slug)
        .first()
    )
    if product is None:
        cache.set(
            cache_key,
            MISSING_PRODUCT_SENTINEL,
            timeout=_cache_timeout('PRODUCT_DETAIL_CACHE_TTL', 600),
        )
        return None

    payload = _serialize_product(product)
    cache.set(cache_key, payload, timeout=_cache_timeout('PRODUCT_DETAIL_CACHE_TTL', 600))
    return payload
