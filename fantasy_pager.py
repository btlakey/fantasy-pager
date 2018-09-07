# -*- coding: utf-8 -*-
"""
Created on Wed Nov  8 10:42:59 2017
@author: blakey
"""

## import packages

from bs4 import BeautifulSoup
from urllib.request import urlopen
from datetime import date, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import os
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from simplecrypt import decrypt


## define variables

# dates for search input
# correct for utc timezome in aws server
if os.getcwd() == '/home/ubuntu':
    today = (date.today()-timedelta(hours=6)).strftime('%Y%m%d')
    yesterday = (date.today()-timedelta(days=1, hours=6)).strftime('%Y%m%d')
else:
    today = date.today().strftime('%Y%m%d')
    yesterday = (date.today()-timedelta(days=1)).strftime('%Y%m%d')    

# urls for add/drops
transactions_url = 'http://games.espn.com/ffl/recentactivity?leagueId=973912'
transactions_url_day = 'http://games.espn.com/ffl/recentactivity?leagueId=973912&seasonId=2017&activityType=-1&startDate=%s&endDate=%s&teamId=-1&tranType=-2' % (yesterday, today)
transactions_url_days = 'http://games.espn.com/ffl/recentactivity?leagueId=973912&seasonId=2017&activityType=-1&startDate=%s&teamId=-1&tranType=-2' % (date.today()-timedelta(days=3, hours=6)).strftime('%Y%m%d')
search_url = 'http://games.espn.com/ffl/freeagency?leagueId=973912&teamId=1&seasonId=2017'


## define functions

def find_drops(url=transactions_url_day, target='dropped'):

    # get add/drops page
    html = urlopen(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    # alternative using requests instead of urllib
    #page = requests.get(url)
    #soup = BeautifulSoup(page.text, 'html.parser')
    
    # relevant class header for list of add/drops
    transact_class = soup.find(class_='games-fullcol games-fullcol-extramargin')
    transact_tbl = transact_class.table
    text = transact_tbl.text.strip()
    
    # find the players that follow the target word ("dropped")
    tokens =  text.split()
    #tokens = [x.lower() for x in tokens]
    indices = [count for count, elem in enumerate(tokens) if elem == target]
    
    drop_list = []
    for i in indices:
        drop = ' '.join(tokens[i+1:i+3])
        drop = drop.replace(',', '')
        drop_list.append(drop)
        
    html.close()
    
    # account for injury asterisks
    for i in range(0, len(drop_list)):
        if drop_list[i][-1] == '*':
            drop_list[i] = drop_list[i][:-1]
        
    return drop_list


def make_driver(status, web_driver=False):
    
    if status == 'open':
        # webdriver settings
        chrome_driver_path = os.path.expanduser('~/chromedriver')
        chrome_options = Options()  
        chrome_options.add_argument("--headless")
        web_driver = webdriver.Chrome(executable_path=chrome_driver_path, chrome_options=chrome_options)
        
        return web_driver
        
    if status == 'close':
        web_driver.close()


def search_for_player(player, driver, url=search_url):
    
    driver.get(url)
    
    # find search input field
    sbox = driver.find_element_by_class_name("playerSearchNameInput")
    # input player name
    sbox.send_keys(player)
    # hit enter and send
    sbox.send_keys(u'\ue007')
    page_source = driver.page_source
    
    # get back page html, parse for elements
    soup = BeautifulSoup(page_source, 'html.parser')
    
    return soup
    

def get_player_values(player, soup, prjctn_thresh, own_thresh):

    send_email = False

    # get the info about a player
    player_tbl = soup.find(class_='pncPlayerRow playerTableBgRow0')

    # get the position
    player_info = player_tbl.find(class_='playertablePlayerName')
    position = str(player_info).split('teamid', 2)
    position = position[1].split('\xa0', 2)[1]
    if position[:1] == 'D':
        position = 'D/ST'
    elif position[:1] == 'K':
        position = 'K'
    else: position = position[:2]
    
    # when the player clears waivers
    waivers = player_tbl.find(style='text-align: center;')
    
    try:
        if str(waivers).split('"', 6)[6][1:6] == 'title':
            owner = str(waivers).split('"', 6)[6].split('"', 2)[1]
            clear_wvrs = 'Owned by ' + owner
    except:
        if str(waivers).split('"', 4)[2][1:3] == 'FA':
            clear_wvrs = 'Free Agent'
        else:
            clear_wvrs = str(waivers).split('"', 4)[3][:-5]
            clear_wvrs = clear_wvrs + str(waivers).split('WA', 2)[1][:6]
  
    # find the projected points
    prjctn_rows = player_tbl.find_all(class_='playertableStat appliedPoints')
    prjctn = prjctn_rows[2].text
    if prjctn != '--':
        prjctn = float(prjctn)
        if (prjctn >= prjctn_thresh and position != 'QB') \
        or (prjctn >= prjctn_thresh*2):
            send_email = True
    
    # find the percent ownership
    own_rows = player_tbl.find_all(class_='playertableData')    
    pct_owned = float(own_rows[3].text)
    if pct_owned >= own_thresh:
        send_email = True
    
    if clear_wvrs[:8] == 'Owned by':
        send_email = False    
    
    return {'player':player
           ,'position':position
           ,'projection':prjctn
           ,'percent_owned':pct_owned
           ,'clears_waivers':clear_wvrs
           ,'send_email':send_email}



def read_encrypted(passphrase, filename, string=True):
    
    with open(filename, 'rb') as input:
        ciphertext = input.read()
        plaintext = decrypt(passphrase, ciphertext)
        if string:
            return plaintext.decode('utf8')
        else:
            return plaintext


def login_espn(driver, url=search_url):
    
    driver.get(url)    
    driver.find_element_by_class_name('user').click()    
    driver.switch_to_frame(4)

    username = driver.find_element(By.XPATH, '//*[@id="did-ui"]/div/div/section/section/form/section/div[1]/div/label/span[2]/input')
    username.send_keys('commanderkeeen')
    password = driver.find_element(By.XPATH, '//*[@id="did-ui"]/div/div/section/section/form/section/div[2]/div/label/span[2]/input')
    password.send_keys(read_encrypted('fantasea', os.path.expanduser('~/fantasea.txt')))
    password.send_keys(Keys.ENTER)    


def add_to_watchlist(player, driver):
    
    # get player info
    soup = search_for_player(player, driver)
    
    # find player id
    player_tbl = soup.find(class_='playertablePlayerName')
    match = re.search(r'(id="playername_)([0-9]{1,})(")', str(player_tbl))
    player_id = str(match.group(2))
    
    # define url to add to watchlist
    watchlist_url = 'http://games.espn.com/ffl/watchlist?leagueId=973912&teamId=1&addPlayerId=%s' % str(player_id)
    driver.get(watchlist_url)

    
def make_player_html(d):
    
    html = '''\
    <html>
      <body>
        <p>
           <b>Player</b>: %(player)s <br>
           <b>Position</b>: %(position)s <br>
           <b>Percent Owned</b>: %(percent_owned)s <br>
           <b>Projection</b>: %(projection)s <br>
           <b>Clears Waivers</b>: %(clears_waivers)s <br>
        </p>
      </body>
    </html>
    ''' % {'player': d['player']
          ,'position': d['position']
          ,'percent_owned': d['percent_owned']
          ,'projection': d['projection']
          ,'clears_waivers':  d['clears_waivers']
          }
    
    return html


def make_message(players_email, players_email_last, to='brianlakey@gmail.com'):
    
    # find which players to include
    player_names = [player['player'] for player in players_email]
    player_names_last = [player['player'] for player in players_email_last]
    
    players_keep = set(player_names) - set(player_names_last)
    players_bottom = set(player_names_last).intersection(set(player_names))
    
    player_email_top = [player for player in players_email if player['player'] in players_keep]
    player_email_bottom = [player for player in players_email if player['player'] in players_bottom]
    
    
    top_header = '''\
        <html>
          <body>
            <p>
               <b><u>NEW PLAYERS</u></b>:
            </p>
          </body>
        </html>
    '''
    
    bottom_header = '''\
        <html>
          <body>
            <p>
               <b><u>PLAYERS STILL WORTH CONSIDERATION</u></b>:
            </p>
          </body>
        </html>
    '''
    
    msg = MIMEMultipart()
    msg['Subject'] = 'FANTASY_PAGER: ESPN Potential Add/Drop Alert, %s' % date.today().strftime('%b-%d-%Y')
    msg['From'] = 'Fantasy.Pager'
    msg['To'] = to
    
    msg.attach(MIMEText(top_header, 'html'))
    for player in player_email_top:
        msg.attach(MIMEText(make_player_html(player), 'html'))
    
    if len(player_email_bottom) > 0:
        msg.attach(MIMEText(bottom_header, 'html'))
        for player in player_email_bottom:
            msg.attach(MIMEText(make_player_html(player), 'html'))
        
    return msg, player_email_top + player_email_bottom, player_email_top
    
    
def send_email(msg):
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login('fantasy.pager', '20000Leagues')

    server.sendmail(msg['From'], msg['To'], msg.as_string())



def main(prjctn_thresh, own_thresh, url=transactions_url_day, watchlist=True, to='brianlakey@gmail.com'):
  
    # get players that have been dropped
    drop_list = find_drops(url)
    
    # open headless driver
    web_driver = make_driver('open', web_driver=False)
    
    # get all info for each player
    players = []
    for player in drop_list:
        try:
            soup = search_for_player(player, web_driver)
            players.append(get_player_values(player, soup, prjctn_thresh=prjctn_thresh, own_thresh=own_thresh))
        except:
            pass
        
    # identify which to send emails about
    players_email = [x for x in players if x['send_email']]  
    
    # find players in last email
    try:
        with open(os.path.expanduser('~/fantasy_players.txt'), 'r') as file_in:
            players_email_last  = eval(file_in.read())
    except: players_email_last = []
    
    # make html message
    msg, players_final, players_top = make_message(players_email, players_email_last, to=to)
    
    # add new (top) players to watchlist
    if watchlist:        
        # not sure if already logged in, in which case the tags are all different
        try:
            login_espn(web_driver)
        except:
            pass
        [add_to_watchlist(player['player'], web_driver) for player in players_top if player['send_email']] 
    
    # close driver
    make_driver('close', web_driver=web_driver)
    
    # send html message
    if sum([player['send_email'] for player in players_top]) > 0:
        send_email(msg)
    
    # persist email contents
    with open(os.path.expanduser('~/fantasy_players.txt'), 'w') as file_out:
        file_out.write(str(players_final))
    
    
## execute everything
        
if __name__ == '__main__':
    
    prjctn_thresh = 10.
    own_thresh = 33.3
    
    main(prjctn_thresh, own_thresh, watchlist=True, to='brianlakey@gmail.com')
