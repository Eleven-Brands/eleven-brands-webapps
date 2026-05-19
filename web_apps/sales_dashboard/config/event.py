"""
event.py

Define the current event name and its associated dates for the Sales Dashboard.

This module sets the EVENT_NAME constant and the EVENT_DATES mapping,
which associates human-readable labels with concrete `datetime.date` objects
for use throughout the app.

IMPORTANT: Update EVENT_NAME and EVENT_DATES before every sales event
(Prime Day, Black Friday, etc.). Stale dates here cause the forecasting
logic to silently compare against the wrong period.
"""

import datetime

EVENT_NAME = "Black Friday/Cyber Monday"
EVENT_DATES = {

    "PD - Day 1": datetime.date(2025, 11, 20),
    "PD - Day 2": datetime.date(2025, 11, 21),
    "PD - Day 3": datetime.date(2025, 11, 22),
    "PD - Day 4": datetime.date(2025, 11, 23),

    "PD - Day 5": datetime.date(2025, 11, 24),
    "PD - Day 6": datetime.date(2025, 11, 25),
    "PD - Day 7": datetime.date(2025, 11, 26),
    "PD - Day 8": datetime.date(2025, 11, 27),

    "PD - Day 9": datetime.date(2025, 11, 28),
    "PD - Day 10": datetime.date(2025, 11, 29),
    "PD - Day 11": datetime.date(2025, 11, 30),
    "PD - Day 12": datetime.date(2025, 12, 1),
}
