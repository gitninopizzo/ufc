import requests
def get_data(letter):
    fighters_link = "http://www.ufcstats.com/statistics/fighters?char=" + letter + "&page=all"
    data = requests.get(fighters_link)
    return data

import re
def ends_with_int(line):
    return bool(re.search(r"\d+$", line))
def num_chars(str, char):
    return str.count(char)

from bs4 import BeautifulSoup
def kinda_clean(oneletter):
    soup = BeautifulSoup(oneletter.text)
    texts = soup.get_text().strip()
    better_looking_text = texts.replace("\n\n", "\n")
    better_looking_text = better_looking_text.replace("\n", " ")
    better_looking_text = better_looking_text.replace("  ", " ")
    better_looking_text = better_looking_text.replace("      ", "\n")
    better_looking_text = better_looking_text.replace("\n    ", ";")
    better_looking_text = better_looking_text.replace("\n\n", "  ")
    start = better_looking_text.find("First")
    end = better_looking_text.find("All  ")
    fighter_stats = better_looking_text[start:end]
    fighter_stats = fighter_stats.replace(";Belt\n ", "\n")
    fighter_stats = fighter_stats.replace("\n5", ";5")
    fighter_stats = fighter_stats.replace("\n6", ";6")
    fighter_stats = fighter_stats.replace("\n 6", ";6")
    fighter_stats = fighter_stats.replace("\n 5", ";5")
    start = fighter_stats.find("  1")
    fighter_stats = fighter_stats[:start]
    cleaned = "\n".join(line for line in fighter_stats.splitlines() if not (line.startswith("-") or line.startswith(" -")))
    cleaned = "\n".join(line for line in cleaned.splitlines() if (ends_with_int(line) == True or line.endswith(";D")))
    fighter_stats = cleaned
    fighter_stats = fighter_stats.replace("\n ", "\n -")
    splits = fighter_stats.splitlines()
    count = 1
    for line in splits[1:]:
        names = str.split(line[:line.find(";")], " ")
        names[0] = names[0] + ";"    
        names[1] = names[1] + ";"
        clean_names = " ".join(names)
        clean_names = clean_names.replace(" ", "", 2)
        if len(names) == 2:
            clean_names = clean_names + " "
        final_line = line.replace(line[:line.find(";")], clean_names)
        splits[count] = final_line
        count = count + 1
    fighter_stats = "\n".join(splits)
    return fighter_stats

import pandas as pd
from io import StringIO
def make_letter_df(fighterstats):
    FighterData = StringIO(fighterstats)
    fighterDF = pd.read_csv(FighterData, sep=";")
    return fighterDF

def make_huge_fighter_df():
    alphabet = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
    bigfighterDF = pd.DataFrame()
    for let in alphabet:
        start_data = get_data(let)
        organize = kinda_clean(start_data)
        letterDF = make_letter_df(organize)
        bigfighterDF = pd.concat([bigfighterDF, letterDF])
    return bigfighterDF
result = make_huge_fighter_df()
print(result)