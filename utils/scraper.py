import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import re
import json

class EventScraper:
    def __init__(self):
        self.base_url = "https://allevents.in"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }

    def clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace and newlines."""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text).strip()

    def parse_date(self, date_text: str) -> str:
        """Parse date text into a standardized format."""
        if not date_text:
            return None
        
        try:
            # Remove common words and clean the text
            date_text = date_text.lower()
            date_text = re.sub(r'from|to|until|starts?|ends?|on', '', date_text)
            date_text = self.clean_text(date_text)
            
            # Try to parse the date in various formats
            date_patterns = [
                r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*(?:\s+\d{4})?)',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{2}/\d{2}/\d{4})',
                r'(\d{1,2}\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, date_text)
                if match:
                    date_str = match.group(1)
                    # Convert to datetime and back to string
                    for fmt in ['%d %b %Y', '%Y-%m-%d', '%d/%m/%Y', '%d %B %Y']:
                        try:
                            date_obj = datetime.strptime(date_str, fmt)
                            return date_obj.strftime('%Y-%m-%d')
                        except ValueError:
                            continue
            
            return None
        except Exception as e:
            print(f"Error parsing date '{date_text}': {str(e)}")
            return None

    def search_events(self, city: str) -> List[Dict]:
        """Search for events in a specific city."""
        events = []
        city = city.lower().replace(' ', '-')
        
        # Try multiple event sources
        sources = [
            (f"https://insider.in/{city}/all-events", self._scrape_insider),  # insider.in
            (f"https://in.bookmyshow.com/{city}/events", self._scrape_bookmyshow),  # bookmyshow
            (f"{self.base_url}/{city}/events", self._scrape_allevents),  # allevents.in
        ]
        
        for url, scraper_func in sources:
            try:
                print(f"Trying to fetch events from: {url}")
                response = requests.get(url, headers=self.headers, timeout=15)
                print(f"Response status code: {response.status_code}")
                if response.status_code == 200:
                    print(f"Response content preview: {response.text[:500]}")
                    source_events = scraper_func(response.text)
                    if source_events:
                        events.extend(source_events)
                        print(f"Successfully fetched {len(source_events)} events from {url}")
                        print("Sample event:", json.dumps(source_events[0], indent=2) if source_events else "No events")
                else:
                    print(f"Failed to fetch events from {url}. Status code: {response.status_code}")
            except Exception as e:
                print(f"Error fetching events from {url}: {str(e)}")
                continue
        
        print(f"Total events found: {len(events)}")
        return events

    def _scrape_insider(self, html_content: str) -> List[Dict]:
        """Scrape events from insider.in"""
        events = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all event cards
        event_cards = soup.select('div[data-event-id]')
        print(f"Found {len(event_cards)} event cards on insider.in")
        
        for card in event_cards:
            try:
                # Extract event details
                title_elem = card.select_one('h3, h4, .event-title')
                if not title_elem:
                    continue
                
                title = self.clean_text(title_elem.text)
                print(f"Processing event: {title}")
                
                # Get date
                date_elem = card.select_one('.date-display, .event-date')
                date = self.parse_date(date_elem.text) if date_elem else None
                
                # Get venue
                venue_elem = card.select_one('.venue-display, .event-venue')
                venue = self.clean_text(venue_elem.text) if venue_elem else 'Venue not specified'
                
                # Get URL
                url_elem = card.select_one('a[href]')
                url = url_elem['href'] if url_elem else '#'
                if not url.startswith('http'):
                    url = f"https://insider.in{url}"
                
                # Get image
                img_elem = card.select_one('img[src]')
                image_url = img_elem['src'] if img_elem else None
                
                # Get description
                desc_elem = card.select_one('.event-description, .description')
                description = self.clean_text(desc_elem.text) if desc_elem else 'View event details on Insider'
                
                event_data = {
                    'title': title,
                    'date': date if date else 'Date not specified',
                    'venue': venue,
                    'url': url,
                    'image_url': image_url,
                    'description': description
                }
                
                print(f"Adding event: {json.dumps(event_data, indent=2)}")
                events.append(event_data)
                
            except Exception as e:
                print(f"Error processing insider.in event card: {str(e)}")
                continue
        
        return events

    def _scrape_bookmyshow(self, html_content: str) -> List[Dict]:
        """Scrape events from BookMyShow"""
        events = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all event cards
        event_cards = soup.select('.event-card, .bwc__sc-1nbn7v6-0')
        print(f"Found {len(event_cards)} event cards on bookmyshow")
        
        for card in event_cards:
            try:
                # Extract event details
                title_elem = card.select_one('h4, .bwc__sc-1nbn7v6-9')
                if not title_elem:
                    continue
                
                title = self.clean_text(title_elem.text)
                print(f"Processing event: {title}")
                
                # Get date
                date_elem = card.select_one('.date-venue time, .bwc__sc-1nbn7v6-13')
                date = self.parse_date(date_elem.text) if date_elem else None
                
                # Get venue
                venue_elem = card.select_one('.date-venue address, .bwc__sc-1nbn7v6-14')
                venue = self.clean_text(venue_elem.text) if venue_elem else 'Venue not specified'
                
                # Get URL
                url_elem = card.select_one('a[href]')
                url = url_elem['href'] if url_elem else '#'
                if not url.startswith('http'):
                    url = f"https://in.bookmyshow.com{url}"
                
                # Get image
                img_elem = card.select_one('img[src]')
                image_url = img_elem['src'] if img_elem else None
                
                event_data = {
                    'title': title,
                    'date': date if date else 'Date not specified',
                    'venue': venue,
                    'url': url,
                    'image_url': image_url,
                    'description': 'View event details on BookMyShow'
                }
                
                print(f"Adding event: {json.dumps(event_data, indent=2)}")
                events.append(event_data)
                
            except Exception as e:
                print(f"Error processing bookmyshow event card: {str(e)}")
                continue
        
        return events

    def _scrape_allevents(self, html_content: str) -> List[Dict]:
        """Scrape events from allevents.in"""
        events = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all event cards
        event_cards = soup.select('.event-item, .event-card, .event-list-item')
        print(f"Found {len(event_cards)} event cards on allevents.in")
        
        for card in event_cards:
            try:
                # Extract event details
                title_elem = card.select_one('.title, .event-title')
                if not title_elem:
                    continue
                
                title = self.clean_text(title_elem.text)
                print(f"Processing event: {title}")
                
                # Get date
                date_elem = card.select_one('.date, .event-date')
                date = self.parse_date(date_elem.text) if date_elem else None
                
                # Get venue
                venue_elem = card.select_one('.venue, .location')
                venue = self.clean_text(venue_elem.text) if venue_elem else 'Venue not specified'
                
                # Get URL
                url_elem = card.select_one('a[href]')
                url = url_elem['href'] if url_elem else '#'
                if not url.startswith('http'):
                    url = f"https://allevents.in{url}"
                
                # Get image
                img_elem = card.select_one('img[src]')
                image_url = img_elem['src'] if img_elem else None
                
                # Get description
                desc_elem = card.select_one('.event-description, .description')
                description = self.clean_text(desc_elem.text) if desc_elem else 'View event details on AllEvents'
                
                event_data = {
                    'title': title,
                    'date': date if date else 'Date not specified',
                    'venue': venue,
                    'url': url,
                    'image_url': image_url,
                    'description': description
                }
                
                print(f"Adding event: {json.dumps(event_data, indent=2)}")
                events.append(event_data)
                
            except Exception as e:
                print(f"Error processing allevents.in event card: {str(e)}")
                continue
        
        return events

class MeetupScraper:
    def __init__(self):
        self.base_url = "https://api.meetup.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        }
        # Common Meetup category IDs
        self.categories = [
            1,   # Arts & Culture
            2,   # Career & Business
            3,   # Cars & Motorcycles
            4,   # Community & Environment
            5,   # Dancing
            6,   # Education & Learning
            8,   # Fashion & Beauty
            9,   # Fitness
            10,  # Food & Drink
            11,  # Games
            13,  # Movements & Politics
            14,  # Health & Wellbeing
            15,  # Hobbies & Crafts
            16,  # Language & Ethnic Identity
            17,  # LGBT
            18,  # Lifestyle
            20,  # Movies & Film
            21,  # Music
            22,  # New Age & Spirituality
            23,  # Outdoors & Adventure
            24,  # Paranormal
            25,  # Parents & Family
            26,  # Pets & Animals
            27,  # Photography
            28,  # Religion & Beliefs
            29,  # Sci-Fi & Fantasy
            30,  # Singles
            31,  # Socializing
            32,  # Sports & Recreation
            33,  # Support
            34,  # Tech
            35,  # Writing
        ]

    def clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace and newlines."""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text).strip()

    def get_coordinates(self, city: str) -> tuple:
        """Get coordinates for a city using OpenStreetMap Nominatim API."""
        try:
            response = requests.get(
                f"https://nominatim.openstreetmap.org/search",
                params={
                    'q': city,
                    'format': 'json',
                    'limit': 1
                },
                headers={'User-Agent': 'LocalEventFinder/1.0'}
            )
            response.raise_for_status()
            
            data = response.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
            
            return None, None
            
        except Exception as e:
            print(f"Error getting coordinates for {city}: {str(e)}")
            return None, None

    def search_events(self, city: str, limit: int = 50) -> List[Dict]:
        """Search for events in a specific city."""
        events = []
        print(f"Fetching events for: {city}")
        
        try:
            # Get coordinates for the city
            lat, lon = self.get_coordinates(city)
            if not lat or not lon:
                print(f"Could not get coordinates for {city}")
                return events
            
            # Find groups in the area first
            groups_url = f"{self.base_url}/find/groups"
            params = {
                'lat': lat,
                'lon': lon,
                'radius': 50,  # 50 miles radius
                'category_ids': ','.join(map(str, self.categories)),
                'upcoming_events': 'true',
                'page': limit
            }
            
            response = requests.get(groups_url, headers=self.headers, params=params)
            response.raise_for_status()
            
            groups = response.json()
            print(f"Found {len(groups)} groups")
            
            # Get events from each group
            for group in groups:
                try:
                    group_urlname = group.get('urlname')
                    if not group_urlname:
                        continue
                    
                    events_url = f"{self.base_url}/{group_urlname}/events"
                    response = requests.get(
                        events_url,
                        headers=self.headers,
                        params={'page': 5}  # Get up to 5 events per group
                    )
                    
                    if response.status_code == 404:
                        continue
                    
                    response.raise_for_status()
                    group_events = response.json()
                    
                    for event in group_events:
                        event_info = {
                            'title': self.clean_text(event.get('name', 'No Title')),
                            'description': self.clean_text(event.get('description', 'No Description')),
                            'date': event.get('time'),
                            'venue': {
                                'name': event.get('venue', {}).get('name', 'Venue not specified'),
                                'address': event.get('venue', {}).get('address_1', 'Address not specified'),
                                'city': event.get('venue', {}).get('city', ''),
                                'state': event.get('venue', {}).get('state', ''),
                                'country': event.get('venue', {}).get('country', '')
                            },
                            'group': {
                                'name': group.get('name', ''),
                                'city': group.get('city', '')
                            },
                            'url': event.get('link'),
                            'image_url': group.get('group_photo', {}).get('photo_link'),
                            'going': event.get('yes_rsvp_count', 0)
                        }
                        
                        events.append(event_info)
                        print(f"Found event: {event_info['title']}")
                        
                        # Stop if we've reached the limit
                        if len(events) >= limit:
                            return events
                    
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching events for group {group_urlname}: {str(e)}")
                    continue
                except Exception as e:
                    print(f"Error processing events for group {group_urlname}: {str(e)}")
                    continue
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching events: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response text: {e.response.text[:200]}")
        except Exception as e:
            print(f"Error processing events: {str(e)}")
        
        return events

def fetch_events(location: str, date: str = None) -> List[Dict]:
    """
    Fetch events for a given location.
    
    Args:
        location: City name to search events in
        date: Date string (optional)
        
    Returns:
        List of events with their details
    """
    try:
        print(f"Fetching events for location: {location}, date: {date}")
        
        # Initialize event scraper
        event_scraper = EventScraper()
        
        # Try different city name formats
        city_formats = [
            location,  # Original format
            location.lower(),  # Lowercase
            location.replace(' ', '-').lower(),  # Lowercase with hyphens
            location.replace(' ', '').lower(),  # Lowercase without spaces
            location.split(',')[0].strip(),  # First part before comma
        ]
        
        all_events = []
        for city in city_formats:
            print(f"Trying city format: {city}")
            events = event_scraper.search_events(city)
            if events:
                all_events.extend(events)
                print(f"Found {len(events)} events for city format: {city}")
                break  # Stop if we found events
        
        # Parse target date
        target_date = None
        if date:
            try:
                target_date = datetime.strptime(date, '%Y-%m-%d').date()
                print(f"Target date: {target_date}")
            except ValueError:
                print(f"Invalid date format: {date}")
                return []
        
        print(f"Found {len(all_events)} total events before filtering")
        
        # Filter and standardize events
        standardized_events = []
        seen_events = set()  # To avoid duplicates
        
        for event in all_events:
            try:
                # Skip if we've seen this event before (based on title and venue)
                event_key = (event.get('title', '').lower(), event.get('venue', '').lower())
                if event_key in seen_events:
                    continue
                seen_events.add(event_key)
                
                # Get and validate the event date
                event_date_str = event.get('date', '')
                event_date = None
                
                if event_date_str and event_date_str != 'Date not specified':
                    try:
                        # Try parsing the date in various formats
                        date_formats = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%B %d, %Y', '%d %B %Y']
                        for fmt in date_formats:
                            try:
                                event_date = datetime.strptime(event_date_str, fmt).date()
                                break
                            except ValueError:
                                continue
                        
                        if not event_date and event_date_str:
                            # Try using the parse_date method as a fallback
                            parsed_date = event_scraper.parse_date(event_date_str)
                            if parsed_date:
                                event_date = datetime.strptime(parsed_date, '%Y-%m-%d').date()
                    
                    except (ValueError, TypeError) as e:
                        print(f"Could not parse date '{event_date_str}': {str(e)}")
                        continue
                
                # Skip events that don't match the target date
                if target_date and (not event_date or event_date != target_date):
                    continue
                
                # Format the event date for display
                display_date = event_date.strftime('%B %d, %Y') if event_date else 'Date not specified'
                
                # Clean and standardize the event data
                standardized_event = {
                    'title': event.get('title', 'No Title').strip(),
                    'description': event.get('description', 'No description available').strip(),
                    'venue': event.get('venue', 'Location not specified').strip(),
                    'date': display_date,
                    'url': event.get('url', '#'),
                    'image_url': event.get('image_url')
                }
                
                # Only add events with valid titles
                if standardized_event['title'] and standardized_event['title'].lower() != 'no title':
                    standardized_events.append(standardized_event)
                    print(f"Added event: {standardized_event['title']} on {standardized_event['date']}")
            
            except Exception as e:
                print(f"Error processing event: {str(e)}")
                continue
        
        print(f"Found {len(standardized_events)} events after filtering")
        
        if not standardized_events:
            print(f"No events found for {location}" + (f" on {date}" if date else ""))
            # Try fetching events without date filter if no events found
            if target_date and len(all_events) > 0:
                print("Trying to fetch events without date filter...")
                return fetch_events(location, None)
        
        return standardized_events
        
    except Exception as e:
        print(f"Error fetching events: {str(e)}")
        return []
