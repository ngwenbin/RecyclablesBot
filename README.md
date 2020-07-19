# Recyclables

Singapore's 1st Karung Guni hailing bot

Our goal is to improve Singapore’s domestic recycling efforts by partnering with the local karung guni community. By bridging the gap between residents and the collectors via a digital platform, household recycling is made more convenient and at the same time, it reduces recycling waste contamination which makes recycling overall more effective.

## Table of contents

* Requirements

* Misc

## Requirements

To install the necessary packages/ modules:

```sh
  pip install -r requirements.txt
```
Create your own .env file and paste your own Telegram bot token inside:
```sh
TELEGRAM_TOKEN = YOUR TOKEN
```

Remember to comment the following snippet during development. Likewise, uncomment it before making a commit.
```sh
# For production deployment
updater.start_webhook(listen="0.0.0.0",
                      port=int(PORT),
                      url_path=TOKEN)
updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(NAME, TOKEN))
```

## Misc

- Updates to the bot must be done via pull request.

  Be careful of editing files in master branch!
