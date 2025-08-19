from django.shortcuts import render,get_object_or_404,redirect
from django.http import JsonResponse
from django.conf import settings
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from myapp.models import Product,Order
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

class ProductView(View):
    def get(self, request):
        products = Product.objects.all()
        return render(request, "product_list.html", {"products": products})



class CheckoutView(LoginRequiredMixin,View):
    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        return render(request, "checkout.html", {"product": product})



def success(request):
    return render(request, "success.html")

def cancel(request):
    return render(request, "cancel.html")

@method_decorator(csrf_exempt,name='dispatch')
class CreatePaymentView(LoginRequiredMixin , View):
    def post(self , request , product_id):
        product = get_object_or_404(Product , id=product_id)
        if product.stock <= 0:
            return JsonResponse({"error": "This product is out of stock"}, status=400)

        order = Order.objects.create(user=request.user , product=product , amount=product.price)
        
        checkout_session = stripe.checkout.Session.create(
            line_items= [{
                'price_data':{
                    'currency':'usd',
                    "unit_amount":int(product.price * 100),
                    "product_data":{
                        "name":product.name
                    }
                },
                "quantity":1,
            }],
            mode='payment',
            customer_email= request.user.email,
            success_url='http://localhost:8000/success/',
            cancel_url='http://localhost:8000/cancel/',
            
        )
        order.stripe_checkout_session_id = checkout_session.id
        order.save()
        return redirect(checkout_session.url)
  
@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    def post(self, request):
        payload = request.body  
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=endpoint_secret
            )
        except (ValueError, stripe.error.InvalidRequestError) as e:
            return JsonResponse({"error": "Invalid payload"}, status=400)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            try:
                order = Order.objects.get(stripe_checkout_session_id=session["id"])
                order.is_paid = True
                order.save()
                
                product = order.product
                if product.stock > 0:
                    product.stock -= 1
                    product.save()
                else:
                    print("Stock already empty!")
            except Order.DoesNotExist:
                return JsonResponse({"error": "Order not found"}, status=404)

        return JsonResponse({"status": "success"}, status=200)

