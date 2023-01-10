"""Main module."""
from pathlib import Path
from tokenize import String
from typing import OrderedDict
import requests
from urllib.parse import quote
from SPARQLWrapper import SPARQLWrapper, JSON
import webbrowser
from time import gmtime, strftime, sleep, strptime
from tqdm import tqdm
from itertools import islice
import json
from dataclasses import dataclass, field
from typing import List


# Wikidata lookups via SPARQL


def get_wikidata_items_for_id(identifier_property):
    """
    Returns and ID:QID dictionary for all occurences of a certain identifier on Wikidata.
    Might time-out for heavily used identifiers.

    Args:
      identifier_property: The identifier property to be used on Wikidata. E.g. "P7963".
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


# Other Wikidata-related searches, mostly using Cirrus Search


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


# Quickstatements management


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


# Dict handling
@dataclass
class NewItemConfig:
    """A class containing the information for a new item

    Attributes:
      labels: A dictionary of labels in the format {"langcode": "label"}
      descriptions: A dictionary of descriptions in the format {"langcode": "description"}
      id_property: The property for the target ID for the item, if available.
      id_value:  The value for the target id.
    """

    labels: dict
    descriptions: dict
    item_property_value_pairs: dict = field(default_factory=lambda: {})
    id_property_value_pairs: dict = field(default_factory=lambda: {})
    quickstatements = ""

    def render_quickstatements(self):
        qs = """CREATE
      """
        for k, v in self.labels.items():
            qs += f"""
      LAST|L{k}|"{v}" """

        for k, v in self.descriptions.items():
            qs += f"""
      LAST|D{k}|"{v}" """

        for k, v in self.item_property_value_pairs.items():
            for value in v:
                qs += f"""
        LAST|{k}|{value} """
        for k, v in self.id_property_value_pairs.items():
            for value in v:
                qs += f"""
        LAST|{k}|"{value}" """

        self.quickstatements = qs


@dataclass
class WikidataDictAndKey:
    """
    A class containing the dicts and keys used in reconciliations to Wikidata
    Attributes:
      master_dict: A dict of dicts, each of the inner dicts containing the keys mapped to Wikidata ids.
      dict_name: The name of the inner dict that the new key will be added.
      string: The key and search string to be added to the dict. It is overwritten by
      "dict_key" and "search_string" when available.
      dict_key: The dict key to be added to the curation dictionary.
      search_string: A custom search string, when different from the dict key
      path: The Pathlib path to the folder where the dicts are stored.
      format_function: The function to format the string before the search. Defaults to str (no change).
      excluded_types: A list of Wikidata P31 values to be excluded of the search.

    """

    master_dict: dict
    dict_name: str
    path: Path
    new_item_config: NewItemConfig
    string: str = ""
    dict_key: str = ("",)
    search_string: str = ""
    format_function = str
    excluded_types: List = field(default_factory=lambda: ["Q13442814"])

    def add_key(self, return_qs=False):
        """
        Prompts the user for adding a key to the target dictionary.
        """

        if self.dict_key == "":
            self.dict_key = self.string
        if self.search_string == "":
            self.search_string = self.string

        predicted_id = search_wikidata(self.search_string, self.excluded_types)
        annotated = False

        while annotated == False:
            answer = input(
                f"Is the QID for '{self.search_string}'  \n "
                f"{predicted_id['id']} - {predicted_id['label']} "
                f"({predicted_id['description']}) ? (y/n) "
            )

            if answer == "y":
                self.master_dict[self.dict_name][self.dict_key] = predicted_id["id"]
                annotated = True
            elif answer == "n":
                search = input("Search Wikidata? (y/n/skip/create)")
                if search == "y":
                    go_to_wikidata(self.search_string)
                if search == "n" or search == "y":
                    qid_input = False
                    while qid_input == False:
                        qid = input(
                            f"What is the qid for: '{self.search_string}' ? (QXX/skip/create) "
                        )
                        if "Q" in qid:
                            self.master_dict[self.dict_name][self.dict_key] = qid
                            qid_input = True
                        if qid == "skip":
                            break
                        elif qid == "create":
                            new_item_config = self.new_item_config
                            new_item_config.render_quickstatements()
                            if return_qs:
                                return new_item_config.quickstatements
                            print(new_item_config.quickstatements)
                            print(render_qs_url(new_item_config.quickstatements))

                            break
                    annotated = True
                elif search == "skip":
                    break
                elif search == "create":
                    new_item_config = self.new_item_config
                    new_item_config.render_quickstatements()
                    if return_qs:
                        return new_item_config.quickstatements
                    print(new_item_config.quickstatements)
                    print(render_qs_url(new_item_config.quickstatements))

                    break

            else:
                print("Answer must be either 'y', 'n' ")
            return ""
        if return_qs:
            return ""

    def save_dict(self):
        self.path.joinpath(f"{self.dict_name}.json").write_text(
            json.dumps(self.master_dict[self.dict_name], indent=4, sort_keys=True)
        )


def check_and_save_dict(
    master_dict,
    dict_name,
    string,
    path,
    dict_key="",
    search_string="",
    format_function=str,
    excluded_types: list = ["Q13442814"],
):
    if string not in master_dict[dict_name]:
        master_dict[dict_name] = add_key(
            master_dict[dict_name],
            string,
            dict_key=dict_key,
            search_string=format_function(string),
            excluded_types=excluded_types,
        )
        path.joinpath(f"{dict_name}.json").write_text(
            json.dumps(master_dict[dict_name], indent=4, sort_keys=True)
        )
    return master_dict[dict_name]


def add_key(
    dictionary,
    string,
    dict_key="",
    search_string="",
    excluded_types: list = ["Q13442814"],
):
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


# Other


def divide_in_chunks_of_equal_len(arr_range, arr_size):
    """Breaks up a list into a list of lists"""
    return chunk(arr_range, arr_size)


def chunk(arr_range, arr_size):
    """Breaks up a list into a list of lists"""
    arr_range = iter(arr_range)
    return iter(lambda: tuple(islice(arr_range, arr_size)), ())
