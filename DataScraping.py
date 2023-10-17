"""
DataScraping.py
Purpose: 
    Read in data sources about employment, wage, cost of living, 
    and house price by state. Scraped 2 sources from web and 
    manually entered data as csv file for employment and wage.
    Cleaned and merged three data sources as csv to be imported 
    by MoveWise.py for EDA and GUI.
    
Python Group C2
    @author 1: Anni Kang;          andrew id: annik
    @author 2: Harshita Agrawal;   andrew id: hagrawa2
    @author 3: Yingyuan Lin;       andrew id: yingyual
    @author 4: Zheyu Yan;          andrew id: zheyuyan
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# Scraping and Loading Data
# read in average rent by state information from web scraping
url = "https://wisevoter.com/state-rankings/average-rent-by-state/"
response = requests.get(url)
# scrape data 
if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': 'shdb-on-page-table'})
    data = []

    for row in table.find_all('tr')[1:]:
        columns = row.find_all('td')
        state = columns[1].text.strip()
        median_rent_price = int(columns[2].text.strip().replace('$', '').replace(',', ''))
        vacancy_rate = float(columns[3].text.strip().replace('%', ''))
        housing_units = int(columns[4].text.strip().replace(',', ''))
        median_home_price_text = columns[5].text.strip().replace('$', '').replace(',', '')
        median_home_price = int(median_home_price_text) if median_home_price_text else None

        data.append([state, median_rent_price, vacancy_rate, housing_units, median_home_price])
    # select useful columns for analysis
    columns = ['State', 'Median Rent Price ($)', 'Rental Vacancy Rate (%)', 'Occupied Housing Units', 'Median Home Price($)']
    rent_by_state = pd.DataFrame(data, columns=columns)
    # sort data by state names alphabetically
    rent_by_state = rent_by_state.sort_values(by='State', ascending=True)
    # reset index
    rent_by_state = rent_by_state.reset_index()
    rent_by_state = rent_by_state.drop(columns = 'index')
    # store scraped data 
    rent_by_state.to_csv('rental_data.csv', index=False)



# read in cost of living per state data from web scraping
url = "https://meric.mo.gov/data/cost-living-data-series"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
table = soup.find('table')
table_div = soup.find('div', {'class': 'table-responsive'})
if table_div:
    table = table_div.find('table')
    headers = [th.text.strip() for th in table.find_all('th')]
    # Extract table rows
    rows = table.find_all('tr')[1:]  # Exclude header row

    data = []
    for row in rows:
        columns = row.find_all('td')
        row_data = {headers[i]: columns[i].text.strip() for i in range(len(columns))}
        data.append(row_data)

    # Convert to DataFrame
    cost_of_living = pd.DataFrame(data)
    file_path = os.path.abspath('cost_of_living.csv')
    cost_of_living.to_csv(file_path, index=False)

# read in employment data by state information from manually cleaned csv
wage_by_state = pd.read_csv("EmploymentandWage_updated.csv")

# sort cost_of_living by state alphabetically 
cost_of_living = cost_of_living.sort_values(["State"], ascending=True)
# delete rows for total sum (index 52) and Puerto Rico (index 27) 
cost_of_living = cost_of_living.drop(index=52)
cost_of_living = cost_of_living.drop(index = 27)
# drop unnecessary columns
cost_of_living = cost_of_living.drop(columns=["Rank"])
# reset index
cost_of_living = cost_of_living.reset_index()
cost_of_living = cost_of_living.drop(columns = "index")

# drop rows for Puerto Rico (index 39) and reset index 
wage_by_state = wage_by_state.drop(index = 39)
wage_by_state = wage_by_state.reset_index()
wage_by_state = wage_by_state.drop(columns = "index")
wage_by_state

# merge 3 dataframes by states
merged_df = pd.merge(rent_by_state, cost_of_living, on='State')
merged_df = pd.merge(wage_by_state, merged_df, on='State')


# Data Cleaning
# rename column names that are too long
merged = merged_df.rename(columns={"Median Hourly Wage ($)": "Median Hourly Wage", 
"Mean Hourly Wage ($)": "Mean Hourly Wage","Annual Mean Wage ($)": "Annual Mean Wage", 
"Median Rent Price ($)": "Median Rent", "Rental Vacancy Rate (%)": "Rental Vacancy", 
"Median Home Price($)": "Median Home Price" })

# Fill Nan values
merged['Median Home Price'] = merged["Median Home Price"].fillna(method = 'ffill')

# Export final data
merged.to_csv("merged_data.csv", sep=',', index=False, encoding='utf-8')
