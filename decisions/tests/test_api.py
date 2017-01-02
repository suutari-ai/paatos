import pytest
from rest_framework.reverse import reverse


@pytest.mark.parametrize('resource', [
    'action',
    'case',
    'event',
    'function',
    'organization',
    'post',
])
@pytest.mark.django_db
def test_smoke_get(client, resource, action, case, function, event, organization, post):
    """
    Test GET to every resource's list and detail endpoint.
    """
    list_url = reverse('v1:%s-list' % resource)
    response = client.get(list_url)
    assert response.status_code == 200
    assert len(response.data['results'])

    detail_url = reverse('v1:%s-detail' % resource, kwargs={'pk': locals().get(resource).id})
    response = client.get(detail_url)
    assert response.status_code == 200
    assert response.data
