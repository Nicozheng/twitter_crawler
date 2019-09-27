import pandas as pd 
import twitter 
from bs4 import BeautifulSoup as bs
import requests
import sys

api = twitter.Api(consumer_key = 'Ryx62ngOz4LOFLgOgEYIOLhjd',
                    consumer_secret = '0C7KRFwz4SMHidSdunWyCTtyU2ZRNRaGZIgqQ0Qd6U2Z89bKnz',
                    access_token_key = '1115279873092849664-RL6oaGlrXPaI5ui1zo306BIcRpTAj1',
                    access_token_secret = 'mhYP334f9Xl5olPr3jx2elw2SgL6Vct3LIPDAP1Xax0vS')

def get_twitters(username):
    try:
        data = api.GetUserTimeline(screen_name=username, include_rts=False, exclude_replies=False, count=200, max_id="")
        content = [c.text for c in data]
        created_at = [c.created_at for c in data]
        favorite_count = [c.favorite_count for c in data]
        retweet_count = [c.retweet_count for c in data]
        tw_id = [c.id for c in data]
        name = [c.user.screen_name.lower() for c in data]
        result = pd.DataFrame({'username': name, 'tw_id':tw_id, 'content':content, 'created_at':created_at, 'favorite_count': favorite_count, 'retweet_count': retweet_count})
        result['created_at'] = pd.to_datetime(result['created_at'])
        result['created_at'] = result['created_at'].dt.tz_localize(None)
        return result
    except:
        print("error when processing user: %s \n" %username)
        return None

def parse_replies(replies):
    try:
        name = [c.find('div', {'data-component-context':'replies'}).get('data-name') for c in replies]
        content = [c.find("p",{"class":"TweetTextSize js-tweet-text tweet-text"}).text for c in replies]
        time = [c.find("a", {"class":"tweet-timestamp js-permalink js-nav js-tooltip"}).get('title') for c in replies]
        tmp2 = [c.find("span", {"class":"ProfileTweet-action--reply u-hiddenVisually"}) for c in replies]
        r_reply = [c.span.span.text for c in tmp2]
        tmp2 = [c.find("span", {"class":"ProfileTweet-action--retweet u-hiddenVisually"}) for c in replies]
        r_retweet = [c.span.span.text for c in tmp2]
        tmp2 = [c.find("span", {"class":"ProfileTweet-action--favorite u-hiddenVisually"}) for c in replies]
        r_likes = [c.span.span.text for c in tmp2]
        result = pd.DataFrame({"r_name": name ,"r_content": content, "r_time": time, "r_reply": r_reply, "r_retweet": r_retweet, 'r_likes': r_likes})
        return result 
    except:
        return None

def get_replies_info(username, tw_id):
    try:
        r = requests.get("https://twitter.com/" + username + "/status/" + str(tw_id))
        html_soup = bs(r.content, "html.parser")
        tmp = html_soup.find_all("li",{"class":"js-stream-item stream-item stream-item"})
        replies_data = parse_replies(tmp)
        if replies_data is not None:
            replies_data['username'] = username
            replies_data['tw_id'] = tw_id
            return replies_data
        else:
            return None
    except:
        return None

def run(username):
    user_twittes = get_twitters(username)
    if user_twittes is not None:
        replies_info = []
        for i,j in user_twittes[['username','tw_id']].values:
            replies_info.append(get_replies_info(i,j))
        empty_replies = sum([1 for c in replies_info if c is None])
        if empty_replies < len(replies_info):
            replies_info = pd.concat(replies_info)
            reply_count = replies_info.groupby('tw_id').size().to_dict()
            user_twittes['replies_count'] = user_twittes['tw_id'].map(reply_count)
            user_twittes['replies_count'] = user_twittes['replies_count'].fillna(0)
            return user_twittes, replies_info
        else:
            user_twittes['replies_count'] = 0
            return user_twittes, None
    else:
        return None, None

if __name__ == '__main__':

    with open("social_executives_Lee data added female CEOs.csv",'r') as f:
        user_list = f.readlines()
        user_list = [c.strip().replace(",","") for c in user_list]
        user_list = [c for c in user_list if c is not ""]

    all_user_twittes = []
    all_replies_info = []
    cnt = 0
    all_users_cnt = len(user_list[1:])

    for username in user_list[1:]:
        sys.stdout.write(u'processing user: {0}/{1}\r'.format(cnt + 1,all_users_cnt))
        sys.stdout.flush()
        user_twittes, replies_info = run(username)
        all_user_twittes.append(user_twittes)
        all_replies_info.append(replies_info)
        cnt += 1
    all_user_twittes = pd.concat(all_user_twittes)
    all_replies_info = pd.concat(all_replies_info)

    # store to txt
    all_user_twittes.to_csv("all_user_twittes.txt", sep="\t", index=None)
    all_replies_info.to_csv("all_replies_info.txt", sep='\t', index=None)

    # store to csv
    all_user_twittes.to_csv("all_user_twittes.csv", index=None)
    all_replies_info.to_csv("all_replies_info.csv", index=None)