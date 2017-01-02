from django_filters import CharFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, viewsets

from decisions.models import Action, Post

from .base import BaseFilter, DataModelSerializer


class PostFilter(BaseFilter):
    organization = CharFilter(name='organization_id')

    class Meta:
        model = Post
        fields = BaseFilter.Meta.fields + ('organization',)


class PostSerializer(DataModelSerializer):
    actions = serializers.HyperlinkedRelatedField(queryset=Action.objects.all(), many=True, view_name='action-detail')

    class Meta:
        model = Post
        fields = '__all__'


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Post.objects.select_related('data_source', 'organization').prefetch_related('actions',)
    serializer_class = PostSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = PostFilter
