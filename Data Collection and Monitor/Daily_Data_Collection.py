import asyncio
import os
import twikit
import random
import datetime
import pickle
import time
import pandas as pd
import sys
import json

# No need to write "from twikit.twikit_async import Client"
from twikit import Client

#client = Client()


async def main() -> None:
    now = datetime.datetime.now()
    current_date = now.date()
    client = Client("en-US")
    print(twikit.__version__)
    #client.load_cookies('cookie_JohnFisher.json')
    client.load_cookies('adam_kane_cookie.json')
    my_list = []
    
    with open("", "r") as fp:
        my_list = json.load(fp)
        
    newpath = "" +  str(current_date) + "/"
    if not os.path.exists(newpath):
        os.makedirs(newpath)
        
    df_group_list =my_list

    check_num = 0
    user_prob2 = []
    
    for k in df_group_list:
        check_num = check_num + 1
        #tweets = await client.get_user_tweets(user_id = k,tweet_type ='Tweets')
        #print(tweets)
        #exit()
       
        try:
            tweets = await client.get_user_tweets(user_id = k,tweet_type ='Tweets')
            #user_following3 = clientget_user_following(k)
           
        except:
            print(str(k) + ' was a problem.')
            user_prob2.append(k)
            time.sleep(30)
            continue
        
        tweets_to_store = []
        for tweet in tweets:
            if tweet.text[0:4] == 'RT @':
                #print('This is a Retweet')
                try:
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
                        'Retweet_Lang':tweet.retweeted_tweet.lang,
                        'View_Count': tweet.view_count,
                        'Comment_Count':tweet.reply_count,
                        'Quote_Count': tweet.quote_count,
                        'Text_Hashtags':tweet.hashtags,
                        'has_community_note': tweet.has_community_notes, 
                        'Link': tweet.urls,       
                        'Data_Collection_Time': datetime.datetime.now()
                
                    })
                except:
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
                        'Data_Collection_Time': datetime.datetime.now()})
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
                    'Data_Collection_Time': datetime.datetime.now()})
        #print(tweets)
        with open(newpath + "Tweet_"+ str(k)+ "_" + str(check_num) +".pkl", "wb") as f:
            pickle.dump(tweets_to_store, f)
        try:
            df_tweet = pd.DataFrame(tweets_to_store)
            df_tweet.to_csv(newpath +str(k) +"_" + str(check_num) +"_Tweets.csv", index = False)
        #df_user.to_csv('V:/SBERT All Embedding/Following_List/' +str(k) +'_Following.csv')
        except:
            print('Problem')

        time.sleep(30)
        #break
        if check_num%100 == 0:
            time.sleep(20)
            


    print("Program Execution Complete")
    print("Total_Problem: " + str(len(user_prob2)))


asyncio.run(main())
sys.exit()
