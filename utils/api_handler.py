import requests

def get_events(location, date):
    API_URL = 'https://www.eventbriteapi.com/v3/events/search/'
    API_KEY = 'your_api_key'

    params = {
        'location.address': location,
        'start_date.range_start': date + 'T00:00:00Z',
        'start_date.range_end': date + 'T23:59:59Z',
        'token': API_KEY
    }
    response = requests.get(API_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        events = []
        for event in data['events']:
            events.append({
                'name': event['name']['text'],
                'date': event['start']['local'],
                'location': event['venue']['address']['localized_address_display'],
                'description': event['description']['text']
            })
        return events
    else:
        return [{'name': 'No events found', 'date': '-', 'location': '-', 'description': '-'}]
