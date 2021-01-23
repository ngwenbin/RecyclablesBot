# Recyclables

Singapore's 1st Karung Guni hailing bot

Our goal is to improve Singapore’s domestic recycling efforts by partnering with the local karung guni community. By bridging the gap between residents and the collectors via a digital platform, household recycling is made more convenient and at the same time, it reduces recycling waste contamination which makes recycling overall more effective.

## Table of contents

* Requirements

* Misc

## Requirements to install (Follow the order)

1. Clone repo

2. [Install Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/). You can either choose between mini conda or anaconda. It makes the dependencies installation much easier.

3. Create a Conda env with the provided yml file. Below are a few useful commands.

```python
  # To change the name of the env, edit the first line of the yml file before creating it. Deafult is recyclables
  conda env create -f environment.yml # Create new env with python installed
  conda info --envs # See list of conda envs
  conda activate recyclables # activate the env, if you changed the env name, kindly update env name accordingly.
```
4. Inside kgid.py, do not touch the kg_prod dict as it is for production use only. Update your grpchat ids in the else block:
```python
      else: # testing ids, always use this for personal tests.
        d = {
            "1" : CHATID,
            "2" : CHATID,
            "3" : CHATID,
            "4" : CHATID,
        }
```
5. Create your own .env file and paste your own Telegram bot token + API token inside. Do not touch anything else.:
```python
TELEGRAM_TOKEN = BOT_TOKEN
GROUPCHAT_ID = kgid_test
API_TOKEN = API_TOKEN
HEROKU_NAMES = recyclablesbotlocal
```


## Misc
- For unresolved dependencies, check the bottom left bar of vscode and ensure that you are using the correct python interpreter. It should say Python 3.x.x XX-bit {'YOUR_ENV_NAME':conda}
- For production deployment, we are using a webhook to listen for incoming messages. Local testings will use polling. Do take note before commiting.
```python
# For production deployment
updater.start_webhook(listen="0.0.0.0",
                      port=int(PORT),
                      url_path=TOKEN)
updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(NAME, TOKEN))
```

- Always commit to dev-clean branch. ***Do not edit files in master branch without permission***

- To get your chatids, userids etc. For groupchat ids, you need to add the bot into the group, send a message in the group and use the following api request. No deployment required.

```python
  https://api.telegram.org/bot{YOURBOTTOKEN}/getUpdates/
```
