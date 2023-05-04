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
    if int(x.real) >= 0:
        return p
    else:
        return 1 - p

@api_view(['POST','GET'])
def getData(request):
        ticker = request.data['ticker']
        dictt = {}
        final_dictt = {}
        l = []
#         strategy = OptionStrategyDup.objects.filter(ticker=ticker)
        price = requests.get('https://cp1.invexwealth.com/api/v2/company-profile-quote?symbol='+ticker)
            
        price = price.json()['data']['price']

        today = date.today()
        curr_date = today.strftime("%Y/%m/%d")
        data = '{"date":"'+curr_date+'","symbol":"'+ticker+'","low_strike":"1","high_strike":"500"}'

        expiry = requests.post('https://cp2.invexwealth.com/option_chain', data=data)

        exp = list(expiry.json()['data'].keys())
        dta = {i: list(expiry.json()['data'][i]["Strike"].values()) for i in expiry.json()['data'].keys()}

        call = {i: list(expiry.json()['data'][i]["iVMean"].values()) for i in expiry.json()['data'].keys()}
        strike_mean = {}
        Strike_Mean = {}

        call_put = {}

        for i in expiry.json()['data'].keys():
            Strike = expiry.json()['data'][i]["Strike"].values()
            IVmean = expiry.json()['data'][i]["IVMean"].values()
            ivmean = expiry.json()['data'][i]["iVMean"].values()
        
        for i,j,n in zip(Strike,ivmean,IVmean):
            strike_mean[int(i)] = j
            Strike_Mean[int(i)] = n
        
        expiry_dict_put = {i: strike_mean for i in exp}
        expiry_dict_call = {i: Strike_Mean for i in exp}
        call_put['put'] = expiry_dict_put
        call_put['call'] = expiry_dict_call

        dicttt = {'ticker':ticker, 'expiry':exp, 'strike':dta, 'price':price}
        if OptionStrategyDup.objects.filter(ticker=ticker).exists():
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
            final_dictt['expiry_strike_vol'] = call_put
            final_dictt['expire_list'] = dicttt
            return Response(final_dictt)
        
        else:
            final_dictt = {}
            final_dictt['expiry_strike_vol'] = call_put
            final_dictt['expire_list'] = dicttt
            return Response(final_dictt)

@api_view(['POST','GET'])
def calculate(request):
    static = request.data['static']
    dynamic = request.data['dynamic']
    
    s_id = static['id']
    current_stock_price = static['current_stock_price']
    risk_free_rate = static['risk_free_rate']
    interval = static['interval']
    start_date = static['start_date']
    is_active = static['is_active']

    date_list = []
    for i in dynamic:
        date_list.append(i['expiry_date'])
    min_date = min(date_list, key=lambda x: datetime.strptime(x, '%m/%d/%Y'))

    startdate_object = datetime.strptime(start_date, '%d/%m/%Y').date()
    date1 = date.today()
    date11 = datetime.strptime(min_date, '%m/%d/%Y').date()
    timedelta = date11 - date1
    timed = int(timedelta.days) - 0.01
    
    prm = []
    debitcredit = []
    final_data = {}
    prem_dc = []
    for i in dynamic:
        context = {}
        id = i['id']
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
        time = (daystoexp - timed)/365
        if callput_flag == 's':
            premium = current_stock_price
        else:
            try:
                premium = BlackScholes(callput_flag, current_stock_price, strike, time, risk_free_rate, volatility)
            except:
                s = 'Enter valid input'
                return Response(s)
        prm.append(premium)
        dbc = premium*contract*100
        debitcredit.append(dbc)
        
        # context['buysell'] = buysell
        # context['expiry'] = expiry_date
        # context['contract'] = contract
        # context['callput'] = callput
        # context['volatility'] = volatility
        context['premium'] = premium
        context['debit_credit'] = dbc
        # context['strike'] = strike
        prem_dc.append(context)
    final_data['calculated_data'] = prem_dc
    final_data['end_date'] = min_date
    return Response(final_data)

def calc(static, dynamic):
    id = static['id']
    current_stock_price = static['current_stock_price']
    risk_free_rate = static['risk_free_rate']
    interval = static['interval']
    start_date = static['start_date']
    is_active = static['is_active']

    date_list = []
    for i in dynamic:
        date_list.append(i['expiry_date'])

    min_date = min(date_list, key=lambda x: datetime.strptime(x, '%m/%d/%Y'))


    startdate_object = datetime.strptime(start_date, '%d/%m/%Y').date()
    date1 = date.today()
    date11 = datetime.strptime(min_date, '%m/%d/%Y').date()
    timedelta = date11 - date1
    timed = int(timedelta.days) - 0.01
    prm = []
    debitcredit = []
    final_data = {}
    
    for i in dynamic:
        context = {}
        id = i['id']
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
        time = (daystoexp - timed)/365
        if callput_flag == 's':
            premium = current_stock_price
        else:
            try:
                premium = BlackScholes(callput_flag, current_stock_price, strike, time, risk_free_rate, volatility)
            except:
                s = 'Enter valid input'
                return Response(s)
        prm.append(premium)
        dbc = premium*contract*100
        debitcredit.append(dbc)
        
        # context['buysell'] = buysell
        # context['expiry'] = expiry_date
        # context['contract'] = contract
        # context['callput'] = callput
        # context['volatility'] = volatility
        context['premium'] = premium
        context['debit_credit'] = dbc
        # context['strike'] = strike
        final_data[id] = context
    
    return final_data

def save_new_data(static,dynamic):
    # data = calc(static, dynamic)
    id = static.get('id')
    ticker = static.get('ticker')
    current_stock_price = static.get('current_stock_price')
    risk_free_rate = static.get('risk_free_rate')
    days_from_today = static.get('days_from_today')
    interval = static.get('interval')
    start_date = static.get('start_date')
    dupdict = {"id":id,"ticker":ticker,"current_stock_price":current_stock_price, "risk_free_rate":risk_free_rate, "days_from_today":days_from_today,
                "interval":interval, "start_date":start_date}

    serializerdup = optionStrategyDupSerializers(data=dupdict)
    
    if serializerdup.is_valid():
        obj = serializerdup.save()
    
    p = obj.id
    final_output_dict = {}
    final_output_list = []

    # id_status_list = OptionStrategyDup.objects.values_list('id')
    # p = id_status_list[len(id_status_list)-1][0]
    
    for i in dynamic:
        dynamic_output = {}
        subid = i.get('id')
        buysell = i.get('buysell')
        contract = i.get('contract')
        callput = i.get('callput')
        strike = i.get('strike')
        expiry_date = i.get('expiry_date')
        volatility = i.get('volatility')
        premium = i.get('premium')
        debit_credit = i.get('debit_credit')

        #     debit_credit = i.get('debit_credit')

        positiondict = {"buysell":buysell, "contract":contract, "callput":callput, "strike":strike, "expiry_date":expiry_date, "volatility":volatility, "premium":premium, "debit_credit":debit_credit}
        positiondict["option_strategy_id"] = p
        serializerposition = optionStrategyPositionSerializers(data=positiondict)

        serializerposition.is_valid(raise_exception=True)
        if serializerposition.is_valid():
            obj1 = serializerposition.save()

        did = obj1.id
        dynamic_output['id'] = did
        dynamic_output['premium'] = premium
        dynamic_output['debit_credit'] = debit_credit

        final_output_list.append(dynamic_output)

    final_output_dict['Dynamic'] = final_output_list

    final_output_dict['Static'] = {"id":p, "ticker":ticker,"current_stock_price":current_stock_price, "risk_free_rate":risk_free_rate, "days_from_today":days_from_today,
                 "interval":interval, "start_date":start_date}
    
    # print(final_output_dict)
    return final_output_dict
    

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
            position =  OptionStrategyPositionDup.objects.get(id=in_id)
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
        dictt = save_new_data(static,dynamic)
    else:
        update_data(static,dynamic,id)
    return Response({"Message":"Data saved successfully","status":True, "Data":dictt})

@api_view(['POST','GET'])
def getVol(request):
    context = {}
    ticker = request.data['ticker']
    call_put = request.data['call_put']
    exp = request.data['expiry_date']
    strike = request.data['strike']
    today = date.today()
    curr_date = today.strftime("%Y/%m/%d")
    data = '{"date":"'+curr_date+'","symbol":"'+ticker+'","low_strike":"1","high_strike":"500"}'
    expiry = requests.post('https://cp2.invexwealth.com/option_chain', data=data)
    exp_data = expiry.json()
    data = exp_data['data']

    if exp in data:
        d = data[exp]

    if call_put == 'call':
        key = [v for v in d['Strike'] if d['Strike'][v] == strike][0]
        vol = d['IVMean'][key]
        
    elif call_put == 'put':
        key = [v for v in d['strike'] if d['strike'][v] == strike]
        vol = d['ivMean']
        
    else:
        return Response("Please enter Call or Put")
    context["expiry_date"] = exp
    context["strike"] = strike
    context['iv'] = vol
    return Response(context)