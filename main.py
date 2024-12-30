
# ========== DON'T FORGET TO DEPLOY THE CODE USING THE FOLLOWING COMMAND ==========
# gcloud functions deploy post-wiki-to-twitter --gen2 --runtime python39 --region us-east1 --source . --entry-point post_to_twitter --trigger-topic=post-tweet-topic
# =================================================================================

from google.cloud import secretmanager
import tweepy
import wikipedia
import random
import os
import base64

# Secret Manager Client
client = secretmanager.SecretManagerServiceClient()

def access_secret_version(secret_id, project_id, version_id="latest"):
    """Helper function to access secrets."""
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def get_random_wikipedia_page(options=None, recursion_depth=5):
    """Fetches a random Wikipedia page and its URL."""
    if recursion_depth == 0:
        print("Maximum recursion depth reached.")
        return "Error message", "https://en.wikipedia.org/wiki/Error_message"
    try:
        if options == None:
            random_page = wikipedia.random(1)
            page = wikipedia.page(random_page)
        else:
            s = random.choice(options)
            page = wikipedia.page(s)
    except wikipedia.exceptions.DisambiguationError as e:
        print(f"DisambiguationError: {e}")
        print(f"Options: {e.options}")
        return get_random_wikipedia_page(e.options, recursion_depth=recursion_depth-1)
    except wikipedia.exceptions.PageError:
        return get_random_wikipedia_page(recursion_depth=recursion_depth-1)
    return page.title, page.url

def post_to_twitter(event, context):
    #print('Function called.')
    """Cloud Function triggered by Cloud Scheduler via Pub/Sub."""
    project_id = "twitter-bot-project-445900"
    print(f'Project ID is {project_id}')

    consumer_key = access_secret_version("twitter-consumer-key", project_id)
    consumer_secret = access_secret_version("twitter-consumer-secret", project_id)
    access_token = access_secret_version("twitter-access-token", project_id)
    access_token_secret = access_secret_version("twitter-access-token-secret", project_id)
    #print('Credentials fetched.')

    #auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    #auth.set_access_token(access_token, access_token_secret)
    #api = tweepy.API(auth)
    api = tweepy.Client(consumer_key=consumer_key,
                        consumer_secret=consumer_secret,
                        access_token=access_token,
                        access_token_secret=access_token_secret)
    #print('API ready.')

    title, url = get_random_wikipedia_page()
    if title == "Error message":
        tweet_text = f"Something went wrong. - {title}\n{url}"
    else:
        tweet_text = f"Check out this interesting Wikipedia page: {title}\n{url}"
    print(f'Selected wikipedia page: {title}')

    try:
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        print(f"Received message from Pub/Sub: {pubsub_message}")

        api.create_tweet(text=tweet_text)
        print(f"Tweet posted: {tweet_text}")

    except tweepy.TweepyException as e:
        print(f"Error posting tweet: {e}")

    except Exception as e:
        print(f"An error occurred: {e}")