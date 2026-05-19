from django.core.cache import cache
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext

from .cache import (
    get_homepage_payload,
    get_product_detail_payload,
    get_product_list_payload,
)
from .models import Category, Product


TEST_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'products-test-cache',
    }
}


@override_settings(
    CACHES=TEST_CACHES,
    PRODUCT_CACHE_TTL=300,
    PRODUCT_DETAIL_CACHE_TTL=600,
)
class ProductCacheTests(TestCase):
    def setUp(self):
        cache.clear()
        self.category = Category.objects.create(name='Medicines', slug='medicines')
        self.secondary_category = Category.objects.create(name='Vitamins', slug='vitamins')
        self.product = Product.objects.create(
            name='Aspirin Tablets',
            slug='aspirin-tablets',
            category=self.category,
            description='Pain relief tablets for fever and headaches.',
            price='9.99',
            stock=10,
            active=True,
        )
        self.secondary_product = Product.objects.create(
            name='Vitamin C',
            slug='vitamin-c',
            category=self.secondary_category,
            description='Daily immunity support tablets.',
            price='14.99',
            stock=8,
            active=True,
        )

    def tearDown(self):
        cache.clear()

    def test_homepage_payload_uses_cache_after_first_lookup(self):
        with CaptureQueriesContext(connection) as first_queries:
            first_payload = get_homepage_payload()

        with CaptureQueriesContext(connection) as second_queries:
            second_payload = get_homepage_payload()

        self.assertGreater(len(first_queries), 0)
        self.assertEqual(len(second_queries), 0)
        self.assertEqual(first_payload['featured_products'], second_payload['featured_products'])

    def test_product_list_payload_is_cached_per_filter(self):
        with CaptureQueriesContext(connection) as first_queries:
            first_payload = get_product_list_payload(query='Aspirin', category_slug='medicines', page_number=1)

        with CaptureQueriesContext(connection) as second_queries:
            second_payload = get_product_list_payload(query='Aspirin', category_slug='medicines', page_number=1)

        self.assertGreater(len(first_queries), 0)
        self.assertEqual(len(second_queries), 0)
        self.assertEqual([item['slug'] for item in first_payload['products']], ['aspirin-tablets'])
        self.assertEqual(first_payload, second_payload)

    def test_product_detail_cache_is_invalidated_after_product_update(self):
        initial_payload = get_product_detail_payload('aspirin-tablets')

        self.product.name = 'Aspirin Plus'
        self.product.save()

        refreshed_payload = get_product_detail_payload('aspirin-tablets')

        self.assertEqual(initial_payload['name'], 'Aspirin Tablets')
        self.assertEqual(refreshed_payload['name'], 'Aspirin Plus')

    def test_product_detail_cache_is_invalidated_after_category_update(self):
        initial_payload = get_product_detail_payload('aspirin-tablets')

        self.category.name = 'Pain Relief'
        self.category.save()

        refreshed_payload = get_product_detail_payload('aspirin-tablets')

        self.assertEqual(initial_payload['category_name'], 'Medicines')
        self.assertEqual(refreshed_payload['category_name'], 'Pain Relief')

