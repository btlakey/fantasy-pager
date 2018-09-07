# fantasy-pager
Service to email recipients about potential new free agents on the waiver wire (ESPN league)


## setup

### create ubuntu system

#### ssh using pem key you created
```
ssh -i ~/.ssh/fantasypager.pem ubuntu@ec2-34-201-127-136.compute-1.amazonaws.com
```

#### install miniconda
```
wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

#### set alias to python3
```
sudo nano ~/.bashrc
```
`alias python="/home/ubuntu/miniconda3/bin/python"`
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

#### schedule crontab (every 20 mins)
```
sudo nano /etc/crontab
```
`*/20 * * * * ubuntu /home/ubuntu/miniconda3/bin/python fantasy_pager.py`

#### install chrome driver (mac link)
```
wget https://chromedriver.storage.googleapis.com/2.33/chromedriver_mac64.zip
```
