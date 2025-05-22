import argparse
import os
from utils import *
from agents import *
import pandas as pd
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
import json


def _add_to_list(search_result, result_list):
    """ 
    Determine if search result should be added to result_list
    Input: search_result (SerperResult), result_list (list of SerperResult instances)
    Output: True or False
    """
    for result in result_list:
        if result.link == search_result.link:
            return False
    return True


def fact_check(claim, openai_model_name, client, serper, MAX_SEARCH_QUERIES,
               MAX_SEARCH_RESULTS_PER_QUERY, use_webextraction_agent):

    memory_bank = [] # list of SerperResult objects
    not_self_contained_results = []
    query_list = [InitialQueryGen(client, openai_model_name, claim)]
    num_search_queries_made = 0
    while len(query_list) > 0 and num_search_queries_made < MAX_SEARCH_QUERIES:
        search_query = query_list.pop(0)
        result_list = serper.query(search_query) # list of SerperResult objects sorted by position
        result_list = [item for item in result_list if _add_to_list(item, memory_bank)] # exclude results that are already in evidence set
        try:
            # list of SerperResult objects in sorted order
            ranked_result_list = SearchRank(client, openai_model_name,
                                            search_query, result_list)
            # only keep top MAX_SEARCH_RESULTS_PER_QUERY
            ranked_result_list = ranked_result_list[0:min(MAX_SEARCH_RESULTS_PER_QUERY, len(ranked_result_list))]
        except Exception:
            print(f"Exception occurred during sorting for query: {search_query}")
            ranked_result_list = result_list[0:min(MAX_SEARCH_RESULTS_PER_QUERY, len(result_list))]

        if len(ranked_result_list) > 0:
            num_search_queries_made += 1

        for result in ranked_result_list:

            # visit webpage and store extracted content
            result.visit_web_page(client, openai_model_name, use_webextraction_agent)

            is_self_contained = SelfContainedCheck(client, openai_model_name, claim, memory_bank, result) # boolean
            
            # —— if document is self-contained —————
            if is_self_contained:
                helpful = DetHelpful(client, openai_model_name, claim, memory_bank, result) # boolean
                if helpful:
                    memory_bank.append(result)
                    sufficient = SufficientEvidence(client, openai_model_name, claim, memory_bank) # boolean
                    if sufficient:
                        print(f"CASE 1: {len(memory_bank)}, {len(not_self_contained_results)}")
                        return Classifier(client, openai_model_name, claim, memory_bank)
                    else:
                        query_list = [AdditionalQueryGen(client, openai_model_name, claim, memory_bank)] + query_list
                        break
                else:
                    continue
            
            # --- if document isn't self-contained ----
            else:
                if _add_to_list(result, not_self_contained_results):
                    not_self_contained_results.append(result)
    
    # go through documents/webpages that were previously not self-contained and check to see if they are now
    print(f"len(not_self_contained_results)={len(not_self_contained_results)}")
    for result in not_self_contained_results:
        is_self_contained = SelfContainedCheck(client, openai_model_name, claim, memory_bank, result) # boolean
        if is_self_contained:
            helpful = DetHelpful(client, openai_model_name, claim, memory_bank, result) # boolean
            if helpful:
                memory_bank.append(result)
                sufficient = SufficientEvidence(client, openai_model_name, claim, memory_bank)
                if sufficient:
                    print(f"CASE 2: {len(memory_bank)}, {len(not_self_contained_results)}")
                    return Classifier(client, openai_model_name, claim, memory_bank)
    
    # at this point just return a label
    print(f"CASE 3: {len(memory_bank)}, {len(not_self_contained_results)}")
    return Classifier(client, openai_model_name, claim, memory_bank)


def main(args):
    """ Entrypoint """

    print(f"args.use_webextraction_agent={args.use_webextraction_agent}")

    dataset = pd.read_csv(args.dataset).sample(frac=1) # shuffle rows
    SERPER_API_KEY, OPENAI_KEY = get_credentials(args.credentials_path)

    client = OpenAI(api_key=OPENAI_KEY)
    serper = Serper(SERPER_API_KEY)

    if os.path.exists(args.json_pred_path):
        with open(args.json_pred_path) as file:
            predictions = json.load(file)
    else:
        predictions = {}

    for _, row in dataset.iterrows():
        if str(row["id"]) in predictions:
            continue
        claim = row["claim"]
        if type(claim) != str:
            claim = str(claim)
        prediction = fact_check(claim, args.openai_model_name, 
                                client, serper, args.max_search_queries,
                                args.max_search_results_per_query,
                                args.use_webextraction_agent)
        predictions[row["id"]] = prediction
        with open(args.json_pred_path, "w") as file:
            json.dump(predictions, file)


if __name__ == "__main__":
    
    # load arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--credentials_path", type=str, default="../credentials.ini") # path to credentials file
    parser.add_argument("--max_search_queries", type=int) # max search queries
    parser.add_argument("--max_search_results_per_query", type=int) # max number of search results per query
    parser.add_argument("--dataset", type=str) # path to data
    parser.add_argument("--openai_model_name", type=str)
    parser.add_argument("--use_webextraction_agent", action='store_true')
    parser.add_argument("--json_pred_path", type=str) # json file to save predictions to
    args = parser.parse_args()

    main(args)