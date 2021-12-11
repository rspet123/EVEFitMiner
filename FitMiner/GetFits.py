import requests
import pickle
from tqdm import tqdm
from os.path import exists
import os
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
import math
from time import time
def encode_itemsets(itemsets,all_list):
    all_items = []
    
    frame1 = []
    for itemset in itemsets:
        for item in itemset:
            if item not in all_items:
                all_items.append(item)
    all_list = all_items
    df = pd.DataFrame(columns= all_list)
    for itemset in itemsets:
        curr_set = [False for i in range(len(all_list))]
        for item in itemset:
            curr_set[all_list.index(item)] = True
        frame1.append(curr_set)
        df = pd.DataFrame(frame1,columns = all_list)
    return df
            
reaquire_fits = False
tot_list= []
inv_types = {}
num_fits = 200
num_pages = math.ceil(num_fits/200)
support_items = {}
killmail_list = []
for page in range(num_pages):
    killmail_list.extend(requests.get("https://zkillboard.com/api/losses/regionID/10000060/page/" + str(page+1)+"/").json())
if not exists("Resources/invTypes.kte"):
    inv_types = {row[0] : row[2] for _, row in pd.read_csv("Resources/invTypes.csv").iterrows()}
    with open('Resources/invTypes.kte', 'wb') as handle:
        pickle.dump(inv_types, handle, protocol=pickle.HIGHEST_PROTOCOL)
else:
    with open('Resources/invTypes.kte', 'rb') as handle:
        inv_types = pickle.load(handle)
itemset_list = []
#Getting All Items
if exists("Resources/itemSets.kte"):
    try:
        #We check if our data file is good, IE, it is valid and up to date
        with open("Resources/itemSets.kte", 'rb') as handle:
                last_data = pickle.load(handle)
                last_load = last_data[1]
                last_len = last_data[2]
        if (time()-last_load > 3000) or (last_len < num_fits) or reaquire_fits:
            #if the data is old, or we request more fits than we have in memory, we're going to rebuild the data file
            os.remove("Resources/itemSets.kte")
    except Exception:
        os.remove("Resources/itemSets.kte")
        
if not exists("Resources/itemSets.kte"):
    for killmail in tqdm(killmail_list[:num_fits]):
        items = []
        km_id = killmail["killmail_id"]
        km_hash = killmail["zkb"]["hash"]
        current_killmail = requests.get("https://esi.evetech.net/latest/killmails/" + str(km_id) + "/" + km_hash + "/?datasource=tranquility").json()
        ship = inv_types[current_killmail["victim"]["ship_type_id"]]
        if not ship == "Capsule":
            items.append(ship)
            try:
                for item in current_killmail["victim"]["items"]:
                    items.append(inv_types[item["item_type_id"]])
            except KeyError:
                continue
            itemset_list.append(items)
    with open("Resources/itemSets.kte", 'wb') as handle:
        pickle.dump((itemset_list,time(),num_fits), handle, protocol=pickle.HIGHEST_PROTOCOL)
else:
    with open("Resources/itemSets.kte", 'rb') as handle:
        itemset_list = pickle.load(handle)[0]
encoded_sets = encode_itemsets(itemset_list,tot_list)

frq_items = apriori(encoded_sets, min_support = 0.03, use_colnames = True)
rules = association_rules(frq_items, metric ="lift", min_threshold = .5)
rules = rules.sort_values(['confidence', 'lift'], ascending =[False, False])
print(rules.head())    