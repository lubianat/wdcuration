"""Other Wikidata-related searches, mostly using Cirrus Search"""
import webbrowser
from urllib.parse import quote

import requests

from wdcuration.sparql import query_wikidata


def search_wikidata(
    search_term,
    excluded_types=[],
    fixed_type=None,
    exclude_basic=True,
):
    """
    Looks up string on Wikidata
    """

    basic_exclusion = list(
        {
            "Q26842193": "journal",
            "Q5633421": "scientific journal",
            "Q737498": "academic journal",
            "Q7725634": "literary work",
            "Q47461344": "written work",
            "Q101352": "family name",
            "Q13442814": "scholarly article",
            "Q732577": "publication",
            "Q3331189": "version, edition or translation",
            "Q187685": "doctoral thesis",
            "Q1266946": "thesis",
            "Q4167410": "disambiguation page",
            "Q3754629": "taxon",
            "Q4167836": "Wikimedia category",
            "Q30612": "clinical trial",
            "Q215380": "musical group",
            "Q482994": "musical album",
            "Q105543609": "musical work",
            "Q5": "human",
            "Q838795": "comic strip",
        }.keys()
    )
    excluded_types_local = excluded_types

    # Workaround to avoid accumulation. Not sure why, but they are accumulating.
    excluded_types_local = list(set(excluded_types_local))

    if exclude_basic == True:
        for excluded_type in basic_exclusion:
            excluded_types_local.append(excluded_type)  # Disambiguation page

    for excluded_type in excluded_types_local:
        search_term += f" -haswbstatement:P31={excluded_type} "
    if fixed_type is not None:
        search_term += f" haswbstatement:P31={fixed_type} "

    base_url = "https://www.wikidata.org/w/api.php"
    payload = {
        "action": "query",
        "list": "search",
        "srsearch": search_term,
        "language": "en",
        "format": "json",
        "origin": "*",
    }

    res = requests.get(base_url, params=payload)

    parsed_res = parse_wikidata_result(res.json())
    return parsed_res


def parse_wikidata_result(wikidata_result):
    base_result = {
        "id": "NONE",
        "label": "NONE",
        "description": "NONE",
        "url": f"https://www.wikidata.org/wiki/NONE",
    }
    # Workaround for when finding no results
    if len(wikidata_result["query"]["search"]) == 0:
        return base_result

    first_item = wikidata_result["query"]["search"][0]
    qid = first_item["title"]

    label_and_description = get_label_and_description(qid, lang="en")

    return {
        "id": qid,
        "label": label_and_description["label"],
        "description": label_and_description.get("description", "no description"),
        "url": f"https://www.wikidata.org/wiki/{qid}",
    }


def get_label_and_description(qid, lang="en", method="wikidata_api"):
    if method == "wikidata_api":
        url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&props=labels|descriptions&ids={qid}&languages={lang}&format=json"
        r = requests.get(url)
        data = r.json()
        try:
            return {
                "label": data["entities"][qid]["labels"][lang]["value"],
                "description": data["entities"][qid]["descriptions"][lang]["value"],
            }
        except KeyError:
            return {"label": "NONE", "DESCRIPTION": "NONE"}

    if method == "json_dump":
        url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
        r = requests.get(url)
        data = r.json()
        return {
            "label": data["entities"][qid]["labels"][lang]["value"],
            "description": data["entities"][qid]["descriptions"][lang]["value"],
        }

    if method == "sparql":
        label_and_description_query = (
            """
      SELECT ?label ?description
      WHERE
      {"""
            f"wd:{qid} rdfs:label ?label . "
            f'FILTER (LANG (?label) = "{lang}")'
            "OPTIONAL {"
            f"wd:{qid} schema:description ?description . "
            f'FILTER (LANG (?description) = "{lang}")'
            "}"
            "}"
        )
        label_and_description = query_wikidata(label_and_description_query)
        if len(label_and_description) == 0:
            label_and_description = [{"label": "NONE", "description": "NONE"}]
        return label_and_description[0]


def go_to_wikidata(search_term):
    """
    Open the browser for manual search on Wikidata
    """
    url = "https://www.wikidata.org/w/index.php?search=" + quote(search_term)
    webbrowser.open_new_tab(url)


def add_key(
    dictionary,
    string,
    dict_key="",
    search_string="",
    excluded_types: list = ["Q13442814"],
) -> dict:
    """
    Prompts the user for adding a key to the target dictionary.
    Args:
        dictionary (dict): A reference dictionary containing strings as keys and Wikidata QIDs as values.
        string (str): A new key to add to the dictionary.
        dict_key (str): The key to be used in the dictionary. If none is provided, uses the "string" entry.
        search_string (str): The string to be searched in Wikidata. If none is provided, uses the "string" entry.
    Returns:
        dict: The updated dictionary.
    """

    if dict_key == "":
        dict_key = string
    if search_string == "":
        search_string = string

    predicted_id = search_wikidata(search_string, excluded_types)
    annotated = False

    while annotated == False:
        answer = input(
            f"Is the QID for '{search_string}'  \n "
            f"{predicted_id['id']} - {predicted_id['label']} "
            f"({predicted_id['description']}) ? (y/n) "
        )

        if answer == "y":
            dictionary[dict_key] = predicted_id["id"]
            annotated = True
        elif answer == "n":
            search = input("Search Wikidata? (y/n/skip)")
            if search == "y":
                go_to_wikidata(search_string)
            elif search == "skip":
                break
            qid = input(f"What is the qid for: '{search_string}' ? ")
            dictionary[dict_key] = qid
            annotated = True
        else:
            print("Answer must be either 'y', 'n' ")

    return dictionary
