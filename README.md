# Recyclables

Singapore's 1st Karung Guni hailing bot

Our goal is to improve Singapore’s domestic recycling efforts by partnering with the local karung guni community. By bridging the gap between residents and the collectors via a digital platform, household recycling is made more convenient and at the same time, it reduces recycling waste contamination which makes recycling overall more effective.

## Table of contents

* Requirements

* Misc

## Requirements to install (Follow the order)

1. Clone repo

2. [Create a virtual environment](https://uoa-eresearch.github.io/eresearch-cookbook/recipe/2014/11/26/python-virtual-env/), your env folder should be in the same directory as your clone.

3. Activate env and install the necessary packages/ modules:

```python
  pip install -r requirements.txt
```
4. Create your own .env file and paste your own Telegram bot token + Groupchat id inside:
```python
TELEGRAM_TOKEN = YOUR TOKEN
GROUPCHAT_ID = YOUR GRP CHAT ID
```


## Misc

- For production deployment, we are using a webhook to listen for incoming messages. Local testings will use polling. Do take note before commiting.
```python
# For production deployment
updater.start_webhook(listen="0.0.0.0",
                      port=int(PORT),
                      url_path=TOKEN)
updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(NAME, TOKEN))
```

- Updates to the bot must be done via pull request. ***Be careful of editing files in master branch!***

- To get your chatids, userids etc. For groupchat ids, you need to add the bot into the group and then send the /start command. No deployment required.

```python
  https://api.telegram.org/bot{YOURBOTTOKEN}/getUpdates/
```
