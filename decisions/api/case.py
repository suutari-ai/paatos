from django_filters import CharFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, serializers, viewsets

from decisions.models import Action, Case, CaseGeometry

from .base import BaseFilter, DataModelSerializer


class CaseGeometrySerializer(DataModelSerializer):

    class Meta:
        model = CaseGeometry
        exclude = ('url', 'id')


class CaseFilter(BaseFilter):
    function = CharFilter(name='function_id')

    class Meta:
        model = Case
        fields = BaseFilter.Meta.fields + ('function', 'register_id')


class CaseSerializer(DataModelSerializer):
    actions = serializers.HyperlinkedRelatedField(queryset=Action.objects.all(), many=True, view_name='action-detail')
    geometries = CaseGeometrySerializer(many=True, read_only=True)

    class Meta:
        model = Case
        fields = '__all__'


class CaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Case.objects.select_related('data_source').prefetch_related('actions', 'attachments')
    serializer_class = CaseSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    filter_class = CaseFilter
    search_fields = ('title', 'summary')
