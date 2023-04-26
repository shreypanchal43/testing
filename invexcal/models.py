from django.db import models

# Create your models here.
isActive = [('non active', 'Non Active'), ('active', 'Active'), ('expired', 'Expired')]
buysell = [('but', 'Buy'), ('sell','Sell')]
callput = [('call', 'Call'), ('put', 'Put'), ('stock', 'Stock')]

class OptionStrategyDup(models.Model):
    created_by = models.IntegerField(null=True, default=None, blank=True)
    ticker = models.CharField(max_length=100, null=True, default=None, blank=True)
    parent_id = models.IntegerField(default=0, blank=True, null=True)
    is_active = models.CharField(max_length=30, choices=isActive, blank=True)
    current_stock_price = models.FloatField( blank=True)
    risk_free_rate = models.FloatField(null=True, blank=True)
    days_from_today = models.FloatField(null=True, blank=True)
    days_from_today_date = models.DateField(null=True, default=None, blank=True)
    start_date = models.CharField(null=True, max_length=20, blank=True)
    end_date = models.DateTimeField(blank=True, null=True)
    current_date = models.CharField(null=True, max_length=20, blank=True)
    default_interval = models.IntegerField(null=True, blank=True)                            
    calculation = models.JSONField(null=True, default=None, blank=True)
    cash = models.FloatField(null=True, default=0, blank=True)
    extra_cash = models.FloatField(null=True, default=0, blank=True)
    cash_in_hand = models.FloatField(null=True, default=0, blank=True)
    calc_itc = models.FloatField(null=True, default=0, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        db_table = 'option_strategy_dup'
        app_label = 'invexcal'


class OptionStrategyPositionDup(models.Model):
    # author = models.ForeignKey(Author, on_delete=models.CASCADE)
    option_strategy_id = models.ForeignKey(OptionStrategyDup,on_delete=models.CASCADE)
    row_id = models.CharField(max_length=10, blank=True, null=True)
    buysell = models.CharField(max_length=10, choices=buysell, blank=True)
    contract = models.IntegerField(blank=True, null=True)
    callput = models.CharField(max_length=10, choices=callput, blank=True)
    strike = models.FloatField(blank=True)
    # days_to_expire = models.IntegerField(blank=True)
    expiry_date = models.CharField(null=True, max_length=20)
    volatility = models.FloatField(blank=True)
    premium = models.FloatField(null=True, default=None,blank=True)
    debit_credit = models.FloatField(null=True, default=None,blank=True)
    initial_trade_cost = models.FloatField(null=True, default=None,blank=True)
    cash_required = models.FloatField(null=True, default=None,blank=True)
    initial_cash_req = models.FloatField(null=True, default=None,blank=True)
    graphcal = models.JSONField(null=True, default=None,blank=True)
    total = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'option_strategy_position_dup'
        app_label = 'invexcal'

class OptionStrategySpreadDup(models.Model):
    option_strategy_id = models.IntegerField()
    position_id_first = models.CharField(max_length=10)
    position_id_second = models.CharField(max_length=10)
    cash_required = models.FloatField(null=True, default=None)
    initial_cash_required = models.FloatField(null=True, default=None)
    spread_data = models.TextField(null=True, default=None)

    class Meta:
        db_table = 'option_strategy_spread_dup'
        app_label = 'invexcal'