from bs4 import BeautifulSoup
import pandas as pd
import requests
import urllib.request
import time
from datetime import datetime
import os
import re

#Create lists to store the scraped data
authors = []
dates = []
statements = []
sources = []
targets = []
link_url = []


input_data =  input("Enter date (YYYY-MM-DD): ")
specific_date = pd.to_datetime(input_data)

def clean_and_parse_date(date_string):
    # Remove unexpected characters and strip spaces
    cleaned_date_string = date_string.replace("•", "").strip()
    
    # Check if the date string contains a year (using regex to detect four-digit year)
    if re.search(r'\d{4}', cleaned_date_string):
        # Parse the date with the year (flexible for different formats)
        return datetime.strptime(cleaned_date_string, "%B %d, %Y")
    else:
        # If no year is present, parse the date and set the year to 2024
        parsed_date = datetime.strptime(cleaned_date_string, "%B %d,")
        return parsed_date.replace(year=2024)



#Create a function to scrape the site
def scrape_website(page_number, category):
    page_num = str(page_number) #Convert the page number to a string

    '''source: a certain speaker only'''
    URL = 'https://www.politifact.com/factchecks/list/?page={}&category ={}'.format(page_num, category)

    '''source: all'''
    # URL = 'https://www.politifact.com/factchecks/list/?page='+page_num #append the page number to complete the URL

    webpage = requests.get(URL)  #Make a request to the website
    #time.sleep(3)
    soup = BeautifulSoup(webpage.text, "html.parser") #Parse the text from the website
    #Get the tags and it's class
    statement_footer =  soup.find_all('footer',attrs={'class':'m-statement__footer'})  #Get the tag and it's class
    statement_quote = soup.find_all('div', attrs={'class':'m-statement__quote'}) #Get the tag and it's class
    statement_meta = soup.find_all('div', attrs={'class':'m-statement__meta'})#Get the tag and it's class
    target = soup.find_all('div', attrs={'class':'m-statement__meter'}) #Get the tag and it's class
    link = soup.find_all('div', attrs={'class':'m-statement__meter'}) #Get the tag and it's class
    #loop through the footer class m-statement__footer to get the date and author
    for i in statement_footer:
        link1 = i.text.strip()
        name_and_date = link1.split()
        try:
            first_name = name_and_date[1]
        except:
            first_name = ''
        try:
            last_name = name_and_date[2]
        except:
            last_name = ''
        full_name = first_name+' '+last_name
        try:
            month = name_and_date[4]
        except:
            month = ''
        try:
            day = name_and_date[5]
        except:
            day = ''
        try:
            year = name_and_date[6]
        except:
            year = ''
        date = month+' '+day+' '+year
        dates.append(date)
        authors.append(full_name)
        
    #Loop through the div m-statement__quote to get the link
    for i in statement_quote:
        link2 = i.find_all('a')
        statements.append(link2[0].text.strip())
        links = [a['href'] for a in link2]
        for link_url_temp in links:
            #print(link_url_temp)
            link_url.append("https://www.politifact.com" + str(link_url_temp))
    #Loop through the div m-statement__meta to get the source
    for i in statement_meta:
        link3 = i.find_all('a') #Source
        source_text = link3[0].text.strip()
        sources.append(source_text)
    #Loop through the target or the div m-statement__meter to get the facts about the statement (True or False)
    for i in target:
        fact = i.find('div', attrs={'class':'c-image'}).find('img').get('alt')
        targets.append(fact)

#Loop through 'n-1' webpages to scrape the data
n=3
for i in range(1, n):
    scrape_website(i, category='elections')

#Create a new dataFrame
data_election = pd.DataFrame(columns = ['author',  'statement', 'source', 'date', 'target', 'URL'])
data_election['author'] = authors
data_election['statement'] = statements
data_election['source'] = sources
data_election['date'] = dates
data_election['target'] = targets
data_election['URL'] = link_url
data_election['parsed_date'] = data_election['date'].apply(clean_and_parse_date)
data_election['date_column'] = pd.to_datetime(data_election['parsed_date'])
matched_dates = data_election[data_election['date_column'] == specific_date].reset_index(drop = True)
matched_dates.to_csv('Politifact_Data_' + str(input_data) + '.csv', index = False)
