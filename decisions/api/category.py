from rest_framework import viewsets

from decisions.models import Function

from .base import DataModelSerializer


class FunctionSerializer(DataModelSerializer):
    class Meta:
        model = Function
        fields = '__all__'


class FunctionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Function.objects.select_related('data_source', 'parent', 'parent__parent', 'parent__parent__parent')
    serializer_class = FunctionSerializer
