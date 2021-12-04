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
	purchase_orders_list = PurchaseOrder.objects.filter(status='open').order_by('price')
	sale_orders_list = SaleOrder.objects.filter(status='open').order_by('price')
	# Orders lists
	if request.method == 'POST':

		print(f'request.POST results:\n{ request.POST }')
		# Buy Order
		form = Order_Form(request.POST or None)
		if form.is_valid():
			status='open'
			price = form.cleaned_data.get('price')
			quantity = form.cleaned_data.get('quantity')
			P_Q = price*quantity

			profile_wallet = Profile.objects.get(user=request.user)
			if price < 0.0:
				messages.error(request, 'Cannot put a price lower than 0')
				return redirect('app:buy')
			if quantity < 0.0:
				messages.error(request, 'Cannot put a quantity lower than 0')
				return redirect('app:buy')
			if profile_wallet.usd_amount >= price and profile_wallet.btc_amount>= quantity:
				profile_wallet.usd_amount -=price
				profile_wallet.btc_amount -= quantity
				profile_wallet.save()
				# Order creation
				new_buy_order = PurchaseOrder.objects.create(profile=profile_wallet,
													 status=status,
													 price=price,
													 quantity=quantity,
													 modified=timezone.now())
				# Order matching
				if sale_orders_list.exists():
					for num, sale_order in enumerate(sale_orders_list):
						if new_buy_order.profile != sale_order.profile:

							if sale_order.price <= new_buy_order.price:
								messages.success(request,f'Partner found! Purchase Order ID: {new_buy_order._id}.\n'
									  f'Sale order id: {sale_order._id}.\n'
									 )



								# Modifying orders.
								if sale_order.quantity >= new_buy_order.quantity:
									# Buy order still open. Updating bitcoins yet to be bought.
									actual_btc = new_buy_order.quantity

									new_buy_order.quantity += sale_order.quantity
									new_buy_order.price-=sale_order.price
									new_buy_order.status='close'
									new_buy_order.save()
									profile_wallet.btc_amount+=new_buy_order.quantity
									profile_wallet.usd_amount+=new_buy_order.price
									profile_wallet.save()
									messages.success(request,f'Buy order id: {new_buy_order._id}. Status: {new_buy_order.status}.\n'
										  f'BTC before trade: {actual_btc}; BTC after trade: {new_buy_order.quantity};')
									# Sell order can close.
									sell_order = SaleOrder.objects.get(_id=sale_order._id)
									profile_s= Profile.objects.get(user= sell_order.profile.user)
									profile_s.usd_amount+=sale_order.price

									profile_s.save()
									sell_order.status = 'close'
									sell_order.save()

									messages.success(request,f'Sell order id: {sell_order._id}. received the money successfully. Status: {sell_order.status}.')
									messages.success(request, 'Your order has been totally executed! Congratulations!')
									return redirect('app:buy')
								elif sale_order.quantity < new_buy_order.quantity:
									messages.error(request,"The amount of bitcoins sold is less than the amount you want to buy\n"
										  f"amount of bitcoins placed for sale : {sale_order.quantity} \n"
										  f"amount of bitcoins you want to buy : {new_buy_order.quantity}")


							else:
								return redirect('app:buy')
				else:
					messages.success(request, 'Your order is successfully added to the Order Book!')
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
	purchase_orders_list = PurchaseOrder.objects.filter(status='open').order_by('price')
	sale_orders_list = SaleOrder.objects.filter(status='open').order_by('price')
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
				# Order matching
				if purchase_orders_list.exists():
					for buy_open_order in purchase_orders_list:
						if buy_open_order.profile != new_sell_order.profile:

							if  buy_open_order.price >= new_sell_order.price:
								messages.success(request,f'Partner found! Sale Order ID: {new_sell_order._id}.\n'
									  f'Buy order id: {buy_open_order._id}.\n'
									  )



								# Modifying orders.
								if buy_open_order.quantity < new_sell_order.quantity:
									messages.error(request,
												   "The amount of bitcoins they want to buy is less than the amount you want to sell\n"
												   f"amount of bitcoins placed for sale : {new_sell_order.quantity} \n"
												   f"amount of bitcoins they want to buy : {buy_open_order.quantity}")
								elif buy_open_order.quantity >= new_sell_order.quantity:
									# Sell order can close.
									actual_usd=new_sell_order.price
									new_sell_order.status ='close'
									new_sell_order.save()
									profile_wallet.usd_amount+=buy_open_order.price
									profile_wallet.save()
									messages.success(request,f'Sell order id: {new_sell_order._id}. Status: {new_sell_order.status}.')
									profile_b = Profile.objects.get(user=buy_open_order.profile.user)
									profile_b.btc_amount +=buy_open_order.quantity

									profile_b.save()
									buy_open_order.status = 'close'
									buy_open_order.save()
									messages.success(request, f'Sell order id: {new_sell_order._id}. Status: {new_sell_order.status}.')
									messages.success(request, 'Your order has been totally executed! Congratulations!')
									return redirect('app:sell')

				else:
					messages.success(request, 'Your order is successfully added to the Order Book!')
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
