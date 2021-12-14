from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DeleteView
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
# From this app
from .models import PurchaseOrder,SaleOrder, Profile
from .forms import Order_Form
from .market import Report
from django.urls import reverse_lazy
from bson import ObjectId
import logging

# Other imports


def home_view(request):

	impactReport = Report()  # ad impactReport gli assegno la classe Report()
	currency = impactReport.get_data()
	return render(request, 'app/base.html',{'currency':currency})

# Create your views here.
@login_required()
def buy_order_view(request):
	impactReport = Report()  # ad impactReport gli assegno la classe Report()
	currency = impactReport.get_data()
	purchase_orders_list = PurchaseOrder.objects.filter(status='open').order_by('created')
	sale_orders_list = SaleOrder.objects.filter(status='open').order_by('created')
	# Orders lists
	if request.method == 'POST':

		print(f'request.POST results:\n{ request.POST }')
		# Buy Order
		form = Order_Form(request.POST or None)
		if form.is_valid():
			status='open'
			price = form.cleaned_data.get('price')
			quantity = form.cleaned_data.get('quantity')


			profile_wallet = Profile.objects.get(user=request.user)
			if price < 0.0:
				messages.error(request, 'Cannot put a price lower than 0')
				return redirect('app:buy')
			if quantity < 0.0:
				messages.error(request, 'Cannot put a quantity lower than 0')
				return redirect('app:buy')
			if profile_wallet.usd_amount >= price and profile_wallet.btc_amount>= quantity:
				profile_wallet.usd_amount -=price
				profile_wallet.save()
				# Order creation
				new_buy_order = PurchaseOrder.objects.create(profile=profile_wallet,
													 status=status,
													 price=price,
													 quantity=quantity,
													 modified=timezone.now())
				messages.success(request, f'Your  purchase order of {new_buy_order.quantity} BTC for {new_buy_order.price}  is successfully added to the Order Book! || Status: {new_buy_order.status}')
				# Order matching
				if sale_orders_list.exists():
					max_order_btc=None
					for sale_order in sale_orders_list:
						if new_buy_order.profile != sale_order.profile:
							if sale_order.price <= new_buy_order.price:
								if max_order_btc == None or (sale_order.quantity >= max_order_btc.quantity and sale_order.price<= max_order_btc.price) :
									max_order_btc = sale_order



					if max_order_btc!=None:
					# Modifying orders.
						if max_order_btc.quantity >= new_buy_order.quantity:
							messages.info(request, f'Search for the best sales order')
							messages.info(request, f'Partner found! sale order id:{max_order_btc._id}')
							messages.success(request, f'He wants to sell {max_order_btc.quantity} BTC for {max_order_btc.price} $')

							# Buy order still open. Updating bitcoins yet to be bought.
							actual_btc = profile_wallet.btc_amount

							new_buy_order.quantity = sale_order.quantity
							new_buy_order.status='close'
							new_buy_order.save()
							profile_wallet.btc_amount+=new_buy_order.quantity
							profile_wallet.save()
							messages.info(request, 'Start of the bitcoin exchange')
							messages.success(request,f'Your Buy order id: {new_buy_order._id}. || Status: {new_buy_order.status}.')
							messages.success(request, f'|| BTC before exchange: {actual_btc}; || BTC after exchange: {profile_wallet.btc_amount};')

							# Sell order can close.
							sell_order = SaleOrder.objects.get(_id=sale_order._id)
							profile_s= Profile.objects.get(user= sell_order.profile.user)
							profile_s.usd_amount+=new_buy_order.price

							profile_s.save()
							max_order_btc.status = 'close'
							max_order_btc.save()

							messages.success(request, f'Sell order id: {max_order_btc._id}. || Status: {max_order_btc.status}.')
							messages.success(request, f'Received  successfully {new_buy_order.price} $.')
							messages.info(request, 'The bitcoin exchange has been totally executed! Congratulations!')
							return redirect('app:buy')
						elif max_order_btc.quantity < new_buy_order.quantity:
							messages.info(request, f'Search for the best sales order')
							messages.info(request, f'Partner found! sale order id:{max_order_btc._id}')
							messages.success(request, f'He wants to sell {max_order_btc.quantity} BTC for {max_order_btc.price} $')

							messages.error(request,"The amount of bitcoins they want to sell is less than the amount you want to buy")
							messages.error(request, f"|Amount of bitcoins placed for sale : {max_order_btc.quantity} ")
							messages.error(request, f"||Amount of bitcoins you want to buy : {new_buy_order.quantity}")


						else:
							return redirect('app:buy')
				else:

					return redirect('app:buy')
			else:
				messages.error(request, 'Your balance is not enough.')
		else:
			messages.error(request, 'Order can not have negative values!')





	# Orders lists refresh
	form = Order_Form()
	profile_pocket= Profile.objects.get(user=request.user)
	# Getting latest trade price



	return render(request, 'app/page_buy.html', {'form': form,
														  'purchase_orders_list': purchase_orders_list,
														  'sale_orders_list': sale_orders_list,
														  'profile_pocket': profile_pocket,
													  	  'currency': currency
																  })


def sell_order_view(request):
	purchase_orders_list = PurchaseOrder.objects.filter(status='open').order_by('created')
	sale_orders_list = SaleOrder.objects.filter(status='open').order_by('created')
	impactReport = Report()  # ad impactReport gli assegno la classe Report()
	currency = impactReport.get_data()

	if request.method == 'POST':
		form = Order_Form(request.POST or None)
		if form.is_valid():
			status = 'open'
			price = form.cleaned_data.get('price')
			quantity = form.cleaned_data.get('quantity')
			# Checking wallet availability.
			profile_wallet = Profile.objects.get(user=request.user)
			if price < 0.0:
				messages.error(request, 'Cannot put a price lower than 0')
				return redirect('app:sell')
			if quantity < 0.0:
				messages.error(request, 'Cannot put a quantity lower than 0')
				return redirect('app:sell')
			if profile_wallet.btc_amount >= quantity:
				profile_wallet.btc_amount -= quantity
				profile_wallet.save()
				# Order creation
				new_sell_order = SaleOrder.objects.create(profile=profile_wallet,
													 status=status,
													 price=price,
													 quantity=quantity,
													 modified=timezone.now())
				messages.success(request, f'Your sales order of {new_sell_order.quantity} BTC for {new_sell_order.price}  is successfully added to the Order Book! || Status:{new_sell_order.status}')
				# Order matching
				if purchase_orders_list.exists():

					max_value = None
					for buy_open_order in purchase_orders_list:
						if buy_open_order.profile != new_sell_order.profile:
							if  buy_open_order.price >= new_sell_order.price :

								if max_value == None or (buy_open_order.price > max_value.price and buy_open_order.quantity<= max_value.quantity) :
									max_value = buy_open_order

									if max_value.quantity < new_sell_order.quantity:
										messages.info(request,f'Search for the best purchase order')
										messages.info(request,f'Partner found! purchase order id:{max_value._id}')
										messages.success(request,f'He wants to buy {max_value.quantity} BTC for {max_value.price} $')

										messages.error(request,"The amount of bitcoins they want to buy is less than the amount you want to sell")
										messages.error(request,f"|Amount of bitcoins placed for sale : {new_sell_order.quantity} ")
										messages.error(request, f"||Amount of bitcoins they want to buy : {max_value.quantity}")
										max_value=None



					if max_value!=None:

						if max_value.quantity == new_sell_order.quantity:
							# Sell order can close.
							actual_usd=profile_wallet.usd_amount
							new_sell_order.status ='close'
							new_sell_order.save()
							profile_wallet.usd_amount+=max_value.price
							profile_wallet.save()
							messages.info(request, f'Search for the best purchase order')
							messages.info(request, f'Partner found! purchase order id:{max_value._id}')
							messages.success(request, f'He wants to buy {max_value.quantity} BTC for {max_value.price} $')
							messages.info(request,'Start of the bitcoin exchange')
							messages.success(request, f'Sell order id: {new_sell_order._id}. || Status: {new_sell_order.status}.')
							messages.success(request,f'|| USD before exchange: {actual_usd}; || USD after exchange: {profile_wallet.usd_amount};')

							profile_b = Profile.objects.get(user=max_value.profile.user)
							profile_b.btc_amount +=new_sell_order.quantity
							profile_b.save()
							max_value.status = 'close'
							max_value.save()
							messages.success(request,f'Buy order id: {max_value._id}. || Status: {max_value.status}.')
							messages.success(request,f'Received  successfully {new_sell_order.quantity} BTC.')
							messages.info(request, 'The bitcoin exchange has been totally executed! Congratulations!')
							return redirect('app:sell')
					else:
						return redirect('app:sell')

				else:

					return redirect('app:sell')
			else:
				messages.error(request, 'Your balance is not enough.')
		else:
			messages.error(request, 'Order can not have negative values!')



	# Orders lists refresh
	form = Order_Form()
	profile_pocket= Profile.objects.get(user=request.user)

	return render(request, 'app/page_sell.html', {'form': form,
													  'purchase_orders_list': purchase_orders_list,
													  'sale_orders_list': sale_orders_list,
													  'profile_pocket': profile_pocket,
												      'currency': currency

												  })
def profit(request):
	response = []
	profile = Profile.objects.get(user=request.user)
	response.append(
		{
			'User ID': str(profile._id),
			'Name': profile.user.first_name,
			'Surname': profile.user.last_name,
			'Balance': profile.usd_amount,
			'BTC': profile.btc_amount,
			'Profit': profile.profit
		}
	)
	return JsonResponse(response, safe=False)

def purchase_order_Book(request):
    response = []
    activeOrders = PurchaseOrder.objects.filter(status='open').order_by('price')
    for order in activeOrders:
        response.append(
            {
                'Order ID': str(order._id),
                'Status': order.status,
                'created': order.created,
                'Price': order.price,
                'Quantity': order.quantity,
				'Modified':order.modified
            }
        )
    return JsonResponse(response, safe=False)

def sale_order_Book(request):
    response = []
    activeOrders =SaleOrder.objects.filter(status='open').order_by('price')
    for order in activeOrders:
        response.append(
            {
                'Order ID': str(order._id),
                'Status': order.status,
                'created': order.created,
                'Price': order.price,
                'Quantity': order.quantity,
				'Modified':order.modified
            }
        )
    return JsonResponse(response, safe=False)

def delete_order_view(request):

	if request.method == 'POST':
		_id = ObjectId(request.POST['delete'])

		if PurchaseOrder.objects.get(id=_id) :
			p_order = PurchaseOrder.objects.get(id=_id)
			profile_pocket = Profile.objects.get(user=p_order.user)
			profile_pocket.usd_amount += p_order.price
			profile_pocket.save()
			p_order.delete()
			messages.success(request, 'Your order has been deleted successfully!')
			return redirect('app:buy')
		elif  SaleOrder.objects.get(id=_id):
			s_order = SaleOrder.objects.get(id=_id)
			profile_pocket = Profile.objects.get(user=s_order.user)
			profile_pocket.btc_amount += s_order.quantity
			profile_pocket.save()
			s_order.delete()
			messages.success(request, 'Your order has been deleted successfully!')
			return redirect('app:sell')


	return render(request, 'app/order_delete.html')
	# If method is not POST, render the default template.
# *Note*: Replace 'template_name.html' with your corresponding template name.
