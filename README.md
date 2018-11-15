# fantasy-pager
Service to email recipients about potential new free agents on the waiver wire (ESPN league)


## setup

#### create free AWS EC2 ubuntu system
https://aws.amazon.com/free/

#### ssh using pem key you created to EC2 address
```
ssh -i ~/.ssh/fantasypager.pem ubuntu@ec2-34-201-127-136.compute-1.amazonaws.com
```

#### install miniconda
```
wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

#### set alias to python3 (if not default)
```
sudo nano ~/.bashrc
  alias python="/home/ubuntu/miniconda3/bin/python"
```
```
source ~/.bashrc
```

#### install chrome
```
cd /tmp
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get -f install
```

#### install chrome driver (linux instructions)
```
sudo apt install unzip
wget https://chromedriver.storage.googleapis.com/2.33/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
```

#### need compiler to build some pip packages
```
sudo apt-get install build-essential libssl-dev libffi-dev python-dev
```

#### install pip dependencies
```
pip install bs4 selenium simple-crypt
```

#### copy files over / clone repo
```
scp -i ~/.ssh/fantasypager.pem ~/Documents/fantasy_pager.py ubuntu@ec2-34-201-127-136.compute-1.amazonaws.com:~
scp -i ~/.ssh/fantasypager.pem ~/fantasea.txt ubuntu@ec2-34-201-127-136.compute-1.amazonaws.com:~
```

#### schedule crontab (every 60 mins) to run script
```
sudo nano /etc/crontab
  */60 * * * * ubuntu /home/ubuntu/miniconda3/bin/python fantasy_pager.py
```

#### install chrome driver (mac link)
```
wget https://chromedriver.storage.googleapis.com/2.33/chromedriver_mac64.zip
```

#### instal mail client
```
sudo apt install aptitude
sudo aptitude install postfix
```
- select "Local Only" during setup, accept defaults

#### make sure you allowed access to google accounts
https://support.google.com/accounts/answer/6010255?authuser=2&p=lsa_blocked&hl=en&authuser=2&visit_id=636718867648495172-3778857106&rd=1

#### set up credentials.py locally with encrypted usr/pwd
##### this enables `read_encrypted()` in `fantasy_pager.py`
```python
import os
from simplecrypt import encrypt, decrypt

passphrase = 'fantasea'
filename = 'fantasea.txt'
password = 'your_password'

def write_encrypted(passphrase, filename, plaintext):
    with open(filename, 'wb') as output:
        ciphertext = encrypt(passphrase, plaintext)
        output.write(ciphertext)

data = write_encrypted(passphrase, filename, password) 
```

### sample urls

- transactions_url: http://games.espn.com/ffl/recentactivity?leagueId=973912
- transactions_url_day: http://games.espn.com/ffl/recentactivity?leagueId=973912&seasonId=2017&activityType=-1&startDate=20180906&endDate=20180907&teamId=-1&tranType=-2
- transactions_url_days: http://games.espn.com/ffl/recentactivity?leagueId=973912&seasonId=2017&activityType=-1&startDate=20180904&teamId=-1&tranType=-2
- search_url: http://games.espn.com/ffl/freeagency?leagueId=973912&teamId=1&seasonId=2017
