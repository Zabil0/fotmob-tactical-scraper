# Tactical Football Scraper ⚽️📊

A Python tool built to scrape advanced tactical match data from FotMob, focusing on the relationship between high possession and attacking penetration/defensive vulnerability.

This tool utilizes Selenium and BeautifulSoup to navigate dynamic JavaScript elements and extract deep match stats like "Touches in the opposition box", "Opposition half passes", and "Expected Goals (xG)".

## Key Features
* **Possession Filtering:** Automatically identifies the dominant team (>= 54% possession) in a given match.
* **Sterile Possession Tracking:** Measures actual attacking penetration using box touches and passes in the final third.
* **Rest Defense Analysis:** Extracts the counter-attacking metrics (Shots, Big Chances, xG) of the opposition team to evaluate the dominant team's defensive vulnerability.

## Prerequisites & Installation

This scraper requires Google Chrome and several Python libraries.

## Additional Notes

Anyone can change the season and league id variables. 

Common FotMob League IDs:
47 - Premier League
54 - Bundesliga
55 - Serie A
87 - La Liga
