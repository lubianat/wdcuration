"""Main module."""
from tokenize import String
from typing import OrderedDict
import clipboard
import requests
from urllib.parse import quote
from SPARQLWrapper import SPARQLWrapper, JSON
import webbrowser
from time import gmtime, strftime, sleep
from tqdm import tqdm
from itertools import islice


def main():
    query_wikidata("SELECT * WHERE {?s ?p ?o} LIMIT 10 ")


def chunk(arr_range, arr_size):
    """Breaks up a list into a list of lists"""
    arr_range = iter(arr_range)
    return iter(lambda: tuple(islice(arr_range, arr_size)), ())


def lookup_multiple_ids(list_of_ids, wikidata_property):
    """
    Looks up multiple IDs on Wikidata and returns a dict containing them and the QIDs.
    """
    if len(list_of_ids) > 200:
        list_of_smaller_lists_of_ids = chunk(list_of_ids, 200)
        result_dict = {}
        for small_list in tqdm(list_of_smaller_lists_of_ids):
            current_dict = lookup_multiple_ids(small_list, wikidata_property)
            result_dict.update(current_dict)
            sleep(0.3)

        return result_dict

    formatted_ids = '""'.join(list_of_ids)
    query = (
        """
  SELECT  
  (REPLACE(STR(?item), ".*Q", "Q") AS ?qid) 
  ?id 
  WHERE { """
        f'VALUES ?id {{ "{formatted_ids}" }} . '
        f"?item wdt:{wikidata_property} ?id . "
        """
  }
  """
    )
    query_result = query_wikidata(query)
    result_dict = {}
    for entry in query_result:
        result_dict[entry["id"]] = entry["qid"]
    return result_dict


def today_in_quickstatements():
    """
    Return todays date in quickstatements format.
    """
    return strftime("+%Y-%m-%dT00:00:00Z/11", gmtime())


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
        "description": first_item.get("description", "no description"),
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
    """
    Render an URL targeting Quickstatements.
    """
    quoted_qs = quote(qs.replace("\t", "|").replace("\n", "||"), safe="")
    url = f"https://quickstatements.toolforge.org/#/v1={quoted_qs}\\"
    return url


def lookup_id(id, property, default=""):
    """
    Looks up a foreign ID on Wikidata based on its specific property.

    Args:
      id (str): The value of the ID as encoded on Wikidata.
      property (str): The property used to link to that ID .
      default (str): What to return if no unique ID is present. Defaults to "".

    Returns:
      str: The Wikidata QID for the foreign ID or "".
    """

    sparql = SPARQLWrapper(
        "https://query.wikidata.org/sparql",
        agent="wdcuration (https://github.com/lubianat/wdcuration)",
    )
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


def lookup_label(qid, lang="en", default=""):
    """
    Looks up a label on Wikidata given a QID.
    """

    sparql = SPARQLWrapper(
        "https://query.wikidata.org/sparql",
        agent="wdcuration (https://github.com/lubianat/wdcuration)",
    )
    query = f"""
    SELECT ?item ?itemLabel
    WHERE
    {{
        {qid} rdfs:label ?itemLabel. 
        FILTER (LANG (?itemLabel) = "{lang}")
    }}
    """
    bindings = query_wikidata(query)
    if len(bindings) == 1:
        item = bindings[0]["itemLabel"].split("/")[-1]
        return item
    else:
        return default


def get_statement_values(qid, property, label=False):
    """
    Return the values for a Wikidata QID + PID pair as a Python list.
    """

    if label:
        label_projection = "?valueLabel"
        label_line = (
            "?value rdfs:label ?valueLabel . FILTER (LANG (?valueLabel) = 'en')"
        )
    else:
        label_projection = ""
        label_line = ""
    query = f"""
    SELECT ?value {label_projection}
    WHERE
    {{
        wd:{qid} wdt:{property} ?value .
        {label_line}
    }}
    """

    bindings = query_wikidata(query)
    value_list = []
    for binding in bindings:
        if label:
            value_list.append(
                {
                    "id": binding["value"].split("/")[-1],
                    "label": binding["valueLabel"],
                }
            )

        else:
            value_list.append(binding["value"])
    return value_list


def query_wikidata(
    query,
    endpoint="https://query.wikidata.org/sparql",
    agent="wdcuration (https://github.com/lubianat/wdcuration)",
    simplify=True,
):
    """A simple function to query Wikidata and return a python dictionary"""
    sparql = SPARQLWrapper(endpoint=endpoint, agent=agent)
    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    bindings = results["results"]["bindings"]

    if simplify:
        return_value = []

        for binding in bindings:
            entry = {}
            for key, value in binding.items():
                entry[key] = value["value"]
            return_value.append(entry)
        return return_value
    else:
        return bindings


if __name__ == "__main__":
    main()
