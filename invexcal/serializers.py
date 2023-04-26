from rest_framework import serializers
from .models import *

class optionStrategyDupSerializers(serializers.ModelSerializer):
    class Meta:
        model = OptionStrategyDup
        fields = ('ticker', 'current_stock_price', 'risk_free_rate', 'days_from_today', 'default_interval', 'start_date', 'end_date', 'current_date', 'is_active', 'cash_in_hand', 'extra_cash')


class optionStrategyPositionSerializers(serializers.ModelSerializer):
    option_strategy_id = serializers.PrimaryKeyRelatedField(queryset= OptionStrategyDup.objects.all(), many=False)
  
    class Meta:
        model = OptionStrategyPositionDup
        fields = ('option_strategy_id','buysell', 'contract', 'callput', 'volatility', 'premium', 'debit_credit', 'initial_trade_cost', 'cash_required', 'initial_cash_req', 'strike')


class OptionStrategySpreadDup(serializers.ModelSerializer):
    class Meta:
        model = OptionStrategyPositionDup
        fields = ('cash_required', 'initial_cash_required')
