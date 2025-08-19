from django.urls import path
from myapp.views import     ProductView , CheckoutView ,success , cancel ,CreatePaymentView , StripeWebhookView
urlpatterns = [
    path('',ProductView.as_view() , name="product_list"),
    path('checkout/<int:product_id>/',CheckoutView.as_view() , name="checkout"),
    path('create-payment/<int:product_id>/',CreatePaymentView.as_view() , name="create_payment"),
    path('stripe-webhook/', StripeWebhookView.as_view(), name="webhook"),
    path('success/',success , name="success"),
    path('cancel/',cancel , name="cancel"),
]   