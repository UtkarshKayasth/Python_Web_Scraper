from flask import Blueprint, render_template, request
from .forms import EventSearchForm
from utils.scraper import fetch_events
from datetime import datetime
import json

main = Blueprint('main', __name__)

@main.route('/', methods=['GET', 'POST'])
def index():
    form = EventSearchForm()
    if request.method == 'POST':
        print(f"Form submitted with data: {request.form}")
        print(f"Form validation errors: {form.errors}")
        if form.validate_on_submit():
            location = form.location.data
            date = form.date.data
            print(f"Fetching events for location: {location}, date: {date}")
            
            # Check if date is too far in the future
            days_in_future = (date - datetime.now().date()).days
            if days_in_future > 90:
                message = f"The date {date} is {days_in_future} days in the future. Most event listings only show events up to 3 months ahead. Try searching for a closer date."
                return render_template('results.html', 
                                    location=location, 
                                    date=date, 
                                    events=[],
                                    message=message)
            
            events = fetch_events(location, str(date))
            print(f"Received {len(events)} events from fetch_events")
            print("Events data:")
            print(json.dumps(events, indent=2))
            
            message = None
            if not events:
                if days_in_future > 30:  # If date is more than a month away
                    message = f"No events found in {location} for {date}. The date might be too far ahead - most venues post events 2-4 weeks in advance. Try:"
                else:
                    message = f"No events found in {location} for {date}. Try:"
            
            print(f"Rendering template with {len(events)} events")
            return render_template('results.html', 
                                location=location, 
                                date=date, 
                                events=events,
                                message=message)
        else:
            print(f"Form validation failed: {form.errors}")
    return render_template('index.html', form=form)
