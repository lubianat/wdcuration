"""Wikidata lookups via SPARQL"""
from time import sleep

from SPARQLWrapper import JSON, SPARQLWrapper
from tqdm import tqdm

from wdcuration.utils import chunk


def get_wikidata_items_for_id(identifier_property):
    """
    Returns and ID:QID dictionary for all occurences of a certain identifier on Wikidata.
    Might time-out for heavily used identifiers.

    Args:
      identifier_property (str): The identifier property to be used on Wikidata. E.g. "P7963".
    """
    existing_terms_output = query_wikidata(
        f'  SELECT DISTINCT ?id   (REPLACE(STR(?item), ".*Q", "Q") AS ?qid)  WHERE {{ ?item wdt:{identifier_property} ?id . }} '
    )

    existing_terms_dict = {}
    for a in existing_terms_output:
        existing_terms_dict[str(a["id"])] = a["qid"]

    return existing_terms_dict


def detect_direct_links(list_of_qids, link_phrase="wdt:P279*"):
    """Detects and returns pairs from a list of Wikidata QIDs
    with links to each other.
    The base link if "wdt:P279*" which covers indirect and direct subclasses (P279*).

    Args:
      list_of_qids (list): A list of Wikidata QIDs.
      link_phrase (str): The link to be searched between the entities. Defaults to "wdt:P279*"
    """
    clean_list = [x for x in list_of_qids if str(x) != "nan"]

    formatted_qids = "{ wd:" + " wd:".join(clean_list) + "}"
    query = f"""
  SELECT
    (REPLACE(STR(?a_), ".*Q", "Q") AS ?a)
    (REPLACE(STR(?b_), ".*Q", "Q") AS ?b)

  WHERE
{{

  VALUES ?a_ {formatted_qids} .
  VALUES ?b_ {formatted_qids} .
  FILTER (?a_ != ?b_)
  ?a_ {link_phrase}?b_ .
  }}"""
    return query_wikidata(query)


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


def lookup_id(id, property, default="") -> str:
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


def lookup_multiple_ids(list_of_ids, wikidata_property, return_type="dict"):
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

        if return_type == "dict":
            return result_dict
        if return_type == "list":
            return list(result_dict.values())
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
    if return_type == "dict":
        return result_dict
    if return_type == "list":
        return list(result_dict.values())
