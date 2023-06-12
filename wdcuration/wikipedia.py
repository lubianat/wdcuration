from tqdm import tqdm
from wdcuration import divide_in_chunks_of_equal_len
import time
import requests


def get_qids_from_enwiki_pages(pages):
    """
    Returns a dictionary with page titles as keys and Wikidata QIDs as values
    """

    pages_with_wikidata_ids = {}
    if len(pages) > 50:
        for pages in tqdm(divide_in_chunks_of_equal_len(pages, 50, "list")):
            pages_with_wikidata_ids.update(get_qids_from_enwiki_pages(pages))
            time.sleep(0.2)
        return pages_with_wikidata_ids
    else:
        url = "https://en.wikipedia.org/w/api.php?action=query"
        params = {
            "format": "json",
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "redirects": "1",
            "titles": "|".join(pages),
        }
        r = requests.get(url, params)
        data = r.json()
        id_dict = {}
        for key, values in data["query"]["pages"].items():
            title = values["title"]
            try:
                qid = values["pageprops"]["wikibase_item"]
            except KeyError:
                print(f"No page found for {title}")
                qid = ""
                continue
            id_dict[title] = qid

        return id_dict
