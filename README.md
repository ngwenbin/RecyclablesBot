# Recyclables

Singapore's 1st Karung Guni hailing bot

Our goal is to improve Singapore’s domestic recycling efforts by partnering with the local karung guni community. By bridging the gap between residents and the collectors via a digital platform, household recycling is made more convenient and at the same time, it reduces recycling waste contamination which makes recycling overall more effective.

## Table of contents

* Requirements

* Misc

## Requirements to install (Follow the order)

1. Clone repo and its submodules
```shell
  git clone --recursive https://github.com/ngwenbin/RecyclablesBot.git
```

2. Switch to dev branch
```shell
  git checkout dev-clean
```

3. Open terminal to create a python venv and install dependencies from req.txt.
Make sure you are running python 3.8.x

#### For Windows:
```shell
  python -m venv YOUR_ENV_NAME # Creates virtual env
  pip install -r req.txt # install packages from req.txt
  cd wheel_dependencies # navigates to binary wheel dir
  for %x in (*.whl) do python -m pip install %x # install binary wheels/ deps
```

#### For MacOS:

If the pip fails, please use conda with conda forge channel priority to install the packages.

-  With Pip:
```shell
    python -m venv YOUR_ENV_NAME # Creates virtual env
    pip install -r req.txt # install packages from req.txt
    pip install shapely fiona pyproj # Order is important
    pip install geopandas # Order is important
  ```

- With Conda

Install conda via miniconda or anaconda.

```shell
  conda create --name YOUR_ENV_NAME python=3.8 # Creates virtual env
  conda config --add channels conda-forge # sets dep channel
  conda config --set channel_priority strict
  pip install -r req.txt # install packages from req.txt
  conda install geopandas # Conda will install the necessary deps
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
- For unresolved dependencies, check the bottom left bar of vscode and ensure that you are in the correct environment. It should say Python 3.x.x XX-bit {'env'}. The python interpreter should be pointer at your env python at ENVNAME/Scripts/python.exe

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
