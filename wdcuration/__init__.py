"""Top-level package for Wikidata Curation Tools."""

__author__ = """Tiago Lubiana"""
__email__ = "tiago.lubiana.alves@usp.br"
__version__ = "0.2.1"

from wdcuration.api_searches import add_key, parse_wikidata_result, search_wikidata
from wdcuration.dict_handler import (
    NewItemConfig,
    WikidataDictAndKey,
    check_and_save_dict,
)
from wdcuration.quickstatements import (
    convert_date_to_quickstatements,
    render_qs_url,
    today_in_quickstatements,
)
from wdcuration.sheet_based_curation import (
    generate_curation_spreadsheet,
    get_quickstatements_for_curated_sheet,
    get_subset_not_on_wikidata,
    print_quickstatements_for_curated_sheet,
    run_multiple_searches,
)
from wdcuration.sparql import (
    detect_direct_links,
    get_statement_values,
    get_wikidata_items_for_id,
    lookup_id,
    lookup_multiple_ids,
    query_wikidata,
)
from wdcuration.utils import divide_in_chunks_of_equal_len
