"""
event.py

Define the current event name and its associated dates for the Sales Dashboard.

This module sets the EVENT_NAME constant and the EVENT_DATES mapping,
which associates human-readable labels with concrete `datetime.date` objects
for use throughout the app.
"""

import datetime

EVENT_NAME = "Prime Day"
EVENT_DATES = {
    "PD - Day 1": datetime.date(2025, 10,  7),
    "PD - Day 2": datetime.date(2025, 10,  8),
    "PD - Day 3": datetime.date(2025, 10,  9),
    "PD - Day 4": datetime.date(2025, 10, 10),
}
