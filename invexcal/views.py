from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import *
from .models import *
from rest_framework import status
from datetime import date, datetime
import math
import requests


def BlackScholes(call_put_flag, S, X, T, r, v):
    r = r / 100
    v = v / 100
    d1 = (math.log(S / X) + (r + pow(v, 2) / 2) * T) / (v * pow(T, 0.5))
    d2 = d1 - v * pow(T, 0.5)
    if call_put_flag == 'c':
        return S * CND(d1) - X * math.exp(-r * T) * CND(d2)
    else:
        return X * math.exp(-r * T) * CND(-d2) - S * CND(-d1)
    
def CND(x):
    Pi = 3.141592653589793238
    a1 = 0.319381530
    a2 = -0.356563782
    a3 = 1.781477937
    a4 = -1.821255978
    a5 = 1.330274429
    L = abs(x)
    k = 1 / (1 + 0.2316419 * L)
    p = 1 - 1 / pow(2 * Pi, 0.5) * math.exp(-pow(L, 2) / 2) * (
            a1 * k + a2 * pow(k, 2) + a3 * pow(k, 3) + a4 * pow(k, 4) + a5 * pow(k, 5))
    if x >= 0:
        return p
    else:
        return 1 - p

@api_view(['POST','GET'])
def getData(request):
        ticker = request.data['ticker']
        dictt = {}
        final_dictt = {}
        l = []
        strategy = OptionStrategyDup.objects.filter(ticker=ticker)
        if strategy != []:
            data = OptionStrategyDup.objects.get(ticker=ticker)
            ids = data.id
            dictt['id'] = data.id
            dictt['ticker'] = data.ticker
            dictt['current_stock_price'] = data.current_stock_price
            dictt['risk_free_rate'] = data.risk_free_rate
            dictt['days_from_today'] = data.days_from_today
            dictt['default_interval'] = data.default_interval
            dictt['start_date'] = data.start_date
            
            
            for d in OptionStrategyPositionDup.objects.filter(option_strategy_id=ids):
                dictt1 = {}
                dictt1['subid'] = d.id
                dictt1['buysell'] = d.buysell
                dictt1['expiry'] = d.expiry_date
                dictt1['contract'] = d.contract
                dictt1['callput'] = d.callput
                dictt1['volatility'] = d.volatility
                dictt1['premium'] = d.premium
                dictt1['debit_credit'] = d.debit_credit
                dictt1['strike'] = d.strike 

                l.append(dictt1)
            final_dictt['static'] = dictt
            final_dictt['dynamic'] = l
            return Response(final_dictt)
        
        else:
            

            # price = requests.get('https://cp1.invexwealth.com/api/v2/company-profile-quote?symbol='+ticker)
            
            # price = price.json()['data']['price']
            data = '{"date":"2023/04/06","symbol":"'+ticker+'","low_strike":"1","high_strike":"100"}'
            expiry = requests.post('https://cp2.invexwealth.com/option_chain', data=data)
            
            exp = list(expiry.json()['data'].keys())
            dta = {i: list(expiry.json()['data'][i]["Strike"].values()) for i in expiry.json()['data'].keys()}
            dictt = {'ticker':ticker, 'expiry':exp, 'strike':dta}
            print(exp)

            # frm = OptionStrategyDupForm(dictt)
            # # frm1 = OptionStrategyPositionDupForm(dates=((a,a) for a in exp))
            # frm1 = OptionStrategyPositionDupFormSet(form_kwargs={"dates":((a,a) for a in exp)})
            
            # context['form'] = frm
            # context['formsets'] = frm1
            # context['strike'] = json.dumps(dta)

            # request.session['expiry_date'] = exp
            # request.session['strike'] = json.dumps(dta)
            # request.session['exp'] = exp
            # request.session['dta'] = dta

            return Response(dictt)

@api_view(['POST','GET'])
def calculate(request):
    static = request.data['static']
    current_stock_price = static['current_stock_price']
    risk_free_rate = static['risk_free_rate']
    days_from_today = static['days_from_today']
    interval = static['interval']
    start_date = static['start_date']

    startdate_object = datetime.strptime(start_date, '%d/%m/%Y').date()
    
    dynamic = request.data['dynamic']
    prm = []
    debitcredit = []
    final_data = []
    for i in dynamic:
        context = {}
        buysell = i['buysell']
        contract = i['contract']
        callput = i['callput']
        strike = i['strike']
        expiry_date = i['expiry_date']
        volatility = i['volatility']

        expdate_object = datetime.strptime(expiry_date, '%m/%d/%Y').date()

        daystoexp = (expdate_object - startdate_object).days

        if callput == 'call':
            callput_flag = 'c'
        elif callput == 'put':
            callput_flag = 'p'
        else:
            callput_flag = 's'

        time = (daystoexp - days_from_today)/365
                # print(formset[-1])

        if callput_flag == 's':
            premium = current_stock_price
        else:
            premium = BlackScholes(callput_flag, current_stock_price, strike, time, risk_free_rate, volatility)
        prm.append(premium)

        dbc = premium*contract*100
        debitcredit.append(dbc)

        context['buysell'] = buysell
        context['expiry'] = expiry_date
        context['contract'] = contract
        context['callput'] = callput
        context['volatility'] = volatility
        context['premium'] = premium
        context['debit_credit'] = dbc
        context['strike'] = strike 

        final_data.append(context)

    s = 'redirect'
    return Response(final_data)


def save_new_data(static,dynamic):
    ticker = static.get('ticker')
    current_stock_price = static.get('current_stock_price')
    risk_free_rate = static.get('risk_free_rate')
    days_from_today = static.get('days_from_today')
    interval = static.get('interval')
    start_date = static.get('start_date')


    dupdict = {"ticker":ticker,"current_stock_price":current_stock_price, "risk_free_rate":risk_free_rate, "days_from_today":days_from_today,
                "interval":interval, "start_date":start_date}


    serializerdup = optionStrategyDupSerializers(data=dupdict)
    
    if serializerdup.is_valid():
        serializerdup.save()

    id_status_list = OptionStrategyDup.objects.values_list('id')
    p = id_status_list[len(id_status_list)-1][0]

    for i in dynamic:
        buysell = i.get('buysell')
        contract = i.get('contract')
        callput = i.get('callput')
        strike = i.get('strike')
        expiry_date = i.get('expiry_date')
        volatility = i.get('volatility')
        premium = i.get('premium')
        debit_credit = i.get('debit_credit')

        positiondict = {"buysell":buysell, "contract":contract, "callput":callput, "strike":strike, "expiry_date":expiry_date, "volatility":volatility, "premium":premium, "debit_credit":debit_credit}
        positiondict["option_strategy_id"] = p
        serializerposition = optionStrategyPositionSerializers(data=positiondict)

        serializerposition.is_valid(raise_exception=True)
        if serializerposition.is_valid():
            serializerposition.save()
    return Response({"Message":"Data saved successfully","status":True})

def update_data(static,dynamic,id):
    current_stock_price = static.get('current_stock_price')
    risk_free_rate = static.get('risk_free_rate')
    days_from_today = static.get('days_from_today')
    interval = static.get('interval')
    start_date = static.get('start_date')

    strategy = OptionStrategyDup.objects.get(pk=id)
    strategy.current_stock_price = current_stock_price
    strategy.risk_free_rate = risk_free_rate
    strategy.days_from_today = days_from_today
    strategy.interval = interval
    strategy.start_date = start_date
    strategy.save()

    for i in dynamic:
        buysell = i.get('buysell')
        contract = i.get('contract')
        callput = i.get('callput')
        strike = i.get('strike')
        expiry_date = i.get('expiry_date')
        volatility = i.get('volatility')
        premium = i.get('premium')
        debit_credit = i.get('debit_credit')
        in_id = i.get('id')

        if in_id == None:
            positiondict = {"buysell":buysell, "contract":contract, "callput":callput, "strike":strike, "expiry_date":expiry_date, "volatility":volatility, "premium":premium, "debit_credit":debit_credit}
            positiondict["option_strategy_id"] = id
            serializerposition = optionStrategyPositionSerializers(data=positiondict)
            serializerposition.is_valid(raise_exception=True)
            if serializerposition.is_valid():
                serializerposition.save()

        else:
            position =  OptionStrategyPositionDup.objects.get(pk=in_id)
            position.buysell = buysell
            position.contract = contract
            position.callput = callput
            position.strike = strike
            position.expiry_date = expiry_date
            position.volatility = volatility
            position.premium = premium
            position.debit_credit = debit_credit
            position.save()
    



@api_view(['POST','GET'])
def save(request):
    static = request.data['static']
    dynamic = request.data['dynamic']
    id = static.get('id')

    if id == None:
        save_new_data(static,dynamic)
    else:
        update_data(static,dynamic,id)



# def update(request,pk):
    

# Create your views here.
# @api_view(['POST','GET'])
# def optionDup(request):
#     total = 0
#     current_stock_price = request.data['current_stock_price']
#     risk_free_rate = request.data['risk_free_rate']
#     days_from_today = request.data['days_from_today']
#     interval = request.data['interval']
#     start_date = request.data['start_date']

#     buysell = request.data['buysell']
#     contract = request.data['contract']
#     callput = request.data['callput']
#     strike = request.data['strike']
#     expiry_date = request.data['expiry_date']
#     volatility = request.data['volatility']

#     startdate_object = datetime.strptime(start_date, '%d/%m/%Y').date()
#     expdate_object = datetime.strptime(expiry_date, '%m/%d/%Y').date()
    
#     daystoexp = (expdate_object - startdate_object).days

#     if callput == 'call':
#         callput_flag = 'c'
#     elif callput == 'put':
#         callput_flag = 'p'
#     else:
#         callput_flag = 's'

#     time = (daystoexp - days_from_today)/365
#                 # print(formset[-1])

#     if callput_flag == 's':
#         premium = current_stock_price
#     else:
#         premium = BlackScholes(callput_flag, current_stock_price, strike, time, risk_free_rate, volatility)

#     dbc = premium*contract*100

#     total = total + dbc

#     dupdict = {"current_stock_price":current_stock_price, "risk_free_rate":risk_free_rate, "days_from_today":days_from_today,
#                "interval":interval, "start_date":start_date}
    
#     positiondict = {"buysell":buysell, "contract":contract, "callput":callput, "strike":strike, "expiry_date":expiry_date, "volatility":volatility, "premium":premium, "debit_credit":dbc, "total":total}

#     serializerdup = optionStrategyDupSerializers(data=dupdict)
 
#     if serializerdup.is_valid():
#         serializerdup.save()
    
#     id_status_list = OptionStrategyDup.objects.values_list('id')
#     p = id_status_list[len(id_status_list)-1][0]
  
#     positiondict["option_strategy_id"] = p
#     serializerposition = optionStrategyPositionSerializers(data=positiondict)

#     serializerposition.is_valid(raise_exception=True)
#     if serializerposition.is_valid():
#         print("in")
#         serializerposition.save()
#         return Response(serializerposition.data, status=status.HTTP_201_CREATED)
    
#     context = {}
#     context['dup'] = serializerdup.data
#     context['position'] = serializerposition.data
#     return Response(context)    