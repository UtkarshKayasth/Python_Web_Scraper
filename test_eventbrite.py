from utils.scraper import fetch_events
from datetime import datetime

def format_date(date_str):
    try:
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime('%Y-%m-%d %H:%M')
    except:
        return date_str

def test_events():
    print("Fetching events...")
    events = fetch_events('Mumbai')
    
    print(f"\nFound {len(events)} Events:\n")
    for event in events:
        print(f"Title: {event['title']}")
        print(f"Date: {format_date(event['date'])}")
        print(f"Venue: {event['venue']['name']}")
        print(f"Address: {event['venue']['address']}")
        print(f"Group: {event['group']['name']}")
        if event['description']:
            print(f"Description: {event['description'][:200]}...")
        print(f"URL: {event['url']}")
        print(f"Attendees: {event['going']}")
        print("-" * 80)
        print()

if __name__ == "__main__":
    test_events()
