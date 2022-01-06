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
    purchase_orders_list = Order.objects.filter(status='open',type='buy').order_by('created')
    sale_orders_list = Order.objects.filter(status='open',type='sell').order_by('created')
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
                limit_min = form.cleaned_data.get('limit')
                profile_wallet = Profile.objects.get(user=request.user)

                if price <=0.0:
                    messages.error(request, 'Cannot put a price lower than 0')
                    return redirect('app:order')
                if quantity <= 0.0:
                    messages.error(request, 'Cannot put a quantity lower than 0')
                    return redirect('app:order')
                if limit_min <= 0.0:
                    messages.error(request, 'Cannot put a limit lower than 0')
                    return redirect('app:order')
                if limit_min > price:
                    messages.error(request, 'Cannot put a limit superior than price')
                    return redirect('app:order')


                if profile_wallet.usd_amount >= price:
                    profile_wallet.usd_amount -=price
                    profile_wallet.save()
                    # Order creation
                    new_buy_order = Order.objects.create(profile=profile_wallet,
                                                         status=status,
                                                         type=type,
                                                         price=price,
                                                         quantity=quantity,
                                                         limit=limit_min,
                                                         modified=timezone.now())
                    messages.success(request, f'Your  purchase order of {new_buy_order.quantity} BTC for {new_buy_order.price} ,{new_buy_order._id}  is successfully added to the Order Book! || Status: {new_buy_order.status}')
                    # Order matching
                    if sale_orders_list.exists():
                        max_order_btc=None
                        for sale_order in sale_orders_list:
                            if new_buy_order.profile != sale_order.profile:
                                if sale_order.price <= new_buy_order.price and sale_order.price>=new_buy_order.limit:
                                    if new_buy_order.price<=sale_order.limit:
                                        if max_order_btc == None or ( sale_order.limit>= max_order_btc.quantity ) :
                                            max_order_btc = sale_order



                        if max_order_btc!=None:
                            # Modifying orders.
                            messages.info(request, f'Search for the best sales order')
                            messages.info(request, f'Partner found! sale order id:{max_order_btc._id}')
                            messages.success(request,
                                             f'He wants to sell {max_order_btc.quantity} BTC for {max_order_btc.price} $')
                            messages.info(request, 'Start of the bitcoin exchange')

                            if max_order_btc.quantity == new_buy_order.quantity:

                                actual_btc = profile_wallet.btc_amount

                                new_buy_order.quantity = max_order_btc.quantity
                                new_buy_order.status='close'
                                new_buy_order.save()
                                profile_wallet.btc_amount+=max_order_btc.quantity
                                profile_wallet.save()

                                messages.success(request,f'Your Buy order id: {new_buy_order._id}. || Status: {new_buy_order.status}.')
                                messages.success(request, f'|| BTC before exchange: {actual_btc}; || BTC after exchange: {profile_wallet.btc_amount};')

                                # Sell order can close.
                                sell_order = Order.objects.get(_id=max_order_btc._id)
                                profile_s= Profile.objects.get(user= sell_order.profile.user)
                                profile_s.usd_amount+=new_buy_order.price

                                profile_s.save()
                                max_order_btc.status = 'close'
                                max_order_btc.save()

                                messages.success(request, f'Sell order id: {max_order_btc._id}. || Status: {max_order_btc.status}.')
                                messages.success(request, f' The User who Sold has Received  successfully {new_buy_order.price} $.')
                                messages.info(request, 'The bitcoin exchange has been totally executed! Congratulations!')
                                return redirect('app:order')
                            elif max_order_btc.quantity > new_buy_order.quantity :
                                actual_btc = profile_wallet.btc_amount

                                new_buy_order.price = max_order_btc.price
                                new_buy_order.status = 'close'
                                new_buy_order.save()
                                profile_wallet.btc_amount+=new_buy_order.quantity
                                profile_wallet.save()
                                messages.success(request,
                                                 f'Your Buy order id: {new_buy_order._id}. || Status: {new_buy_order.status}.')
                                messages.success(request,
                                                 f'|| BTC before exchange: {actual_btc}; || BTC after exchange: {profile_wallet.btc_amount};')

                                max_order_btc.quantity-=new_buy_order.quantity
                                max_order_btc.save()

                                sell_order = Order.objects.get(_id=max_order_btc._id)
                                profile_s = Profile.objects.get(user=sell_order.profile.user)
                                profile_s.usd_amount += new_buy_order.price

                                profile_s.save()

                                messages.success(request,
                                                 f'Sell order id: {max_order_btc._id}. || Status: {max_order_btc.status}.')
                                messages.success(request,
                                                 f' The User who Sold has Received  successfully {new_buy_order.price} $.')
                                messages.info(request,
                                              'The bitcoin exchange has been totally executed! Congratulations!')


                            elif max_order_btc.quantity < new_buy_order.quantity:
                                actual_btc = profile_wallet.btc_amount

                                new_buy_order.quantity -= max_order_btc.quantity
                                new_buy_order.save()
                                profile_wallet.btc_amount += max_order_btc.quantity
                                profile_wallet.save()
                                messages.success(request,
                                                 f'Your Buy order id: {new_buy_order._id}. || Status: {new_buy_order.status}.')
                                messages.success(request,
                                                 f'|| BTC before exchange: {actual_btc}; || BTC after exchange: {profile_wallet.btc_amount};')

                                max_order_btc.status= 'close'
                                max_order_btc.save()

                                sell_order = Order.objects.get(_id=max_order_btc._id)
                                profile_s = Profile.objects.get(user=sell_order.profile.user)
                                profile_s.usd_amount += max_order_btc.price

                                profile_s.save()

                                messages.success(request,
                                                 f'Sell order id: {max_order_btc._id}. || Status: {max_order_btc.status}.')
                                messages.success(request,
                                                 f' The User who Sold has Received  successfully {max_order_btc.price} $.')
                                messages.info(request,
                                              'The bitcoin exchange has been totally executed! Congratulations!')

                            else:
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
                limit_max = form.cleaned_data.get('limit')
                profile_wallet = Profile.objects.get(user=request.user)

                if price <= 0.0:
                    messages.error(request, 'Cannot put a price lower than 0')
                    return redirect('app:order')
                if quantity <= 0.0:
                    messages.error(request, 'Cannot put a quantity lower than 0')
                    return redirect('app:order')
                if limit_max <= 0.0:
                    messages.error(request, 'Cannot put a quantity lower than 0')
                    return redirect('app:order')
                if limit_max < price:
                    messages.error(request, 'Cannot put a limit lower than price')
                    return redirect('app:order')

                if profile_wallet.btc_amount >= quantity:
                    profile_wallet.btc_amount -= quantity
                    profile_wallet.save()
                    # Order creation
                    new_sell_order = Order.objects.create(profile=profile_wallet,
                                                          type=type,
                                                          status=status,
                                                          limit=limit_max,
                                                          price=price,
                                                          quantity=quantity,
                                                          modified=timezone.now())
                    messages.success(request,
                                     f'Your sales order of {new_sell_order.quantity} BTC for {new_sell_order.price}, {new_sell_order._id} is successfully added to the Order Book! || Status:{new_sell_order.status}')
                    # Order matching
                    if purchase_orders_list.exists():

                        max_value = None
                        for buy_open_order in purchase_orders_list:
                            if buy_open_order.profile != new_sell_order.profile:
                                if buy_open_order.price >= new_sell_order.price  and buy_open_order.price<=new_sell_order.limit:
                                    if new_sell_order.price >= buy_open_order.limit:
                                        if max_value == None or (buy_open_order.price >= max_value.price ):
                                            max_value = buy_open_order

                        if max_value != None:
                            messages.info(request, f'Search for the best purchase order')
                            messages.info(request, f'Partner found! purchase order id:{max_value._id}')
                            messages.success(request,
                                             f'He wants to buy {max_value.quantity} BTC for {max_value.price} $')
                            messages.info(request, 'Start of the bitcoin exchange')
                            if max_value.quantity == new_sell_order.quantity:
                                # Sell order can close.
                                actual_usd = profile_wallet.usd_amount
                                new_sell_order.price = max_value.price
                                new_sell_order.status = 'close'
                                new_sell_order.save()
                                profile_wallet.usd_amount += max_value.price
                                profile_wallet.save()

                                messages.success(request,
                                                 f'Sell order id: {new_sell_order._id}. || Status: {new_sell_order.status}.')
                                messages.success(request,
                                                 f'|| USD before exchange: {actual_usd}; || USD after exchange: {profile_wallet.usd_amount};')

                                profile_b = Profile.objects.get(user=max_value.profile.user)
                                profile_b.btc_amount += round(new_sell_order.quantity)
                                profile_b.save()
                                max_value.status = 'close'
                                max_value.save()
                                messages.success(request,
                                                 f'Buy order id: {max_value._id}. || Status: {max_value.status}.')
                                messages.success(request, f'The User who purchased has Received  successfully {new_sell_order.quantity} BTC.')
                                messages.info(request,
                                              'The bitcoin exchange has been totally executed! Congratulations!')
                                return redirect('app:order')
                            elif max_value.quantity > new_sell_order.quantity:
                                actual_usd = profile_wallet.usd_amount
                                new_sell_order.price = max_value.price
                                new_sell_order.status = 'close'
                                new_sell_order.save()

                                profile_wallet.usd_amount+=new_sell_order.price
                                profile_wallet.save()
                                messages.success(request,
                                                 f'Sell order id: {new_sell_order._id}. || Status: {new_sell_order.status}.')
                                messages.success(request,
                                                 f'|| USD before exchange: {actual_usd}; || USD after exchange: {profile_wallet.usd_amount};')

                                max_value.quantity-=new_sell_order.quantity
                                max_value.save()
                                if max_value.quantity== 0.00:
                                    max_value.status="close"
                                    max_value.save()

                                profile_b = Profile.objects.get(user=max_value.profile.user)
                                profile_b.btc_amount += new_sell_order.quantity
                                profile_b.save()
                                messages.success(request,
                                                 f'Buy order id: {max_value._id}. || Status: {max_value.status}.')
                                messages.success(request,
                                                 f'The User who purchased has Received  successfully {new_sell_order.quantity} BTC.')
                                messages.info(request,
                                              'The bitcoin exchange has been totally executed! Congratulations!')

                            elif max_value.quantity < new_sell_order.quantity:
                                actual_usd= profile_wallet.usd_amount
                                new_sell_order.quantity-=max_value.quantity
                                new_sell_order.save()
                                if new_sell_order.quantity==0.00:
                                    new_sell_order.status= 'close'
                                    new_sell_order.save()
                                profile_wallet.usd_amount+=new_sell_order.price
                                profile_wallet.save()

                                messages.success(request,
                                                 f'Sell order id: {new_sell_order._id}. || Status: {new_sell_order.status}.')
                                messages.success(request,
                                                 f'|| USD before exchange: {actual_usd}; || USD after exchange: {profile_wallet.usd_amount};')



                                profile_b = Profile.objects.get(user=max_value.profile.user)
                                profile_b.btc_amount += max_value.quantity
                                profile_b.save()
                                max_value.status = 'close'
                                max_value.save()
                                messages.success(request,
                                                 f'Buy order id: {max_value._id}. || Status: {max_value.status}.')
                                messages.success(request,
                                                 f'The User who purchased has Received  successfully {max_value.quantity} BTC.')
                                messages.info(request,
                                              'The bitcoin exchange has been totally executed! Congratulations!')







                            else:
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
            profile_pocket = Profile.objects.get(user=p_order.profile.user)
            profile_pocket.usd_amount += p_order.price
            profile_pocket.save()
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

