from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Order, Profile
from .forms import Order_Form
from .market import Report
from bson import ObjectId





def home_view(request):
    impactReport = Report()  # ad impactReport gli assegno la classe Report()
    currency = impactReport.get_data()
    return render(request, 'app/base.html',{'currency':currency})

# Create your views here.
@login_required()
def order_exchange_view(request):
    impactReport = Report()  # ad impactReport gli assegno la classe Report()
    currency = impactReport.get_data()
    purchase_orders_list = Order.objects.filter(status='open',type='buy').order_by('-price')
    sale_orders_list = Order.objects.filter(status='open',type='sell').order_by('-price')
    # Orders lists
    if request.method == 'POST':
        if request.POST.get('buy'):

            # Buy Order
            form = Order_Form(request.POST or None)
            if form.is_valid():

                status='open'
                type='buy'
                price = form.cleaned_data.get('price')
                quantity = form.cleaned_data.get('quantity')
                profile_wallet = Profile.objects.get(user=request.user)

                if price <=0.0:
                    messages.error(request, 'Cannot put a price lower than 0')
                    return redirect('app:order')
                if quantity <= 0.0:
                    messages.error(request, 'Cannot put a quantity lower than 0')
                    return redirect('app:order')


                if profile_wallet.usd_amount >= price:
                    # Order creation
                    new_buy_order = Order.objects.create(profile=profile_wallet,
                                                         status=status,
                                                         type=type,
                                                         price=price,
                                                         quantity=quantity,
                                                         modified=timezone.now())
                    messages.success(request, f'Your  purchase order of {new_buy_order.quantity} BTC for {new_buy_order.price} ,{new_buy_order._id}  is successfully added to the Order Book! || Status: {new_buy_order.status}')
                    # Order matching
                    if sale_orders_list.exists():
                        for sale_order in sale_orders_list:
                                if sale_order.price <= new_buy_order.price :

                                    messages.info(request, f'Search for the best sales order')
                                    messages.info(request, f'Partner found! sale order id:{sale_order._id}')
                                    messages.success(request,
                                                     f'He wants to sell {sale_order.quantity} BTC for {sale_order.price} $')
                                    messages.info(request, 'Start of the bitcoin exchange')

                                    if sale_order.quantity == new_buy_order.quantity:

                                        actual_btc = profile_wallet.btc_amount

                                        new_buy_order.quantity = sale_order.quantity
                                        new_buy_order.status='close'
                                        new_buy_order.save()
                                        profile_wallet.btc_amount+=new_buy_order.quantity
                                        profile_wallet.usd_amount-=(sale_order.price*sale_order.quantity)
                                        profile_wallet.save()

                                        messages.success(request,f'Your Buy order id: {new_buy_order._id}. || Status: {new_buy_order.status}.')
                                        messages.success(request, f'|| BTC before exchange: {actual_btc}; || BTC after exchange: {profile_wallet.btc_amount};')

                                        # Sell order can close.
                                        sell_order = Order.objects.get(_id=sale_order._id)
                                        profile_s= Profile.objects.get(user= sell_order.profile.user)
                                        profile_s.usd_amount+=(sale_order.price*sale_order.quantity)

                                        profile_s.save()
                                        sale_order.status = 'close'
                                        sale_order.save()

                                        messages.success(request, f'Sell order id: {sale_order._id}. || Status: {sale_order.status}.')
                                        messages.success(request, f' The User who Sold has Received  successfully {sale_order.price}$ *{sale_order.quantity} .')
                                        messages.info(request, 'The bitcoin exchange has been totally executed! Congratulations!')
                                        return redirect('app:order')
                                    elif sale_order.quantity > new_buy_order.quantity :
                                        actual_btc = profile_wallet.btc_amount

                                        new_buy_order.price = sale_order.price
                                        new_buy_order.status = 'close'
                                        new_buy_order.save()
                                        profile_wallet.btc_amount+=new_buy_order.quantity
                                        profile_wallet.usd_amount-=(new_buy_order.price*new_buy_order.quantity)
                                        profile_wallet.save()
                                        messages.success(request,
                                                         f'Your Buy order id: {new_buy_order._id}. || Status: {new_buy_order.status}.')
                                        messages.success(request,
                                                         f'|| BTC before exchange: {actual_btc}; || BTC after exchange: {profile_wallet.btc_amount};')

                                        sale_order.quantity-=new_buy_order.quantity
                                        sale_order.save()

                                        sell_order = Order.objects.get(_id=sale_order._id)
                                        profile_s = Profile.objects.get(user=sell_order.profile.user)
                                        profile_s.usd_amount += (new_buy_order.price*new_buy_order.quantity)

                                        profile_s.save()

                                        messages.success(request,
                                                         f'Sell order id: {sale_order._id}. || Status: {sale_order.status}.')
                                        messages.success(request,
                                                         f' The User who Sold has Received  successfully {new_buy_order.price}$ *{new_buy_order.quantity}.')
                                        messages.info(request,
                                                      'The bitcoin exchange has been totally executed! Congratulations!')



                                    elif sale_order.quantity < new_buy_order.quantity:
                                        actual_btc = profile_wallet.btc_amount

                                        new_buy_order.quantity -= sale_order.quantity
                                        new_buy_order.save()
                                        profile_wallet.btc_amount += sale_order.quantity
                                        profile_wallet.usd_amount-=(sale_order.price*sale_order.quantity)
                                        profile_wallet.save()
                                        messages.success(request,
                                                         f'Your Buy order id: {new_buy_order._id}. || Status: {new_buy_order.status}.')
                                        messages.success(request,
                                                         f'|| BTC before exchange: {actual_btc}; || BTC after exchange: {profile_wallet.btc_amount};')

                                        sale_order.status= 'close'
                                        sale_order.save()

                                        sell_order = Order.objects.get(_id=sale_order._id)
                                        profile_s = Profile.objects.get(user=sell_order.profile.user)
                                        profile_s.usd_amount += (sale_order.price*sale_order.quantity)

                                        profile_s.save()

                                        messages.success(request,
                                                         f'Sell order id: {sale_order._id}. || Status: {sale_order.status}.')
                                        messages.success(request,
                                                         f' The User who Sold has Received  successfully {sale_order.price} $ * {sale_order.quantity}.')
                                        messages.info(request,
                                                      'The bitcoin exchange has been totally executed! Congratulations!')


                                    else:
                                        return redirect('app:order')
                        return redirect('app:order')
                    else:
                        return redirect('app:order')
                else:
                    messages.error(request, 'Your balance is not enough.')
            else:
                messages.error(request, 'Order can not have negative values!')

        elif request.POST.get('sell'):
            form = Order_Form(request.POST or None)
            if form.is_valid():
                type='sell'
                status = 'open'
                price = form.cleaned_data.get('price')
                quantity = form.cleaned_data.get('quantity')
                profile_wallet = Profile.objects.get(user=request.user)

                if price <= 0.0:
                    messages.error(request, 'Cannot put a price lower than 0')
                    return redirect('app:order')
                if quantity <= 0.0:
                    messages.error(request, 'Cannot put a quantity lower than 0')
                    return redirect('app:order')

                if profile_wallet.btc_amount >= quantity:
                    profile_wallet.btc_amount -= quantity
                    profile_wallet.save()
                    # Order creation
                    new_sell_order = Order.objects.create(profile=profile_wallet,
                                                          type=type,
                                                          status=status,
                                                          price=price,
                                                          quantity=quantity,
                                                          modified=timezone.now())
                    messages.success(request,
                                     f'Your sales order of {new_sell_order.quantity} BTC for {new_sell_order.price}, {new_sell_order._id} is successfully added to the Order Book! || Status:{new_sell_order.status}')
                    # Order matching
                    if purchase_orders_list.exists():

                        for buy_open_order in purchase_orders_list:
                                if buy_open_order.price >= new_sell_order.price :

                                    messages.info(request, f'Search for the best purchase order')
                                    messages.info(request, f'Partner found! purchase order id:{buy_open_order._id}')
                                    messages.success(request,
                                                     f'He wants to buy {buy_open_order.quantity} BTC for {buy_open_order.price} $')
                                    messages.info(request, 'Start of the bitcoin exchange')
                                    if buy_open_order.quantity == new_sell_order.quantity:
                                        # Sell order can close.
                                        actual_usd = profile_wallet.usd_amount
                                        new_sell_order.price = buy_open_order.price
                                        new_sell_order.status = 'close'
                                        new_sell_order.save()
                                        profile_wallet.usd_amount += (new_sell_order.price * new_sell_order.quantity)
                                        profile_wallet.save()

                                        messages.success(request,
                                                         f'Sell order id: {new_sell_order._id}. || Status: {new_sell_order.status}.')
                                        messages.success(request,
                                                         f'|| USD before exchange: {actual_usd}; || USD after exchange: {profile_wallet.usd_amount};')

                                        profile_b = Profile.objects.get(user=buy_open_order.profile.user)
                                        profile_b.btc_amount += new_sell_order.quantity
                                        profile_b.usd_amount -= (buy_open_order.price * buy_open_order.quantity)
                                        profile_b.save()
                                        buy_open_order.status = 'close'
                                        buy_open_order.save()
                                        messages.success(request,
                                                         f'Buy order id: {buy_open_order._id}. || Status: {buy_open_order.status}.')
                                        messages.success(request, f'The User who purchased has Received  successfully {new_sell_order.quantity} BTC.')
                                        messages.info(request,
                                                      'The bitcoin exchange has been totally executed! Congratulations!')
                                        return redirect('app:order')

                                    elif buy_open_order.quantity > new_sell_order.quantity:
                                        actual_usd = profile_wallet.usd_amount
                                        new_sell_order.price = buy_open_order.price
                                        new_sell_order.status = 'close'
                                        new_sell_order.save()

                                        profile_wallet.usd_amount+=(new_sell_order.price*new_sell_order.quantity)
                                        profile_wallet.save()
                                        messages.success(request,
                                                         f'Sell order id: {new_sell_order._id}. || Status: {new_sell_order.status}.')
                                        messages.success(request,
                                                         f'|| USD before exchange: {actual_usd}; || USD after exchange: {profile_wallet.usd_amount};')

                                        buy_open_order.quantity -= new_sell_order.quantity
                                        buy_open_order.save()
                                        if buy_open_order.quantity == 0.00:
                                            buy_open_order.status="close"
                                            buy_open_order.save()

                                        profile_b = Profile.objects.get(user=buy_open_order.profile.user)
                                        profile_b.btc_amount += new_sell_order.quantity
                                        profile_b.usd_amount -= (buy_open_order.price*new_sell_order.quantity)
                                        profile_b.save()
                                        messages.success(request,
                                                         f'Buy order id: {buy_open_order._id}. || Status: {buy_open_order.status}.')
                                        messages.success(request,
                                                         f'The User who purchased has Received  successfully {new_sell_order.quantity} BTC.')
                                        messages.info(request,
                                                      'The bitcoin exchange has been totally executed! Congratulations!')


                                    elif buy_open_order.quantity < new_sell_order.quantity:
                                        actual_usd= profile_wallet.usd_amount
                                        new_sell_order.quantity -= buy_open_order.quantity
                                        new_sell_order.save()
                                        if new_sell_order.quantity==0.00:
                                            new_sell_order.status= 'close'
                                            new_sell_order.save()
                                        profile_wallet.usd_amount += (buy_open_order.price *buy_open_order.quantity)
                                        profile_wallet.save()

                                        messages.success(request,
                                                         f'Sell order id: {new_sell_order._id}. || Status: {new_sell_order.status}.')
                                        messages.success(request,
                                                         f'|| USD before exchange: {actual_usd}; || USD after exchange: {profile_wallet.usd_amount};')



                                        profile_b = Profile.objects.get(user=buy_open_order.profile.user)
                                        profile_b.btc_amount += buy_open_order.quantity
                                        profile_b.usd_amount -= (buy_open_order.price *buy_open_order.quantity)
                                        profile_b.save()
                                        buy_open_order.status = 'close'
                                        buy_open_order.save()
                                        messages.success(request,
                                                         f'Buy order id: {buy_open_order._id}. || Status: {buy_open_order.status}.')
                                        messages.success(request,
                                                         f'The User who purchased has Received  successfully {buy_open_order.quantity} BTC.')
                                        messages.info(request,
                                                      'The bitcoin exchange has been totally executed! Congratulations!')

                                    else:
                                        return redirect('app:order')
                        return redirect('app:order')
                    else:
                        return redirect('app:order')
                else:
                    messages.error(request, 'Your balance is not enough.')
            else:
                messages.error(request, 'Order can not have negative values!')

    form = Order_Form()
    profile_pocket= Profile.objects.get(user=request.user)
    return render(request, 'app/page_exchange.html', {'form': form,
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
    activeOrders = Order.objects.filter(status='open',type='buy').order_by('price')
    for order in activeOrders:
        response.append(
            {
                'Order ID': str(order._id),
                'Type': order.type,
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
    activeOrders =Order.objects.filter(status='open',type='sell').order_by('price')
    for order in activeOrders:
        response.append(
            {
                'Order ID': str(order._id),
                'Type':order.type,
                'Status': order.status,
                'created': order.created,
                'Price': order.price,
                'Quantity': order.quantity,
                'Modified':order.modified
            }
        )
    return JsonResponse(response, safe=False)

def delete_order_view(request,id):

    if request.method == 'POST':
        oll=Order.objects.filter(_id=ObjectId(id)).first()
        if oll.type=='buy' :
            p_order = Order.objects.filter(_id=ObjectId(id)).first()
            p_order.delete()
            messages.success(request, 'Your purchase order has been successfully deleted!')
            return redirect('app:order')
        elif oll.type=='sell':
            s_order = Order.objects.filter(_id=ObjectId(id)).first()
            profile_pocket = Profile.objects.get(user=s_order.profile.user)
            profile_pocket.btc_amount += s_order.quantity
            profile_pocket.save()
            s_order.delete()
            messages.success(request, 'Your sell order has been deleted successfully!')
            return redirect('app:order')

    return render(request, 'app/order_delete.html')

