from django.urls import path
from . import views


app_name = 'app'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('exchange/order/', views.order_exchange_view, name='order'),
    path(f'exchange/<str:id>/delete/', views.delete_order_view, name='delete'),
    path('profit/', views.profit, name='profit'),
    path('json-purchase/', views.purchase_order_Book, name='json-purchase'),
    path('json-sale/', views.sale_order_Book, name='json-sale'),



]

