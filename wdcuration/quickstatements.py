"""Quickstatements management"""
from time import gmtime, strftime, strptime
from urllib.parse import quote


def convert_date_to_quickstatements(date, format="%Y-%m-%d"):
    """Converts a date to Quickstatements format using the datetime package."""
    return strftime("+%Y-%m-%dT00:00:00Z/11", strptime(date, format))


def today_in_quickstatements():
    """
    Return todays date in quickstatements format.
    """
    return strftime("+%Y-%m-%dT00:00:00Z/11", gmtime())


def render_qs_url(qs):
    """
    Render an URL targeting Quickstatements.
    """
    quoted_qs = quote(qs.replace("\t", "|").replace("\n", "||"), safe="")
    url = f"https://quickstatements.toolforge.org/#/v1={quoted_qs}\\"
    return url
