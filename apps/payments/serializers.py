# apps/payments/serializers.py

from rest_framework import serializers
from .models import Transaction, PremiumSubscription, DownloadCredit

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_type', 'amount', 'currency', 
            'status', 'description', 'created_at', 'approved_at'
        ]
        read_only_fields = ['id', 'created_at', 'approved_at']

