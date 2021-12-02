from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm,UserEditForm,LoginForm
from django.contrib.auth import login,authenticate
from django.contrib import messages
from app.models import Profile,PurchaseOrder,SaleOrder
from app.market import Report
from django.utils import timezone
import random

def getIpAdd(request):
    try:
        x_forward = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forward:
            ip = x_forward.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
    except:
        ip = ""
    return ip

@login_required()
def ip_control_view(request):

    return render(request, 'accounts/ip_control.html', )

def getIpAdd(request):
    try:
        x_forward = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forward:
            ip = x_forward.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
    except:
        ip = ""
    return ip

def login_view(request):
    impactReport = Report()  # ad impactReport gli assegno la classe Report()
    currency = impactReport.get_data()
    ip_address = getIpAdd(request)
    initial_data = {
        'ip_address': ip_address,
    }
    form = LoginForm(request.POST or None)
    if form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(request, username=username, password=password)
        if user != None:
            login(request, user)
            try:
                user_info = Profile.objects.get(user=user)
                user_info.last_login = timezone.now()
            except:
                user_info = Profile.objects.create(user=user)
                user_info.last_login = timezone.now()
            user_info.save()
            ip_address = getIpAdd(request)
            if ip_address != user_info.ip_address:
                user_info.ip_address = ip_address
                user_info.save()
                return redirect(f"accounts:ip-control")

            else:
                return redirect('accounts:profile',user.pk)
    else:
        form = LoginForm(initial=initial_data)
    return render(request, 'accounts/login.html',{'form': form,'currency':currency})





def register_view(request):
    impactReport = Report()  # ad impactReport gli assegno la classe Report()
    currency = impactReport.get_data()
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db() #stiamo andando a ricaricare l'istanza del profilo che è stata generata dal signals

            newUser = Profile(user=user)
            newUser.btc_amount = int(random.uniform(1, 10))
            newUser.btc_balance= newUser.btc_amount
            newUser.usd_amount= int(random.uniform(100000, 1000000))
            newUser.usd_balance= newUser.usd_amount
            newUser.ip_address=getIpAdd(request)
            newUser.last_login=timezone.now()
            newUser.save()



            username = form.cleaned_data.get('username')
            row_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username,password=row_password)
            login(request,user)
            return redirect('accounts:profile',user.pk)
    else:
        form = RegistrationForm()

    return render(request,'accounts/registration.html',{'form': form,'currency':currency})
@login_required()
def profile(request,id):
    user_profile = get_object_or_404(Profile, user_id=id)
    profile_pocket = Profile.objects.get(user=request.user)
    my_purchase_orders_list = PurchaseOrder.objects.filter(profile=user_profile).order_by('price')
    my_sale_orders_list = SaleOrder.objects.filter(profile=user_profile).order_by('price')
    impactReport = Report()  # ad impactReport gli assegno la classe Report()
    currency = impactReport.get_data()

    mp_list=PurchaseOrder.objects.filter(profile=user_profile,status='close').order_by('price')
    sm_list=SaleOrder.objects.filter(profile=user_profile,status='close').order_by('price')
    profit_buy=[]
    profit_sell=[]
    for purchase_list in mp_list:
        depth = purchase_list.quantity * purchase_list.price
        profit_buy.append(depth)
    for sale_list in sm_list:
        depth = sale_list.quantity * sale_list.price
        profit_sell.append(depth)
    profile_pocket.profit = sum(profit_sell) - sum(profit_buy)
    profile_pocket.save()

    return render(request, 'accounts/profile.html', {'user_profile': user_profile,'user_wallet': profile_pocket,'my_purchase_orders_list':my_purchase_orders_list,'my_sale_orders_list':my_sale_orders_list,'currency':currency})

@login_required
def edit_profile(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)

        if user_form.is_valid() :
            user_form.save()

            messages.success(request,'Your profile has been successfully edited')
            return redirect('accounts:profile', request.user.pk)
        else:
            messages.error(request,'The data entered is not valid',extra_tags='danger')
    else:
        user_form = UserEditForm(instance=request.user)

    return render(request,'accounts/edit.html',
                  {'user_form': user_form})
