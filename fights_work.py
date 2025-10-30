import re
import pandas as pd
from bs4 import BeautifulSoup

def time_to_seconds(time_str):
  if pd.isna(time_str):
    return 0
  minutes, seconds = map(int, time_str.split(':'))
  return minutes * 60 + seconds

def seconds_to_time(total_seconds):
  minutes = total_seconds // 60
  seconds = total_seconds % 60
  return f"{minutes}:{seconds:02d}"

def get_fight_links_weights_and_when_where(card_data):
    card_soup = BeautifulSoup(card_data.text)
    # need all links with fight-details in it
    temp_fight_links = [a['href'] for a in card_soup.find_all('a', href=True) if "fight-details" in a['href']]
    #print(len(temp_fight_links))
    fight_links = [item for i, item in enumerate(temp_fight_links) if item not in temp_fight_links[:i]]
    #print(len(fight_links))
    # get rid of a lot of spaces also get only the text
    clean_card_text = re.sub(r'\s+', ' ', card_soup.get_text()).strip()
    # put into lines before every appearence of win, draw or nc
    card_text_lines = re.sub(r'\b(win)\b', r'\n\1', clean_card_text)
    card_text_lines = re.sub(r'\b(nc nc)\b', r'\n\1', card_text_lines)
    card_text_lines = re.sub(r'\b(draw draw)\b', r'\n\1', card_text_lines)
    # list form of the lines
    fights = card_text_lines.splitlines()
    # get rid of first line of general info
    general_info = fights.pop(0)
    # get date and location
    regexing = re.match(r'(.*)Date:\s(.*)\sLocation:\s(.*)\sClick(.*)', general_info)
    # make a dictionary to return so multiple pieces of information can be returned
    return_dict = {}
    return_dict["Date"] = regexing.group(2)
    return_dict["Location"] = regexing.group(3)
    # get the weights for every fight with a regex
    weight_list = []
    for f in fights:
        # print(f)
        weight = re.search(r'(?:\d+\s+){8}(.*?[Ww]eight\S*)', f).group(1)
        weight_list.append(weight)
    #print(len(weight_list))
    return_dict["Weights"] = weight_list
    return_dict["Fight Links"] = fight_links
    return return_dict

def get_fight_data(soup, weight):
    # list of all of the links relating to bonuses
    perf_links = ['http://1e49bc5171d173577ecd-1323f4090557a33db01577564f60846c.r80.cf1.rackcdn.com/belt.png', 
                'http://1e49bc5171d173577ecd-1323f4090557a33db01577564f60846c.r80.cf1.rackcdn.com/fight.png', 
                'http://1e49bc5171d173577ecd-1323f4090557a33db01577564f60846c.r80.cf1.rackcdn.com/perf.png', 
                'http://1e49bc5171d173577ecd-1323f4090557a33db01577564f60846c.r80.cf1.rackcdn.com/sub.png',
                'http://1e49bc5171d173577ecd-1323f4090557a33db01577564f60846c.r80.cf1.rackcdn.com/ko.png']
    perf_words = ["Title Fight", "FOTN", "POTN", "SOTN", "KOOTN"]
    # check to see if any of the links are in the fight soup
    check_links_booleans = []
    # get image links from the soup
    check_links = [img['src'] for img in soup.find_all('img', src=True)]
    # make the list of booleans to have True if the link is in the check_links list
    for link in perf_links:
        if link in check_links:
            check_links_booleans.append(True)
        else:
            check_links_booleans.append(False)
    # if the link is there, convert the boolean values to words for more detail on the performance
    extras = [perf_word for perf_word, flag in zip(perf_words, check_links_booleans) if flag]
    extras = " ".join(extras)
    ret_dict = {}
    # get rid of the big spaces with singles spaces in the fight soup text
    clean_fight_text = re.sub(r'\s+', ' ', soup.get_text()).strip()
    # make a new line before the word Round
    fight_text_lines = re.sub(r'\b(Round: )\b', r'\n\1', clean_fight_text)
    fight_text_lines = re.sub(r'\b(Round \d)\b', r'\n\1', fight_text_lines)
    # make a new line before the words Significant Strikes
    fight_text_lines = re.sub(r'\b(Significant Strikes)\b', r'\n\1', fight_text_lines)
    # get rid of all of the text before STAT LEADERS inclusive of STAT LEADERS
    start = fight_text_lines.find("STAT LEADERS ")
    fight_text_lines = fight_text_lines[start + 13:]
    # make a list of the lines and get rid of the last entry of just general things at the end of the page
    lines = fight_text_lines.splitlines()
    lines.pop()
    # get rid of any fighter nicknames in the first line. The first line describes the outcome of the fight
    lines[0] = re.sub(r'"(?:\\.|[^"\\])*"', '', lines[0])
    lines[0] = re.sub(r'\s{2,}', ' ', lines[0]).strip()
    # get the details from the first line of the code
    find_event_results = re.match(r'^(.*?)(?: ([WLD]) | (NC) )(.*?)(?: ([WLD]) | (NC) )(.*)', lines[0])
    # get the event name
    event = find_event_results.group(1).strip()
    ret_dict["Event"] = event
    # get the result of the fighter in the red corner
    ret_dict["Red Corner Result"] = find_event_results.group(2) or find_event_results.group(3)
    # get the red corner fighter name
    f_red_corner = find_event_results.group(4)
    ret_dict["Red Corner Fighter"] = f_red_corner
    # get the result of the fighter in the blue corner
    ret_dict["Blue Corner Result"] = find_event_results.group(5) or find_event_results.group(6)
    # get the part after the blue corner result
    last_part = find_event_results.group(7)
    # get the index of where the weight class is in last part
    end = last_part.find(weight)
    # get the blue corner fighter
    f_blue_corner = last_part[:end]
    # strip blue corner fighter of things that may disrupt the reading of later details 
    f_blue_corner = re.sub(r'\bUFC\b', '', f_blue_corner).strip()
    
    if "Interim" in f_blue_corner:
        extras = "Interim" + extras
    f_blue_corner = re.sub(r'\bInterim\b', '', f_blue_corner).strip()
    f_blue_corner = re.sub(r'\bRoad To\b', '', f_blue_corner).strip()
    f_blue_corner = re.sub(r'\bRoad to\b', '', f_blue_corner).strip()
    f_blue_corner = re.sub(r'\b1\b', '', f_blue_corner).strip()
    #if "Ultimate Fighter" or "Ultimate" or "TUF" in f_blue_corner:
        #extras = "Ultimate Fighter" + extras
    f_blue_corner = re.sub(r'\bUltimate Fighter\b', '', f_blue_corner).strip()
    f_blue_corner = re.sub(r'\bUltimate Japan\b', '', f_blue_corner).strip()
    f_blue_corner = re.sub(r'\bLatin America\b', '', f_blue_corner).strip()
    f_blue_corner = re.sub(r'\bBrazil\b', '', f_blue_corner).strip()
    f_blue_corner = re.sub(r'\bChina\b', '', f_blue_corner).strip()
    f_blue_corner = re.sub(r'\bTUF Nations Canada vs. Australia\b', '', f_blue_corner).strip()
    f_blue_corner = re.sub(r'\bAustralia vs. UK\b', '', f_blue_corner).strip()
    f_blue_corner = re.sub(r'\d+', '', f_blue_corner).strip()
    ret_dict["Blue Corner Fighter"] = f_blue_corner
    # get the result of the fight, KO/TKO/Sub/DQ/Decision/Unanimous/Split
    fight_result = re.search(r'Method:\s*(.*)', last_part).group(1)
    ret_dict["Fight Result"] = fight_result
    more_event_dets = re.match(r'Round:\s*(\d+)\s+Time:\s*(.*)\s+Time format:\s*(.*)\s+Referee:\s*(.*)\s+Details:\s*(.*)(Totals)(.*)', lines[1])
    end_round = int(more_event_dets.group(1))
    ret_dict["End Round"] = end_round
    end_time = more_event_dets.group(2)
    ret_dict["End Time"] = end_time
    time_format = more_event_dets.group(3)
    time_format = int(time_format[:1])
    ret_dict["Scheduled Rounds"] = time_format
    ref = more_event_dets.group(4)
    ret_dict["Referee"] = ref
    details = more_event_dets.group(5)
    ret_dict["Details"] = details.rstrip()
    lines.pop(0)
    # loop and dict for totals
    totals = {}
    for i in range(1, end_round+1):
        chop_str = "Round " + str(i) + " " + f_red_corner + " " + f_blue_corner
        start = lines[i].find(chop_str)
        lines[i] = lines[i][start+len(chop_str)+1:]
        round_values = re.match(r'(\d)\s(\d)\s(\d+)\sof\s(\d+)\s(\d+)\sof\s(\d+)\s(.*)\s(.*)\s(\d+)\sof\s(\d+)\s(\d+)\sof\s(\d+)\s(\d+)\sof\s(\d+)\s(\d+)\sof\s(\d+)\s(.*)\s(.*)\s(\d+)\s(\d+)\s(\d+)\s(\d+)\s(.*)\s(.*)', lines[i])
        totals[f'R{i} RC KD'] = round_values.group(1)
        totals[f'R{i} BC KD'] = round_values.group(2)
        totals[f'R{i} RC SIGSTRLND'] = round_values.group(3)
        totals[f'R{i} RC SIGSTRATT'] = round_values.group(4)
        totals[f'R{i} BC SIGSTRLND'] = round_values.group(5)
        totals[f'R{i} BC SIGSTRATT'] = round_values.group(6)
        totals[f'R{i} RC SIGSTRPER'] = round_values.group(7)
        totals[f'R{i} BC SIGSTRPER'] = round_values.group(8)
        totals[f'R{i} RC TOTSTRLND'] = round_values.group(9)
        totals[f'R{i} RC TOTSTRATT'] = round_values.group(10)
        totals[f'R{i} BC TOTSTRLND'] = round_values.group(11)
        totals[f'R{i} BC TOTSTRATT'] = round_values.group(12)
        totals[f'R{i} RC TDLND'] = round_values.group(13)
        totals[f'R{i} RC TDATT'] = round_values.group(14)
        totals[f'R{i} BC TDLND'] = round_values.group(15)
        totals[f'R{i} BC TDATT'] = round_values.group(16)
        totals[f'R{i} RC TDPER'] = round_values.group(17)
        totals[f'R{i} BC TDPER'] = round_values.group(18)
        totals[f'R{i} RC SUBATT'] = round_values.group(19)
        totals[f'R{i} BC SUBATT'] = round_values.group(20)
        totals[f'R{i} RC REVERSALS'] = round_values.group(21)
        totals[f'R{i} BC REVERSALS'] = round_values.group(22)
        totals[f'R{i} RC CTRLTIME'] = round_values.group(23).split(" ")[0]
        totals[f'R{i} BC CTRLTIME'] = round_values.group(23).split(" ")[1]
    index_list = list(range(end_round+1, end_round+end_round+2))
    new_lines = [lines[i] for i in index_list]
    # loop for sig strikes
    sig_strikes = {}
    for j in range(1, end_round+1):
        chop_str = "Round " + str(j) + " " + f_red_corner + " " + f_blue_corner
        start = new_lines[j].find(chop_str)
        new_lines[j] = new_lines[j][start+len(chop_str)+1:]
        round_values = re.match(r'(\d+)\sof\s(\d+)\s(\d+)\sof\s(\d+)\s(.*)\s(.*)\s(\d+)\sof\s(\d+)\s(\d+)\sof\s(\d+)\s(\d+)\sof\s(\d+)\s(\d+)\sof\s(\d+)\s(\d+)\sof\s(\d+)\s(\d+)\sof\s(\d+)\s(\d+)\sof\s(\d+)\s(\d+)\sof\s(\d+)\s(\d+)\sof\s(\d+)\s(\d+)\sof\s(\d+)\s(\d+)\sof\s(\d+)\s(\d+)\sof\s(\d+)', new_lines[j])
        sig_strikes[f'R{j} RC HEADSTRLND'] = round_values.group(7)
        sig_strikes[f'R{j} RC HEADSTRATT'] = round_values.group(8)
        sig_strikes[f'R{j} BC HEADSTRLND'] = round_values.group(9)
        sig_strikes[f'R{j} BC HEADSTRATT'] = round_values.group(10)
        sig_strikes[f'R{j} RC BODYSTRLND'] = round_values.group(11)
        sig_strikes[f'R{j} RC BODYSTRATT'] = round_values.group(12)
        sig_strikes[f'R{j} BC BODYSTRLND'] = round_values.group(13)
        sig_strikes[f'R{j} BC BODYSTRATT'] = round_values.group(14)
        sig_strikes[f'R{j} RC LEGSTRLND'] = round_values.group(15)
        sig_strikes[f'R{j} RC LEGSTRATT'] = round_values.group(16)
        sig_strikes[f'R{j} BC LEGSTRLND'] = round_values.group(17)
        sig_strikes[f'R{j} BC LEGSTRATT'] = round_values.group(18)
        sig_strikes[f'R{j} RC DISTSTRLND'] = round_values.group(19)
        sig_strikes[f'R{j} RC DISTSTRATT'] = round_values.group(20)
        sig_strikes[f'R{j} BC DISTSTRLND'] = round_values.group(21)
        sig_strikes[f'R{j} BC DISTSTRATT'] = round_values.group(22)
        sig_strikes[f'R{j} RC CLINCHSTRLND'] = round_values.group(23)
        sig_strikes[f'R{j} RC CLINCHSTRATT'] = round_values.group(24)
        sig_strikes[f'R{j} BC CLINCHSTRLND'] = round_values.group(25)
        sig_strikes[f'R{j} BC CLINCHSTRATT'] = round_values.group(26)
        sig_strikes[f'R{j} RC GROUNDSTRLND'] = round_values.group(27)
        sig_strikes[f'R{j} RC GROUNDSTRATT'] = round_values.group(28)
        sig_strikes[f'R{j} BC GROUNDSTRLND'] = round_values.group(29)
        sig_strikes[f'R{j} BC GROUNDSTRATT'] = round_values.group(30)
    ret_dict["Bonuses"] = extras
    ret_dict["Fight Totals"] = totals
    ret_dict["Sig Strikes"] = sig_strikes
    return ret_dict

import requests
all_fights_card = []
# replace link every time for new cards
lin = "http://www.ufcstats.com/event-details/7956f026e2672c47"
card_dets = get_fight_links_weights_and_when_where(requests.get(lin))
# iterate through all fight links and weights together
for l, w in zip(card_dets["Fight Links"], card_dets["Weights"]):
    # get the data from the fight
    fight_data = requests.get(l)
    fight_soup = BeautifulSoup(fight_data.text)
    fight_info = get_fight_data(fight_soup, w)
    fight = {"Event": fight_info["Event"], "Date": card_dets["Date"], "Location": card_dets["Location"], 
                "Weight": w}
    # remove totals and sig strikes from the fight info return in order to add to fight dictionary better
    sign_strikes = fight_info.popitem()
    tots = fight_info.popitem()
    fight_info.pop("Event")
    # add the things popped into the fight dictionary
    fight.update(fight_info)
    fight.update(tots[1])
    fight.update(sign_strikes[1])
    all_fights_card.append(fight)
last_card_df = pd.DataFrame(all_fights_card)
last_card_df.to_csv('last_card.csv', sep=";", index=False)

last_card_df = pd.read_csv('last_card.csv', sep=';')
keywords = ["RC KD", "BC KD", "RC SIGSTRLND", "RC SIGSTRATT", "BC SIGSTRLND", "BC SIGSTRATT", 
            "RC TOTSTRLND", "RC TOTSTRATT", "BC TOTSTRLND", "BC TOTSTRATT", "RC TDLND", 
            "RC TDATT", "BC TDLND", "BC TDATT", "RC SUBATT", "BC SUBATT", "RC REVERSALS", 
            "BC REVERSALS", "RC CTRLTIME", "BC CTRLTIME", "RC HEADSTRLND", "RC HEADSTRATT", 
            "BC HEADSTRLND", "BC HEADSTRATT", "RC BODYSTRLND", "RC BODYSTRATT", "BC BODYSTRLND", 
            "BC BODYSTRATT", "RC LEGSTRLND", "RC LEGSTRATT", "BC LEGSTRLND", "BC LEGSTRATT", 
            "RC DISTSTRLND", "RC DISTSTRATT", "BC DISTSTRLND", "BC DISTSTRATT", "RC CLINCHSTRLND", 
            "RC CLINCHSTRATT", "BC CLINCHSTRLND", "BC CLINCHSTRATT", "RC GROUNDSTRLND", "RC GROUNDSTRATT", 
            "BC GROUNDSTRLND", "BC GROUNDSTRATT"]
for keyword in keywords:
    selected_columns = [col for col in last_card_df.columns if keyword in col]
    if "CTRLTIME" in keyword:
        temp_fights_df = last_card_df[selected_columns].copy()
        for column in selected_columns:
            temp_fights_df[column] = temp_fights_df[column].apply(time_to_seconds)
        last_card_df["TOT " + keyword] = temp_fights_df.sum(axis=1)
        last_card_df["TOT " + keyword] = last_card_df["TOT " + keyword].apply(seconds_to_time)
    else:
        last_card_df["TOT " + keyword] = last_card_df[selected_columns].fillna(0).sum(axis=1)
# get the big fights df from my files and read it in
fights_df = pd.read_csv('fights.csv')
# add the page worth of cards to the fights df
fights_df = pd.concat([last_card_df, fights_df], ignore_index=True)
# save the fights df as a csv file
fights_df.to_csv('fights.csv', index=False)