import logging

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .cache import (
    get_homepage_payload,
    get_product_detail_payload,
    get_product_list_payload,
)
from .models import Product
from .serializers import ProductSerializer


def home(request):
    return render(request, 'products/home.html', get_homepage_payload())


def product_list(request):
    query = request.GET.get('q')
    category_slug = request.GET.get('category')
    page_number = request.GET.get('page')
    context = get_product_list_payload(
        query=query,
        category_slug=category_slug,
        page_number=page_number,
    )

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.GET.get('ajax') == '1'
    )

    if is_ajax:
        return render(request, 'products/partials/product_list_chunk.html', context)

    return render(request, 'products/product_list.html', context)


def product_detail(request, slug):
    product = get_product_detail_payload(slug)
    if product is None:
        raise Http404('Product not found')
    return render(request, 'products/product_detail.html', {'product': product})


class ProductsApi(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @action(detail=True, methods=["get"])
    def schedule(self, request, pk=None):
        product = self.get_object()
        return Response({
            "id": product.id,
            "name": product.name,
            "price": product.price,
        })

def upload_rx(request):
    import groq
    import json
    import os
    import base64
    
    if request.method == 'POST' and request.FILES.get('rx_image'):
        try:
            image_file = request.FILES['rx_image']
            
            # Read image file and encode to base64
            image_data = image_file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            api_key = settings.GROQ_API_KEY
            if not api_key:
                return render(request, 'products/upload_rx.html', {'error': 'System Error: Groq API Key missing. Please set GROQ_API_KEY in .env'})
            
            client = groq.Groq(api_key=api_key)
            
            # Improved Prompt for Vision Model
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": """Analyze this prescription image and extract ONLY actual pharmaceutical medicine/drug names.
                            
IMPORTANT RULES:
- Return ONLY a valid JSON list of strings (e.g. ["Medicine A", "Medicine B"])
- ONLY include actual medicine names (like "Paracetamol", "Amoxicillin", "Metformin")
- IGNORE any non-medicine text like:
  * Instructions (e.g., "Take twice daily", "After meals")
  * Patient information (e.g., "John Doe", "Age 45")
  * Doctor information (e.g., "Dr. Smith", "License #123")
  * Dates, addresses, or clinic names
  * Non-medical terms like "Backtesting", "Paper Trading", etc.
- If no actual medicine names are found, return an empty list []

Do not include any other text or markdown formatting."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ]

            try:
                # Use Llama 4 Scout which is multimodal
                chat_completion = client.chat.completions.create(
                    messages=messages,
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    temperature=0.1
                )
                response_content = chat_completion.choices[0].message.content.strip()
            except groq.BadRequestError as e:
                # Fallback to Maverick if Scout fails
                logging.warning(f"Llama 4 Scout failed, trying Maverick: {e}")
                chat_completion = client.chat.completions.create(
                    messages=messages,
                    model="meta-llama/llama-4-maverick-17b-128e-instruct",
                )
                response_content = chat_completion.choices[0].message.content.strip()
            
            # Clean up potential markdown code blocks
            if response_content.startswith('```json'):
                response_content = response_content.replace('```json', '').replace('```', '')
            elif response_content.startswith('```'):
                response_content = response_content.replace('```', '')

            try:
                detected_medicines = json.loads(response_content)
                if not isinstance(detected_medicines, list):
                     if isinstance(detected_medicines, dict):
                        for key, value in detected_medicines.items():
                            if isinstance(value, list):
                                detected_medicines = value
                                break
                     else:
                        detected_medicines = []
            except json.JSONDecodeError:
                detected_medicines = []
                logging.error(f"Failed to parse Groq response: {response_content}")
            
            # Additional filtering: Only keep items that might be medicine names
            # This helps filter out obvious non-medicine terms
            filtered_medicines = []
            common_non_medical = ['backtesting', 'paper trading', 'trading alerts', 'algorithmic trading', 
                                 'buy', 'sell', 'signal', 'indicator', 'strategy', 'test', 'demo']
            
            for med in detected_medicines:
                med_lower = med.lower()
                # Skip if it contains common non-medical terms
                if any(term in med_lower for term in common_non_medical):
                    continue
                # Skip very short terms (likely not medicine names)
                if len(med) < 3:
                    continue
                filtered_medicines.append(med)
            
            # Product Matching - only with filtered medicines
            matched_products = []
            for med in filtered_medicines:
                # Search by name (icontains)
                matches = Product.objects.filter(name__icontains=med, active=True)
                for match in matches:
                    if match not in matched_products:
                        matched_products.append(match)
            
            # If no medicines detected or no matches found, return false
            if not filtered_medicines or not matched_products:
                return render(request, 'products/rx_results.html', {
                    'detected_medicines': filtered_medicines if filtered_medicines else False,
                    'matched_products': False
                })
            
            return render(request, 'products/rx_results.html', {
                'detected_medicines': filtered_medicines,
                'matched_products': matched_products
            })

        except Exception as e:
            logging.error(f"Error processing Rx: {str(e)}")
            return render(request, 'products/upload_rx.html', {'error': f"Error processing image: {str(e)}"})

    return render(request, 'products/upload_rx.html')
