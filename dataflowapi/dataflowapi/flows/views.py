import logging
import requests

from django.conf import settings

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from mohawk import Sender
from mohawk.exc import HawkFail

logger = logging.getLogger(__name__)


@api_view(['POST'])
def run_flow(request, *args, **kwargs):
    """str: API Endpoint to fetch data from.
    Endpoint has to accept GET request and respond with HTTP 200 OK for success
    """
    """str: API Endpoint to insert data to.
    Endpoint has to accept POST request and respond with HTTP 201 created for success
    """
    import ipdb; ipdb.set_trace()
    from_url = request.POST.get('from_url')
    if not from_url:
        return Response('from_url parameter is required', status=status.HTTP_400_BAD_REQUEST)
    to_url = request.POST.get('to_url')
    if not to_url:
        return Response('to_url parameter is required', status=status.HTTP_400_BAD_REQUEST)

    credentials = {
        'id': settings.HAWK_ID,
        'key': settings.HAWK_KEY,
        'algorithm': settings.HAWK_ALGORITHM
    }
    content_type = ''
    sender = Sender(credentials, from_url, 'get', content='', content_type=content_type)
    response = requests.get(
        from_url,
        headers={'Authorization': sender.request_header, 'Content-Type': content_type}
    )
    if response.status_code != 200:
        return Response((
            f'GET request to {from_url} is unsuccessful\n'
            f'Message: {response.text}'
        ), status=response.status_code)
    try:
        sender.accept_response(response.headers['Server-Authorization'],
                               content=response.content,
                               content_type=response.headers['Content-Type'])
    except HawkFail as e:
        return Response('HAWK Authentication failed {}'.format(str(e)),
                        status=status.HTTP_401_UNAUTHORIZED)

    content_type = 'application/json'
    sender = Sender(
        credentials,
        to_url,
        'POST',
        content=str(response.json()),
        content_type=content_type
    )

    response = requests.post(
        to_url,
        json=response.json(),
        headers={'Authorization': sender.request_header, 'Content-Type': content_type}
    )
    if response.status_code != 201:
        return Response((
            f'POST request to {to_url} is unsuccessful\n'
            f'Message: {response.text}'
        ), status=response.status_code)
    logger.info(f'{from_url} to {to_url} data flow completed')
    return Response(status=status.HTTP_200_OK)
