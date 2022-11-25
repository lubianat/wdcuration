"""Top-level package for Wikidata Curation Tools."""

__author__ = """Tiago Lubiana"""
__email__ = "tiago.lubiana.alves@usp.br"
__version__ = "0.1.3"

from .wdcuration import (
    query_wikidata,
    search_wikidata,
    add_key,
    render_qs_url,
    lookup_id,
    today_in_quickstatements,
    get_statement_values,
    lookup_multiple_ids,
    query_wikidata,
)
