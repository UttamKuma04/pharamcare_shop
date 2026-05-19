# PharmaCare

## Project Summary

| Item | Details |
| --- | --- |
| Project type | Django online pharmacy and medical assistant web app |
| Main domain | Medicine catalog, cart, checkout, prescription matching, AI chat |
| Backend | Django app with Django REST Framework endpoints |
| Frontend | Django templates with responsive HTML, CSS, and JavaScript |
| Deployment | Gunicorn, WhiteNoise, `build.sh`, Render/Railway-ready settings |

## Tech Stack

| Layer | Technology |
| --- | --- |
| Language | Python |
| Framework | Django 5.2.8 |
| API | Django REST Framework 3.16.1 |
| Database | SQLite by default, PostgreSQL via `DATABASE_URL` |
| Database config | `dj-database-url`, `psycopg2-binary` |
| Cache | Redis via `django-redis`, fallback Django local memory cache |
| AI chat | Groq API, `llama-3.3-70b-versatile`, fallback `llama-3.1-8b-instant` |
| AI vision | Groq Llama 4 Scout, fallback Llama 4 Maverick |
| Speech | Sarvam AI TTS/STT |
| File parsing | PyPDF2, Pillow |
| Email | Django SMTP backend with Brevo SMTP relay |
| Static files | WhiteNoise, Django staticfiles |
| Frontend assets | Django templates, Font Awesome, Google Fonts, vanilla JavaScript |

## Installed Django Apps

| App | Purpose |
| --- | --- |
| `products` | Catalog, categories, products, product API, prescription upload, cache logic |
| `cart` | Shopping cart, cart item updates, checkout, cart API |
| `accounts` | Registration, email activation, login, logout, profile, order history |
| `Chatbot` | AI assistant, chat API, uploaded file analysis, TTS, STT |
| `app` | Legacy/scaffold app with old product/order models |
| `mr_doctor` | Project settings, root URLs, ASGI/WSGI |

## Main Features

### Product Catalog

| Feature | Implementation |
| --- | --- |
| Home page | Featured products and category list |
| Product listing | Search by query, filter by category, active products only |
| AJAX pagination | Load-more product chunks through partial template |
| Product detail | Product image, price, stock, category, description, prescription badge |
| Product images | Local `ImageField` first, fallback `image_url` |
| Category icons | Slug-based Font Awesome icon mapping |
| Catalog cache | Cached home/list/detail payloads |
| Cache invalidation | Product/category save or delete increments catalog version |
| Seed data | `python manage.py populate_db` creates sample categories and products |

### Prescription Upload

| Feature | Implementation |
| --- | --- |
| Upload page | `/upload-rx/` |
| Input | Prescription image |
| AI extraction | Groq vision model extracts medicine names as JSON |
| Filtering | Removes short and obvious non-medical terms |
| Product matching | Matches detected medicines against active product names |
| Results page | Shows detected medicines and matched products |

### Cart And Checkout

| Feature | Implementation |
| --- | --- |
| Authenticated cart | One cart per logged-in user, duplicate cleanup in cart view |
| Add item | Adds product or increments existing quantity |
| Update item | Updates quantity or deletes when quantity is not positive |
| Remove item | Deletes cart item |
| Cart total | Calculated from cart item subtotals |
| Checkout | Creates `Order` and `OrderItem` records |
| Post-checkout | Clears cart items and redirects home |
| Cart API | Session-key scoped cart viewset |

### Accounts

| Feature | Implementation |
| --- | --- |
| Registration | Creates inactive user with first name, last name, email, password |
| Email activation | Tokenized activation link using Django token generator |
| Login/logout | Custom login/logout views |
| Profile | Editable user details |
| Order history | Shows user orders and order items |
| Password reset | Django auth password reset views and custom templates |
| Profile update email | Sends notification after profile update |

### AI Chatbot

| Feature | Implementation |
| --- | --- |
| Floating assistant | Included on all pages except login/register |
| Languages | English, Hindi, Hinglish |
| Chat API | `/chatbot/api/chat/` |
| Context | User name, cart items, cart total, recent orders |
| Conversation memory | Last 10 saved chat messages |
| File upload | `.txt`, `.pdf`, `.jpg`, `.jpeg`, `.png` |
| PDF parsing | PyPDF2 text extraction |
| Image text extraction | Groq vision model |
| Suggestions | Numbered follow-up questions rendered as clickable chips |
| Text-to-speech | Sarvam AI audio response |
| Speech-to-text | Browser recording sent to Sarvam AI batch transcription |
| Chat storage | `ChatMessage` records for users or anonymous sessions |

### REST API

| Endpoint | View/Class | Purpose |
| --- | --- | --- |
| `/api/products/` | `ProductsApi` | Product CRUD API |
| `/api/products/<id>/schedule/` | `ProductsApi.schedule` | Product summary response |
| `/cart/api/carts/` | `CartViewSet` | Session-scoped cart API |
| `/cart/api/carts/<id>/schedule/` | `CartViewSet.schedule` | Cart summary response |

## URL Map

| URL | Name | View |
| --- | --- | --- |
| `/admin/` | Django admin | `admin.site.urls` |
| `/` | `products:home` | `products.views.home` |
| `/products/` | `products:product_list` | `products.views.product_list` |
| `/product/<slug:slug>/` | `products:product_detail` | `products.views.product_detail` |
| `/upload-rx/` | `products:upload_rx` | `products.views.upload_rx` |
| `/api/products/` | DRF router | `ProductsApi` |
| `/cart/` | `cart:cart_detail` | `cart.views.cart_detail` |
| `/cart/add/<int:product_id>/` | `cart:add_to_cart` | `cart.views.add_to_cart` |
| `/cart/remove/<int:item_id>/` | `cart:remove_from_cart` | `cart.views.remove_from_cart` |
| `/cart/update/<int:item_id>/` | `cart:update_cart` | `cart.views.update_cart` |
| `/cart/checkout/` | `cart:checkout` | `cart.views.checkout` |
| `/cart/api/carts/` | DRF router | `CartViewSet` |
| `/accounts/register/` | `accounts:register` | `accounts.views.register` |
| `/accounts/login/` | `accounts:login` | `accounts.views.user_login` |
| `/accounts/logout/` | `accounts:logout` | `accounts.views.user_logout` |
| `/accounts/profile/` | `accounts:profile` | `accounts.views.profile` |
| `/accounts/activate/<uidb64>/<token>/` | `accounts:activate` | `accounts.views.activate` |
| `/accounts/password_reset/` | `password_reset` | Django `PasswordResetView` |
| `/accounts/` | Django auth URLs | Password reset confirm/done/complete |
| `/chatbot/` | `chatbot:home` | `Chatbot.views.home` |
| `/chatbot/products/` | `chatbot:product_list` | `Chatbot.views.product_list` |
| `/chatbot/product/<slug:slug>/` | `chatbot:product_detail` | `Chatbot.views.product_detail` |
| `/chatbot/api/chat/` | `chatbot:chat_api` | `Chatbot.views.chat_api` |
| `/chatbot/api/tts/` | `chatbot:text_to_speech_api` | `Chatbot.views.text_to_speech_api` |
| `/chatbot/api/transcribe/` | `chatbot:transcribe_api` | `Chatbot.views.transcribe_api` |

## Data Models

| Model | App | Main Fields |
| --- | --- | --- |
| `Category` | `products` | `name`, `slug`, `description` |
| `Product` | `products` | `name`, `slug`, `category`, `description`, `price`, `stock`, `image`, `image_url`, `requires_prescription`, `active`, timestamps |
| `Order` | `products` | `user`, `status`, `total_price`, `shipping_address`, timestamps |
| `OrderItem` | `products` | `order`, `product`, `quantity`, `price` |
| `Cart` | `cart` | `user`, `session_key`, timestamps |
| `CartItem` | `cart` | `cart`, `product`, `quantity` |
| `ChatMessage` | `Chatbot` | `user`, `session_id`, `message`, `role`, `created_at` |
| `Productlist` | `app` | `productId`, `productName`, `price`, `image`, `description` |
| `OrderDetail` | `app` | `user` |

## Core Functions And Classes

| File | Functions/Classes |
| --- | --- |
| `products/views.py` | `home`, `product_list`, `product_detail`, `upload_rx`, `ProductsApi` |
| `products/cache.py` | `get_homepage_payload`, `get_product_list_payload`, `get_product_detail_payload`, `invalidate_product_catalog_cache` |
| `products/signals.py` | `clear_product_catalog_cache` |
| `products/serializers.py` | `ProductSerializer` |
| `products/management/commands/populate_db.py` | `Command.handle` |
| `cart/views.py` | `cart_detail`, `add_to_cart`, `remove_from_cart`, `update_cart`, `checkout`, `CartViewSet` |
| `cart/models.py` | `Cart.get_total`, `CartItem.get_subtotal` |
| `cart/serializers.py` | `CartSerializer`, `CartItemSerializer` |
| `accounts/views.py` | `register`, `activate`, `user_login`, `user_logout`, `profile` |
| `accounts/forms.py` | `UserRegisterForm`, `UserLoginForm`, `UserUpdateForm` |
| `Chatbot/views.py` | `home`, `product_list`, `product_detail`, `chat_api`, `text_to_speech_api`, `transcribe_api` |
| `Chatbot/utils.py` | `get_groq_response`, `extract_text_from_image`, `generate_audio`, `transcribe_audio` |
| `mr_doctor/settings.py` | `env_flag` |

## Templates

| Template | Purpose |
| --- | --- |
| `templates/base.html` | Shared layout, navigation, search, messages, footer, chatbot include |
| `products/templates/products/home.html` | Home page |
| `products/templates/products/product_list.html` | Product listing and load-more script |
| `products/templates/products/product_detail.html` | Product detail page |
| `products/templates/products/upload_rx.html` | Prescription upload page |
| `products/templates/products/rx_results.html` | Prescription analysis results |
| `products/templates/products/partials/product_card.html` | Reusable product card |
| `products/templates/products/partials/product_list_chunk.html` | AJAX product list chunk |
| `cart/templates/cart/cart_detail.html` | Shopping cart page |
| `cart/templates/cart/checkout.html` | Checkout page |
| `accounts/templates/accounts/login.html` | Login page |
| `accounts/templates/accounts/register.html` | Registration page |
| `accounts/templates/accounts/profile.html` | Profile and order history |
| `templates/chatbot.html` | Floating chatbot component |
| `templates/registration/*.html` | Password reset templates |
| `templates/accounts/activation_email.txt` | Activation email text |

## Environment Variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | No | Enables Django debug mode when true |
| `DATABASE_URL` | No | Uses PostgreSQL when set, SQLite when absent |
| `DATABASE_SSL_REQUIRE` | No | Requires TLS for external PostgreSQL connections when true |
| `REDIS_URL` | No | Enables Redis-backed cache when set |
| `SECURE_SSL_REDIRECT` | No | Redirects HTTP requests to HTTPS in production |
| `SESSION_COOKIE_SECURE` | No | Sends session cookies only over HTTPS |
| `CSRF_COOKIE_SECURE` | No | Sends CSRF cookies only over HTTPS |
| `SECURE_HSTS_SECONDS` | No | Enables HTTP Strict Transport Security when greater than `0` |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | No | Applies HSTS to subdomains |
| `SECURE_HSTS_PRELOAD` | No | Marks the site as HSTS preload-ready |
| `PRODUCT_CACHE_TTL` | No | Product list/home cache timeout, default `300` |
| `PRODUCT_DETAIL_CACHE_TTL` | No | Product detail cache timeout, default `600` |
| `GROQ_API_KEY` | For AI features | Chat, vision, prescription extraction |
| `SARVAM_API_KEY` | For speech features | Text-to-speech and speech-to-text |
| `EMAIL_HOST_USER` | For email | Brevo SMTP username |
| `EMAIL_HOST_PASSWORD` | For email | Brevo SMTP password |

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py populate_db
python manage.py runserver
```

## Useful Commands

| Command | Purpose |
| --- | --- |
| `python manage.py runserver` | Start local server |
| `python manage.py migrate` | Apply database migrations |
| `python manage.py makemigrations` | Create migrations |
| `python manage.py createsuperuser` | Create admin user |
| `python manage.py populate_db` | Add dummy product data |
| `python manage.py test` | Run tests |
| `python manage.py collectstatic --noinput` | Collect static files |

## Deployment

| File/Setting | Purpose |
| --- | --- |
| `build.sh` | Installs dependencies, collects static files, runs migrations |
| `gunicorn` | Production WSGI server |
| `whitenoise` | Static file serving |
| Security env vars | Apply HTTPS, cookie, and HSTS settings per environment |
| `CSRF_TRUSTED_ORIGINS` | Allows Railway, Render, localhost origins |

## Testing

| Test Area | File |
| --- | --- |
| Product cache behavior | `products/tests.py` |
| Empty scaffold tests | `accounts/tests.py`, `cart/tests.py`, `Chatbot/tests.py`, `app/tests.py` |
