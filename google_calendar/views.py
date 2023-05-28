# views.py

import json
import os
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from django.http import HttpResponse
from django.views import View
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class GoogleCalendarInitView(APIView):
    def get(self, request):
        # Generate the authorization URL
        auth_url = generate_authorization_url(request)

        return Response({'authorization_url': auth_url}, status=status.HTTP_200_OK)

class GoogleCalendarRedirectView(APIView):
    def get(self, request):
        # Retrieve the authorization code from the request
        code = request.GET.get('code')

        # Exchange authorization code for access token
        access_token = exchange_authorization_code(code)

        if access_token is None:
            return Response({'error': 'Failed to retrieve access token'}, status=status.HTTP_400_BAD_REQUEST)

        # Get the list of events from the user's calendar
        events = get_calendar_events(access_token)

        return Response({'access_token': access_token, 'events': events}, status=status.HTTP_200_OK)

def generate_authorization_url(request):
    # Construct the OAuth authorization endpoint URL
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode({
        'client_id': settings.CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': request.build_absolute_uri('/rest/v1/calendar/redirect/'),
        'scope': 'https://www.googleapis.com/auth/calendar.events',
        'access_type': 'offline',
        'prompt': 'consent',
    })

    return auth_url

def exchange_authorization_code(code):
    # Exchange authorization code for access token
    url = 'https://oauth2.googleapis.com/token'
    data = {
        'code': code,
        'client_id': settings.CLIENT_ID,
        'client_secret': settings.CLIENT_SECRET,
        'redirect_uri': settings.REDIRECT_URI,
        'grant_type': 'authorization_code',
    }

    req = Request(url, method='POST', headers={'Content-Type': 'application/x-www-form-urlencoded'}, data=urlencode(data).encode('utf-8'))
    response = urlopen(req)
    response_data = json.loads(response.read().decode('utf-8'))

    return response_data.get('access_token')

def get_calendar_events(access_token):
    # Make a request to the Google Calendar API to retrieve the user's calendar events
    url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'
    headers = {
        'Authorization': 'Bearer ' + access_token,
        'Accept': 'application/json',
    }

    req = Request(url, method='GET', headers=headers)
    response = urlopen(req)
    response_data = json.loads(response.read().decode('utf-8'))

    return response_data.get('items', [])
