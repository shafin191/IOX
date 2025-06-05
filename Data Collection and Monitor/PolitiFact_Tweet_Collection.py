import asyncio
import csv
import time
import twikit
import os
from twikit import Client
from twikit.errors import TooManyRequests
from datetime import datetime
import random
import pandas as pd
import pickle
import re
from bs4 import BeautifulSoup
import requests
import urllib.request

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


def scrape_website(page_number, category):
    page_num = str(page_number) #Convert the page number to a string

    URL = 'https://www.politifact.com/factchecks/list/?page={}&category ={}'.format(page_num, category)
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
politifact_results_path ='/aul/homes/msidd040/twikit/demo_data/politifact_data/Politifact_Data_' + str(input_data) + '.csv'
matched_dates.to_csv(politifact_results_path, index = False)


# Initialize client
client = Client('en-US')
current_date = datetime.today()

async def main():
    client.load_cookies('/aul/homes/msidd040/twikit/tweet_August_september/cookie.json')
    # Saving the tweets for Politifact reports
    file_path = politifact_results_path
    output_file_path = '/aul/homes/msidd040/twikit/demo_data/tweet_results/tweet_results_'+ str(input_data) + '.csv'
    
    search_types = ['Latest', 'Top']
    
    file_exists = os.path.isfile(output_file_path)
    # Open the output CSV file for appending
    with open(output_file_path, mode='a', newline='', encoding='utf-8') as output_file:
        writer = csv.writer(output_file)

        # Write the header row if the file is newly created
        if not file_exists:
            writer.writerow([
                "Search_Statement", "Target", "Search_Type","Tweet_ID","Tweet_ID_String","Tweet","Tweet_Full_Text","User_ID","User_ID_String","User_name", "Screen_name", "Created_at",
                "Datetime", "Language", "View_count", "Favorite_count", "Retweet_count","Reply_Count","Hashtag","Community_Note","Tweet_link"
            ])
       

        

        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            # for _ in range(start_row - 1):
            #     next(reader, None)

            for row in reader:
                statement = row['statement']
                target=row['target']
                for search_type in search_types:
                    while True:
                        try:
                            tweets = await client.search_tweet(statement, search_type)
                            for tweet in tweets:
                            # Write the tweet data to the CSV file
                                writer.writerow([
                                    statement,
                                    target,
                                    search_type,
                                    tweet.id,
                                    str(tweet.id),
                                    str(tweet.text),
                                    str(tweet.full_text),
                                    tweet.user.id,
                                    str(tweet.user.id),
                                    tweet.user.name,
                                    tweet.user.screen_name,
                                    tweet.created_at,
                                    tweet.created_at_datetime,
                                    tweet.lang,
                                    tweet.view_count,
                                    tweet.favorite_count,
                                    tweet.retweet_count,
                                    tweet.reply_count,
                                    tweet.hashtags,
                                    tweet.has_community_notes,
                                    tweet.urls  
                                ])
                            await asyncio.sleep(30)
                            break  # Break the loop if the request is successful
                        except TooManyRequests:
                            #elapsed_time = time.time() - start_time
                            wait_time = 15*60
                            print(f"Rate limit exceeded. Waiting for {wait_time / 60:.2f} minutes...")
                            await asyncio.sleep(wait_time)
                            #start_time = time.time() 
    
    df_new = pd.read_csv(output_file_path)
    all_user = df_new.User_ID.tolist()
    base_folder = '/aul/homes/msidd040/twikit/demo_data/ID_collection'
    os.makedirs(base_folder, exist_ok=True)

    df_user_id = pd.DataFrame(all_user, columns=['User_ID'])

    file_name = base_folder + '/' + str(input_data) + '_user_id'

    df_user_id.to_csv(file_name + '.csv', index=False)

    df_user_id.to_csv(file_name + '.txt', index=False, header=False)
    
    newpath = "/aul/homes/msidd040/twikit/demo_data/Monitor_All_account/" +  str(input_data) + "/"
    check_num = 0
    user_prob = []
    

    for k in all_user:
        try:
            user_info = await client.get_user_by_id(k)
        except:
            print(str(k) + ' was a problem')
            user_prob.append(k)
            await asyncio.sleep(10)
            

        user_to_store = []
        user_to_store.append({
        'User_ID':user_info.id,
        'ScreenName':user_info.screen_name,
        'Created_At': user_info.created_at,
        'UserName':user_info.name,
        'Default_Image':user_info.default_profile_image,
        'User_Description':user_info.description, 
        'User_Description_URL':user_info.description_urls, 
        'Fast_Follower_Count':user_info.fast_followers_count,
        'Normal_Follower_Count':user_info.normal_followers_count,
        'Favorite_Count':user_info.favourites_count, 
        'Follower_Count':user_info.followers_count, 
        'Friend_Count':user_info.following_count,
        'Total_Status_Count':user_info.statuses_count,
        'Custom_Timeline':user_info.has_custom_timelines,
        'Blue_Verified':user_info.is_blue_verified,
        'Veified':user_info.verified,
        'Is_Translator':user_info.is_translator,
        'Listed_Count':user_info.listed_count,
        'User_Location':user_info.location,
        'Media_Count':user_info.media_count,        
        'Pinned_Tweet_ID':user_info.pinned_tweet_ids,
        'Sensitivity':user_info.possibly_sensitive,
        'Profile_Banner_Link':user_info.profile_banner_url,
        'Profile_Image_Link':user_info.profile_image_url,
        'Is_Protected':user_info.protected,
        'Post_Count':user_info.statuses_count,
        'Translatory_Type':user_info.translator_type,
        'Banned_In_Countries':user_info.withheld_in_countries,
        'URL':user_info.url,
        'URL2':user_info.urls
        })
       

        
        check_num = check_num + 1

        df_user = pd.DataFrame(user_to_store)
        # Selecting the directory
        csv_path = '/aul/homes/msidd040/twikit/demo_data/User_data/'+str(input_data)+'/'
        pickle_path = '/aul/homes/msidd040/twikit/demo_data/User_data/Pickle/'+str(input_data)+'/'
        # Path creation if not exits
        os.makedirs(csv_path, exist_ok=True)
        os.makedirs(pickle_path, exist_ok=True)
        #Change the direcotry
        df_user.to_csv(csv_path +str(k) +'_User.csv', index = False)
        
        with open(pickle_path+ str(k)+ '.pkl', 'wb') as f:
            pickle.dump(user_to_store, f)
       
            
        time.sleep(10)
        if check_num%1000 == 0:
            print('Check_Point : ' + str(check_num))
            await asyncio.sleep(15)
        


    if not os.path.exists(newpath):
        os.makedirs(newpath)


    df_group_list = all_user
    random.shuffle(df_group_list)
    check_num = 0
    user_prob2 = []

    for k in df_group_list:
        check_num = check_num + 1
        try:
            tweets = await client.get_user_tweets(user_id = k,tweet_type ='Tweets',count=20)
            #user_following3 = clientget_user_following(k)
        except:
            print(str(k) + ' was a problem.')
            user_prob2.append(k)
            await asyncio.sleep(20)
            continue
        
        tweets_to_store = []
        for tweet in tweets:
            if tweet.text[0:4] == 'RT @':
                #print('This is a Retweet')
                tweets_to_store.append({
                    'User_ID': tweet.user.id,
                    'Tweet_ID': tweet.id,
                    'Retweet_ID': tweet.retweeted_tweet.id,
                    'Retweet_User_ID': tweet.retweeted_tweet.user.id,
                    'created_at': tweet.created_at,
                    'Retweet_created_at':tweet.retweeted_tweet.created_at,
                    'favorite_count': tweet.favorite_count,
                    'retweet_count': tweet.retweet_count,
                    'media':tweet.media,
                    'Retweet_Media': tweet.retweeted_tweet.media,
                    'text': tweet.text,
                    'Retweet_Text': tweet.retweeted_tweet.text,
                    'full_text': tweet.full_text,
                    'Text_Lang': tweet.lang,
                    'Retweet_Lang': tweet.retweeted_tweet.lang,
                    'View_Count': tweet.view_count,
                    'Comment_Count':tweet.reply_count,
                    'Quote_Count': tweet.quote_count,
                    'Text_Hashtags':tweet.hashtags,
                    'has_community_note': tweet.has_community_notes, 
                    'Link': tweet.urls,       
                    'Data_Collection_Time': datetime.now()
                    })
            else:
                #print('This is a Tweet')
                tweets_to_store.append({
                    'User_ID': tweet.user.id,
                    'Tweet_ID': tweet.id,
                    'created_at': tweet.created_at,
                    'favorite_count': tweet.favorite_count,
                    'retweet_count': tweet.retweet_count,
                    'media':tweet.media,
                    'text': tweet.text,
                    'full_text': tweet.full_text,
                    'Text_Lang': tweet.lang,
                    'View_Count': tweet.view_count,
                    'Comment_Count':tweet.reply_count,
                    'Quote_Count': tweet.quote_count,
                    'Text_Hashtags':tweet.hashtags,
                    'has_community_note': tweet.has_community_notes, 
                    'Link': tweet.urls,       
                    'Data_Collection_Time': datetime.now()})


        with open(newpath + "Tweet_"+ str(k)+ ".pkl", "wb") as f:
            pickle.dump(tweets_to_store, f)
        try:
            df_tweet = pd.DataFrame(tweets_to_store)
            df_tweet.to_csv(newpath +str(k) +"_Tweets.csv", index = False)
        except:
            print('Problem')

        await asyncio.sleep(20)
        if check_num%100 == 0:
            await asyncio.sleep(60)
    
         
asyncio.run(main())