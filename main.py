import artScraper
import json, tweepy

if __name__ == "__main__":
    
    #rGet the credencials to use Twitter api
    with open('credencials.txt','r') as f:
        credencials = json.load(f)
    api_key = credencials['tw_api_key']
    api_key_secret = credencials['tw_api_key_secret']
    bearer_token = credencials['tw_bearer_token']
    access_token = credencials['tw_access_token']
    access_token_secret = credencials['tw_access_token_secret']
    
    # V1 authentication
    auth = tweepy.OAuthHandler(api_key, api_key_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)

    # v2 authentication
    client = tweepy.Client(bearer_token,api_key, api_key_secret, access_token, access_token_secret)
    
    # Get the text and paintings names to use in the download process
    tweet_text, paintings_names= artScraper.start_process()
    media_ids = []
    
    # Uploads the pictures on twitter server
    # if the picture can not be published it will skip it over
    for painting in paintings_names:
        try:
            res = api.media_upload(painting+'.jpg')
            media_ids.append(res.media_id)
        except:
            pass
    # Publish the tweet
    try:
        client.create_tweet(text=tweet_text, media_ids=media_ids)
    except:
        pass
