"""
FotMob Tactical Matchup Scraper
Extracts and categorizes team possession and penetration metrics.
"""

import json
import time
import re
import argparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm

# --- Data Extraction Helpers ---
def find_stat(data, stat_title):
    if isinstance(data, dict):
        if data.get('title') == stat_title and 'stats' in data: return data['stats']
        for value in data.values():
            res = find_stat(value, stat_title)
            if res is not None: return res
    elif isinstance(data, list):
        for item in data:
            res = find_stat(item, stat_title)
            if res is not None: return res
    return None

def find_match_list(data):
    if isinstance(data, dict):
        if 'allMatches' in data: return data['allMatches']
        for value in data.values():
            res = find_match_list(value)
            if res is not None: return res
    elif isinstance(data, list):
        for item in data:
            res = find_match_list(item)
            if res is not None: return res
    return None

def extract_first_int(val):
    if val is None: return 0
    match = re.search(r'\d+', str(val))
    return int(match.group()) if match else 0

def extract_float(val):
    if val is None: return 0.0
    match = re.search(r'\d+\.\d+|\d+', str(val))
    return float(match.group()) if match else 0.0

# --- Core Scraper Logic ---
def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.add_argument("--log-level=3")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scrape_season(league_id, season_string):
    driver = setup_driver()
    
    total_high_poss_games = 0
    total_touches_opp_box = 0
    total_opp_half_passes = 0
    total_opp_shots = 0
    total_opp_xg = 0.0
    total_opp_big_chances = 0

    print(f"\n--- Loading Schedule for League {league_id} | Season {season_string} ---")
    driver.get(f"https://www.fotmob.com/leagues/{league_id}/matches?season={season_string}")
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    next_data_script = soup.find('script', id='__NEXT_DATA__')

    if not next_data_script:
        print("Error: Could not locate match data on the page.")
        driver.quit()
        return

    page_data = json.loads(next_data_script.text)
    matches = find_match_list(page_data)

    if not matches:
        print("Error: Could not parse match list.")
        driver.quit()
        return

    finished_match_ids = [m['id'] for m in matches if m.get('status', {}).get('finished') is True]
    print(f"Found {len(finished_match_ids)} finished matches. Commencing scrape...")

    for match_id in tqdm(finished_match_ids, desc=f"Processing {season_string}", unit="match"):
        driver.get(f"https://www.fotmob.com/match/{match_id}")
        time.sleep(1.2) # Polite scraping delay

        match_soup = BeautifulSoup(driver.page_source, 'html.parser')
        match_script = match_soup.find('script', id='__NEXT_DATA__')
        if not match_script: continue

        match_data = json.loads(match_script.text)

        try:
            possession = find_stat(match_data, "Ball possession")
            touches = find_stat(match_data, "Touches in opposition box")
            opp_half_passes = find_stat(match_data, "Opposition half")
            shots = find_stat(match_data, "Total shots")
            xg = find_stat(match_data, "Expected goals (xG)")
            big_chances = find_stat(match_data, "Big chances")

            if not possession or not touches or not opp_half_passes: continue

            h_poss = extract_first_int(possession[0])
            a_poss = extract_first_int(possession[1])

            if h_poss >= 54:
                total_high_poss_games += 1
                total_touches_opp_box += extract_first_int(touches[0])
                total_opp_half_passes += extract_first_int(opp_half_passes[0])
                total_opp_shots += extract_first_int(shots[1]) if shots else 0
                total_opp_xg += extract_float(xg[1]) if xg else 0.0
                total_opp_big_chances += extract_first_int(big_chances[1]) if big_chances else 0

            elif a_poss >= 54:
                total_high_poss_games += 1
                total_touches_opp_box += extract_first_int(touches[1])
                total_opp_half_passes += extract_first_int(opp_half_passes[1])
                total_opp_shots += extract_first_int(shots[0]) if shots else 0
                total_opp_xg += extract_float(xg[0]) if xg else 0.0
                total_opp_big_chances += extract_first_int(big_chances[0]) if big_chances else 0

        except Exception as e:
            # Silently pass missing data structures to avoid breaking the loop
            pass

    # Averages Calculation
    avg_touches = round(total_touches_opp_box / total_high_poss_games, 1) if total_high_poss_games > 0 else 0
    avg_opp_passes = round(total_opp_half_passes / total_high_poss_games, 1) if total_high_poss_games > 0 else 0
    avg_opp_shots = round(total_opp_shots / total_high_poss_games, 1) if total_high_poss_games > 0 else 0
    avg_opp_xg = round(total_opp_xg / total_high_poss_games, 2) if total_high_poss_games > 0 else 0.0
    avg_opp_bc = round(total_opp_big_chances / total_high_poss_games, 1) if total_high_poss_games > 0 else 0

    print(f"\n{'='*65}")
    print(f"RESULTS: League ID {league_id} | Season {season_string}")
    print(f"{'='*65}")
    print(f"Total >= 54% Possession Games: {total_high_poss_games}")
    if total_high_poss_games > 0:
        print(f"Dominant Team - Avg Touches in Box: {avg_touches}")
        print(f"Dominant Team - Avg Passes in Opp. Half: {avg_opp_passes}")
        print(f"--- OPPOSITION COUNTER-ATTACK THREAT ---")
        print(f"Opposition - Avg Shots per game: {avg_opp_shots}")
        print(f"Opposition - Avg xG per game: {avg_opp_xg}")
        print(f"Opposition - Avg Big Chances per game: {avg_opp_bc}")

    driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape tactical football data from FotMob.")
    parser.add_argument("--league", type=int, default=47, help="FotMob League ID (Default: 47 for Premier League)")
    parser.add_argument("--season", type=str, default="2024-2025", help="Season format YYYY-YYYY (e.g., 2024-2025)")
    args = parser.parse_args()
    
    scrape_season(args.league, args.season)