"""Main module."""
from tokenize import String
import clipboard
import requests
from urllib.parse import quote
from SPARQLWrapper import SPARQLWrapper, JSON
import webbrowser


def go_to_wikidata(search_term):
    """
    Open the browser for manual search on Wikidata
    """
    url = "https://www.wikidata.org/w/index.php?search=" + quote(search_term)
    webbrowser.open_new_tab(url)


def search_wikidata(search_term):
    """
    Looks up string on Wikidata
    """

    base_url = "https://www.wikidata.org/w/api.php"
    payload = {
        "action": "wbsearchentities",
        "search": search_term,
        "language": "en",
        "format": "json",
        "origin": "*",
    }

    res = requests.get(base_url, params=payload)

    parsed_res = parse_wikidata_result(res.json())
    return parsed_res


def parse_wikidata_result(wikidata_result):

    # Workaround for when finding no results
    if len(wikidata_result["search"]) == 0:
        return {
            "id": "NONE",
            "label": "NONE",
            "description": "NONE",
            "url": f"https://www.wikidata.org/wiki/NONE",
        }

    first_item = wikidata_result["search"][0]

    return {
        "id": first_item["id"],
        "label": first_item["label"],
        "description": first_item["description"],
        "url": f"https://www.wikidata.org/wiki/{first_item['id']}",
    }


def add_key(dictionary, string):
    """
    Prompts the user for adding a key to the target dictionary.
    Args:
        dictionary (dict): A reference dictionary containing strings as keys and Wikidata QIDs as values.
        string (str): A new key to add to the dictionary.
    Returns:
        dict: The updated dictionary.
    """

    clipboard.copy(string)
    predicted_id = search_wikidata(string)
    annotated = False

    while annotated == False:
        answer = input(
            f"Is the QID for '{string}'  \n "
            f"{predicted_id['id']} - {predicted_id['label']} "
            f"({predicted_id['description']}) ? (y/n) "
        )

        if answer == "y":
            dictionary[string] = predicted_id["id"]
            annotated = True
        elif answer == "n":
            search = input("Search Wikidata? (y/n)")
            if search == "y":
                go_to_wikidata(string)
            qid = input(f"What is the qid for: '{string}' ? ")
            dictionary[string] = qid
            annotated = True
        else:
            print("Answer must be either 'y', 'n' ")

    return dictionary


def render_qs_url(qs):
    quoted_qs = quote(qs.replace("\t", "|").replace("\n", "||"), safe="")
    url = f"https://quickstatements.toolforge.org/#/v1={quoted_qs}\\"
    return url


def lookup_id(id, property, default):
    """
    Looks up a foreign ID on Wikidata based on its specific property.
    """

    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    query = f"""
    SELECT ?item ?itemLabel
    WHERE
    {{
        ?item wdt:{property} "{id}" .
    }}
    """
    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    bindings = results["results"]["bindings"]
    if len(bindings) == 1:
        item = bindings[0]["item"]["value"].split("/")[-1]
        return item
    else:
        return default
