from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    course = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    amount = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ('id', 'course', 'amount', 'currency', 'status', 'created_at')

    def get_amount(self, obj):
        return f'{obj.amount:.2f}'
