import requests
# import dataset
import json
from datetime import datetime
import sys
import getopt
import subprocess
import pandas as pd
import time
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy import text
import logging
import csv
from email.mime.text import MIMEText
import smtplib
import random
import os



file_path = os.path.dirname(os.path.realpath(__file__))



# The below two lines prevent logging each API call
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)



# '''
# https://developer.stubhub.com/store/site/pages/doc-viewer.jag?category=Search&api=EventSearchAPIv3
# '''

db = create_engine('sqlite:///{}/Stubhub4.db'.format(file_path))
db_min = create_engine('sqlite:///{}/Stubhub_min.db'.format(file_path))

app_token = 'IYPTC8szBdpiTRBT1f1QmuUHCMga' #--- Cubs
# consumer_key = 'blahblah'
# consumer_secret = 'blahblah'

api_url = 'https://api.stubhub.com'

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + app_token,
    'Accept': 'application/json',
    'Accept-Encoding': 'application/json'
}


def get_events(q='',city=''):
    # Stubhub.get_events_to_track(kwargs={'venue':'"United Center"', 'groupingName':'NHL', 'city':'Chicago'})
    url = api_url + '/search/catalog/events/v3'
    query = {'q':q, 'city':city, 'rows':500, 'parking':'False'}
    r = requests.get(url, params=query, headers=headers).json()
    return r

def record_events(events):
    eventId = []
    status = []
    locale = []
    name = []
    description = []
    URL = []
    eventDateLocal = []
    venue = []
    
    for l in events['events']:
        eventId.append(l["id"])
        status.append(l['status'])
        locale.append(l['locale'])
        name.append(l['name'])
        description.append(l['description'])
        URL.append('www.stubhub.com/'+l['webURI'])
        eventDateLocal.append(l['eventDateLocal'])
        venue.append(l['venue']['name'])
    
    df_events = pd.DataFrame({
        "eventId": eventId
        , "status": status
        , "locale": locale
        , "name": name
        , "description": description
        , "URL": URL
        , "eventDateLocal": eventDateLocal
        , "venue": venue
        })    
        # events_tbl.upsert(event, ['eventId'])
    # df_events.to_sql('events', db, if_exists = 'append', index=False)
    df_events.to_sql('events', db, if_exists = 'append', index=False)
    print("done appending events")
    
    delete_dupes = '''
    delete   from events
    where    rowid not in
           (
             select  min(rowid)
             from    events
             group by
                     eventId
           );
    '''
    with db.connect() as con:
        rs = con.execute(delete_dupes)
    with db_min.connect() as con:
        rs = con.execute(delete_dupes)

    print('removed duplicate events')
        
def get_listings_for_event(event_id):
    url = api_url + '/search/inventory/v1'
    query = {'eventId': event_id, 'rows': 1000, 'sort': 'currentprice'}
    r = requests.get(url, params=query, headers=headers)
    print('response = {}'.format(r.status_code))
    return r.json() 

def email_individual_games(curr_price, event_df_live, event_df_most_recent,now_time):
        # The below code never changes, though obviously those variables need values.
        session = smtplib.SMTP('smtp.gmail.com:587')
        session.ehlo()
        session.starttls()
        GMAIL_USERNAME = 'reptarbot@gmail.com'
        GMAIL_PASSWORD = 'reptarbotreptarbot'
        session.login(GMAIL_USERNAME, GMAIL_PASSWORD)
        recipient = 'kevin.james.crawford@gmail.com'
        # recipient = GMAIL_USERNAME

        headers = "\r\n".join(["from: " + GMAIL_USERNAME,
            "subject: Stubhub Individual Game Price Changes",
            "to: " + recipient,
            "mime-version: 1.0",
            "content-type: text/html"])

        body = '''
            \rHello,<br><br>The following game has a price change worth looking into:<br>
            '''

        body += "<br>At {}, the price of the game on {} is   **{}**, when it was **{}** ({} difference). Yesterday, it was {}. the game URL is <br>{}<br> This listing ID is {}".format(
            str(now_time)
            , str(event_df_most_recent.eventDateLocal.values[0])[:10]
            , curr_price
            , event_df_most_recent.low_price.values[0]
            , str(round(100.0*(curr_price-event_df_most_recent.low_price.values[0])/event_df_most_recent.low_price.values[0],2))+'%'
            , event_df_most_recent.yesterdays_best_price.values[0]
            , event_df_most_recent.game_URL.values[0]
            , event_df_live.listingId.values[0]
        )
        # print(body)
        logging.info('%s -- At %s, email finalize body' % (run_id, str(datetime.today())))

        # body_of_email can be plaintext or html!                    
        content = headers + "\r\n\r\n" + body
        logging.info('%s -- At %s, email finalize content' % (run_id, str(datetime.today())))
        session.sendmail(GMAIL_USERNAME, recipient, content)
        logging.info('%s -- At %s, email sent' % (run_id, str(datetime.today())))

def record_listings_for_event(event_id, all_events_df,now_time):
    time.sleep(7)
    
    

    event_listings = get_listings_for_event(event_id)

    eventId = []
    datetimeX = []
    runId = []  
    seatNumbers = []
    currentPrice = []
    listingId = []
    sectionId = []
    sectionName = []
    zoneId = []
    zoneName = []
    row = []
    quantity = []
    try:
        for l in event_listings['listing']:
                eventId.append(event_id)
                #runId.append(run_id)
                datetimeX.append(now_time)
                currentPrice.append(l['currentPrice']['amount'])
                listingId.append(l["listingId"])
                sectionId.append(l["sectionId"])
                sectionName.append(l["sectionName"])
                zoneId.append(l["zoneId"])
                zoneName.append(l["zoneName"])
                row.append(l["row"])
                seatNumbers.append(l["seatNumbers"])
                quantity.append(l["quantity"])
               
        df = pd.DataFrame({
            "eventId": eventId
            #, "runId": run_id
            , "datetime": datetimeX
            , "seatNumbers": seatNumbers
            , "currentPrice": currentPrice
            , "listingId": listingId
            , "sectionId": sectionId
            , "sectionName": sectionName
            , "zoneId": zoneId
            , "zoneName": zoneName
            , "row": row
            , "seatNumbers": seatNumbers
            , "quantity": quantity
            })

        bad_listings = [1190356184
                        , 1182095596
                        , 1189448408
                        , 1185291783
                        , 1188996138
                        , 1189714426
                        , 1173301639
                        , 1191082113
                        , 1186321666
                        , 1188996152
                        , 1194077594
                        , 1191332752
                        , 1183397283
                        , 1191244655
                        , 1192807045
                        , 1194078039
                        , 1193030368
                        , 1186948736
                        , 1190420808
                        , 1205117106
                        , 1191244655
                        , 1194078039
                        , 1186321666
                        , 1193739716
                        , 1192834490
                        , 1191250685
                        , 1202410775
                        , 1204728138
                        , 1206121146
                        , 1185179420]

        try:
            event_df = all_events_df[all_events_df.eventId == event_id]
            most_recent_min_event_df = event_df[event_df.datetime == max(event_df.datetime)]

            current_price_for_comp = min(df[df.sectionId == 117035].currentPrice)
            #print(current_price_for_comp)
            #print(most_recent_min_event_df.low_price.values[0])
            
            if 1.0 * (current_price_for_comp - most_recent_min_event_df.low_price.values[0]) / most_recent_min_event_df.low_price.values[0] < -.15 \
                and current_price_for_comp != most_recent_min_event_df.yesterdays_best_price.values[0] \
                and df.listingId.values[0] not in bad_listings:
                    logging.info('~~~~ should send email for {}.'.format(df.listingId.values[0]))
                    
                    email_individual_games(current_price_for_comp, df, most_recent_min_event_df, now_time)
                    logging.info('%s -- At %s, individual game email sent for event %s!' % (run_id, str(datetime.today()),str(event_id)))
            else:
                print('no email to send')
                pass
        except:
            print('email error')
            logging.info('%s -- At %s, individual game email ERROR for event %s!' % (str(run_id), str(datetime.today()), str(event_id)))
            pass

        df['Rank'] = df.groupby('sectionId')['currentPrice'].rank(ascending = True)

        df2 = df.drop(df[df.Rank > 10].index) #removes high ranking rows
        DF = df2.drop('Rank', 1) # removews rank column 
        DF.to_sql('listings', db, if_exists = 'append', index=False)

        df2_min2 = df.drop(df[df.Rank > 2].index)
        DF_min2 = df2_min2.drop('Rank', 1)
        DF_min3 = DF_min2.loc[DF_min2['sectionId'] == 117035]

        DF_min3.to_sql('listings', db_min, if_exists = 'append', index=False)
    except TypeError:
        print('errored out... no tickets for event?')


    # df.to_sql('listings', db, if_exists = 'append', index=False)
    
    # print(event_ids)
    print('done appending listings for event_id={}'.format(str(event_id)))
    

def build_comparison_database():
    db_min = sqlite3.connect('{}/Stubhub_min.db'.format(file_path))
    c = db_min.cursor()


    qry0 = '''
        create temporary table relevant_games as
        select l.*
        from listings l
        left join events e using (eventId)
        where 
            datetime > date('now','localtime','-240 hours')
            and substr(eventDatelocal, 6,2)*1 >= 1* strftime('%m', 'now')
        ;
    '''

    qry1 = '''
        create temporary table low_price_table as
        select eventId, datetime, min(currentPrice) "low_price"
        from relevant_games
        group by 1,2
        ;
    '''

    qry2 = '''
        create temp table with_last_time as
        select lpt.eventId "eventId", lpt.datetime "datetime", lpt.low_price "low_price", max(lpt2.datetime) "last_datetime"
        from 
            low_price_table lpt 
            left join low_price_table lpt2
                on lpt2.eventId = lpt.eventId
                and lpt2.datetime < lpt.datetime
        group by 1,2,3
        ;
    '''

    qry3 = '''
        create temporary table all_changes as 
        select
        wlt.eventId "eventId", e.eventDateLocal "eventDateLocal", e.URL || '?sid=117035' "game_URL"
        , wlt.datetime "datetime", wlt.low_price "low_price", lpt.low_price "last_price"
        , 'https://www.stubhub.com/buy/review?ticket_id=' || max(l.listingId) || '&quantity_selected=' || l.quantity || '&event_id=' || wlt.eventId "listing_URL"
        , face.faceValue "faceValue"
        , max(l.listingId) "listingId", l.quantity "quantity"
        , min(lpt.low_price) "last_price"
        , wlt.low_price - min(lpt.low_price) "price_change"
        , (wlt.low_price - min(lpt.low_price))/min(lpt.low_price) <= -.05 "price_flag"
        , min(yest.currentPrice) "yesterdays_best_price"
        , wlt.low_price - min(yest.currentPrice) "yest_price_change"
        , abs(wlt.low_price - min(yest.currentPrice)) >= 5 "yest_price_flag"


        from
        with_last_time wlt
        left join low_price_table lpt
            on lpt.eventId = wlt.eventId
            and lpt.datetime = wlt.last_datetime
        left join events e using (eventId)

        left join relevant_games l
            on l.eventId = wlt.eventId
            and l.datetime = wlt.datetime
            and l.currentPrice = wlt.low_price

        left join relevant_games yest
            on yest.eventId = wlt.eventId
            and date(yest.datetime) = date(wlt.datetime, '-001 days')

        left join facevalues face on e.eventDateLocal = face.eventDateLocal

        group by 1,2,3,4,5,6,8
        order by 1,4 desc
        ;
    '''

    qry4 = '''
        select 
            ac.*
        from
            all_changes ac
        where 
            ac.eventDateLocal > date('now','localtime')
            and ac.datetime > date('now','localtime','-120 hours')
        order by 2
    '''

    logging.info('%s -- At %s, comparison queries were generated!' % (run_id, str(datetime.today())))

    c.execute(str(qry0))
    c.execute(str(qry1))
    c.execute(str(qry2))
    c.execute(str(qry3))
    c.execute(str(qry4))
    logging.info('%s -- At %s, comparison queries 0-4 ran!' % (run_id, str(datetime.today())))

    cols = [column[0] for column in c.description]
    df = pd.DataFrame.from_records(data = c.fetchall(), columns = cols)

    c.close()
    db_min.close()

    return df 

def email_price_changes():
    
    db_min = sqlite3.connect('{}/Stubhub_min.db'.format(file_path))
    c = db_min.cursor()

    qry0 = '''
        create temporary table relevant_games as
        select l.*
        from listings l
        left join events e using (eventId)
        where 
            datetime > date('now','localtime','-012 hours')
            and substr(eventDatelocal, 6,2)*1 >= 1* strftime('%m', 'now')
        ;
    '''

    qry1 = '''
        create temporary table low_price_table as
        select eventId, datetime, min(currentPrice) "low_price"
        from relevant_games
        group by 1,2
    ;
    '''

    qry2 = '''
        create temp table with_last_time as
        select lpt.eventId "eventId", lpt.datetime "datetime", lpt.low_price "low_price", max(lpt2.datetime) "last_datetime"
        from 
            low_price_table lpt 
            left join low_price_table lpt2
                on lpt2.eventId = lpt.eventId
                and lpt2.datetime < lpt.datetime
        group by 1,2,3
    ;
    '''

    qry3 = '''
    create temporary table all_changes as 
    select
        wlt.eventId "eventId", e.eventDateLocal "eventDateLocal", e.URL || '?sid=117035' "game_URL"
        , wlt.datetime "datetime", wlt.low_price "low_price", lpt.low_price "last_price"
        , 'https://www.stubhub.com/buy/review?ticket_id=' || max(l.listingId) || '&quantity_selected=' || l.quantity || '&event_id=' || wlt.eventId "listing_URL"
        , face.faceValue "faceValue"
        , max(l.listingId) "listingId", l.quantity "quantity"
        , min(lpt.low_price) "last_price"
        , wlt.low_price - min(lpt.low_price) "price_change"
        , abs(wlt.low_price - min(lpt.low_price)) >= 5 "price_flag"
        , min(yest.currentPrice) "yesterdays_best_price"
        , wlt.low_price - min(yest.currentPrice) "yest_price_change"
        , abs(wlt.low_price - min(yest.currentPrice)) >= 5 "yest_price_flag"
    from
        with_last_time wlt
        left join low_price_table lpt
            on lpt.eventId = wlt.eventId
            and lpt.datetime = wlt.last_datetime
        left join events e using (eventId)

        left join relevant_games l
            on l.eventId = wlt.eventId
            and l.datetime = wlt.datetime
            and l.currentPrice = wlt.low_price

        left join relevant_games yest
            on yest.eventId = wlt.eventId
            and date(yest.datetime) = date(wlt.datetime, '-001 days')

        left join facevalues face on e.eventDateLocal = face.eventDateLocal

    group by 1,2,3,4,5,6,8
    order by 1,4 desc
    ;
    '''

    qry4 = '''
        select 
            ac.*
        from
            all_changes ac
            inner join (
                select eventId, max(datetime) "datetime"
                from all_changes
                group by 1
            ) ac2 using (eventId, datetime)
        where 
            1.0 * (ac.low_price - ac.last_price) / ac.last_price <= -.20
            and ac.eventDateLocal > date('now','localtime')
            -- and ac.datetime = date('now','localtime')
             and ac.datetime > date('now','localtime','-002 hours')
            and ac.listingId not in (1190356184
                                    , 1182095596
                                    , 1189448408
                                    , 1185291783
                                    , 1188996138
                                    , 1189714426
                                    , 1173301639
                                    , 1191082113
                                    , 1186321666
                                    , 1188996152
                                    , 1194077594
                                    , 1191332752
                                    , 1183397283
                                    , 1191244655
                                    , 1192807045
                                    , 1194078039
                                    , 1193030368
                                    , 1186948736
                                    , 1190420808
                                    , 1187297513
                                    , 1191244655
                                    , 1194078039
                                    , 1186321666
                                    , 1193739716
                                    , 1192834490
                                    , 1191250685
                                    , 1202410775
                                    , 1204728138
                                    , 1206121146
                                    , 1205117106
                                    , 1185179420
                )
        order by 2

    '''
    logging.info('%s -- At %s, query was generated!' % (run_id, str(datetime.today())))

    c.execute(str(qry0))
    c.execute(str(qry1))
    c.execute(str(qry2))
    c.execute(str(qry3))
    c.execute(str(qry4))
    logging.info('%s -- At %s, price_change_email queries 0-4 ran!' % (run_id, str(datetime.today())))

    if c.fetchall() != []:
        logging.info('%s -- At %s, price_cahnge_email query has results and should be sent!' % (run_id, str(datetime.today())))
        
        c.execute(str(qry4))
        result = c.fetchall()
        logging.info('%s -- At %s, price_change_email query reran to repull info!' % (run_id, str(datetime.today())))

        # The below code never changes, though obviously those variables need values.
        session = smtplib.SMTP('smtp.gmail.com:587')
        session.ehlo()
        session.starttls()
        GMAIL_USERNAME = 'reptarbot@gmail.com'
        GMAIL_PASSWORD = 'reptarbotreptarbot'
        session.login(GMAIL_USERNAME, GMAIL_PASSWORD)
        recipient = 'kevin.james.crawford@gmail.com'
        # recipient = GMAIL_USERNAME
        logging.info('%s -- At %s, email set info' % (run_id, str(datetime.today())))


        headers = "\r\n".join(["from: " + GMAIL_USERNAME,
            "subject: Stubhub Price Changes",
            "to: " + recipient,
            "mime-version: 1.0",
            "content-type: text/html"])
        logging.info('%s -- At %s, email set headers' % (run_id, str(datetime.today())))

        body = '''
            \rHello,<br><br>The following game prices have changed:<br>
            '''
        logging.info('%s -- At %s, email begin body' % (run_id, str(datetime.today())))

        for row in result:
            nofrag, frag = row[3].split('.')
            pull_time = datetime.strftime(datetime.strptime(nofrag, '%Y-%m-%d %H:%M:%S'),'%I:%M %p')
            game_date = datetime.strftime(datetime.strptime(row[1], '%Y-%m-%dT%H:%M:%S-0500'), '%m-%d')
            body += "<br>At {}, the price of the game on {} was {}, when it was {} ({} difference). the game URL is <br>{}<br> and the listing URL is <br>{}<br>".format(
                pull_time, game_date, row[4],row[5],str(round(100.0*row[11]/row[5],2))+'%',row[2],row[6]
                )
            # print(body)
        logging.info('%s -- At %s, email finalize body' % (run_id, str(datetime.today())))

        # body_of_email can be plaintext or html!                    
        content = headers + "\r\n\r\n" + body
        logging.info('%s -- At %s, email finalize content' % (run_id, str(datetime.today())))
        session.sendmail(GMAIL_USERNAME, recipient, content)
        logging.info('%s -- At %s, email sent' % (run_id, str(datetime.today())))

        print('email sent!')
    else:
        logging.info('%s -- At %s, price_change_query returned no results, no email will be sent' % (run_id, str(datetime.today())))
        print('no changes, no email sent')

    c.close()
    db_min.close()

# def build_output_price_file():
    
#     db_min = sqlite3.connect('{}/Stubhub_min.db'.format(file_path))
#     c = db_min.cursor()
#     logging.info('%s -- At %s, reconnected for output file build' % (run_id, str(datetime.today())))
    
#     qry0 = '''
#     create temporary table small_listings as
#     select currentPrice, datetime, eventId, listingId, quantity
#     from listings
#     ;
#     '''

#     qry0b = '''
#     create index i on small_listings (eventId, datetime, currentPrice)
#     ;
#     '''

#     qry1 = '''
#         create temporary table low_price_table as
#         select eventId, datetime, min(currentPrice) "low_price"
#         from small_listings
#         group by 1,2
#     ;
#     '''

#     qry2 = '''
#         create temp table with_last_time as
#         select lpt.eventId "eventId", lpt.datetime "datetime", lpt.low_price "low_price", max(lpt2.datetime) "last_datetime"
#         from 
#             low_price_table lpt 
#             left join low_price_table lpt2
#                 on lpt2.eventId = lpt.eventId
#                 and lpt2.datetime < lpt.datetime
#         group by 1,2,3
#     ;
#     '''

#     qry3 = '''
#     create temporary table all_changes as 
#     select
#         wlt.eventId "eventId", e.eventDateLocal "eventDateLocal", e.URL || '?sid=117035' "game_URL"
#         , wlt.datetime "datetime", wlt.low_price "low_price", lpt.low_price "last_price"
#         , 'https://www.stubhub.com/buy/review?ticket_id=' || max(l.listingId) || '&quantity_selected=' || l.quantity || '&event_id=' || wlt.eventId "listing_URL"
#         , face.faceValue "faceValue"
#         , max(l.listingId) "listingId", l.quantity "quantity"
#         , min(lpt.low_price) "last_price"
#         , wlt.low_price - min(lpt.low_price) "price_change"
#         , abs(wlt.low_price - min(lpt.low_price)) >= 5 "price_flag"
#         , min(yest.currentPrice) "yesterdays_best_price"
#         , wlt.low_price - min(yest.currentPrice) "yest_price_change"
#         , abs(wlt.low_price - min(yest.currentPrice)) >= 5 "yest_price_flag"
#     from
#         with_last_time wlt
#         left join low_price_table lpt
#             on lpt.eventId = wlt.eventId
#             and lpt.datetime = wlt.last_datetime
#         left join events e using (eventId)

#         left join listings l
#             on l.eventId = wlt.eventId
#             and l.datetime = wlt.datetime
#             and l.currentPrice = wlt.low_price

#         left join listings yest
#             on yest.eventId = wlt.eventId
#             and date(yest.datetime) = date(wlt.datetime, '-001 days')

#         left join facevalues face on e.eventDateLocal = face.eventDateLocal

#     group by 1,2,3,4,5,6,8
#     order by 1,4 desc
#     ;
#     '''

#     qry4 = '''
#         select 
#             ac.*
#         from
#             all_changes ac
#         ;
#     '''
#     logging.info('%s -- At %s, output file build queries generated' % (run_id, str(datetime.today())))

#     c.execute(str(qry1))
#     c.execute(str(qry2))
#     c.execute(str(qry3))
#     c.execute(str(qry4))
#     logging.info('%s -- At %s, output file build queries ran' % (run_id, str(datetime.today())))

#     titles = ['eventId'
#               ,'eventDateLocal'
#               ,'game_URL'
#               ,'datetime'
#               ,'low_price'
#               ,'last_price'
#               ,'listing_URL'
#               ,'faceValue'
#               ,'listingId'
#               ,'quantity'
#               ,'last_price:1'
#               ,'price_change'
#               ,'price_flag'
#               ,'yesterdays_best_price'
#               ,'yest_price_change'
#               ,'yest_price_flag']


#     c.fetchone()
#     with open('{}/stubhub min pricing({}).csv'.format(file_path, datetime.today().strftime('%Y%m%d')),'w', newline='') as file:
#         file.write(','.join(titles))
#         file.write('\n')
#         for i in c:
#             a=c.fetchone()
#             csv.writer(file).writerow(a)
#     logging.info('%s -- At %s, output file built and saved' % (run_id, str(datetime.today())))

#     c.close()
#     db_min.close()

if __name__ == "__main__":
    logging.basicConfig(filename="{}/stubhub_log.log".format(file_path), level=logging.INFO) 
    
    id_1 = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in range(4))
    id_2 = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in range(8))
    id_3 = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in range(4))
    
    run_id = '{}-{}-{}'.format(str(id_1),str(id_2),str(id_3))
    
    try:

        comp_df = build_comparison_database()


        event_ids = get_events('Cubs', 'Chicago')
        record_events(event_ids)

        
        now = datetime.today()

        for n, eid in enumerate(event_ids['events']):
            print('{}/{}  --- {}'.format(str(n+1).zfill(2), str(len(event_ids['events'])).zfill(2), eid['id']))
            if eid['venue']['name'] == 'Wrigley Field':
                record_listings_for_event(eid['id'], comp_df, now)

        logging.info('%s -- At %s, %s events were added' % (run_id, str(datetime.today()), str(len(event_ids['events']))))
        

        try:
            email_price_changes()
        except:
            logging.info('%s -- At %s, errored out... no emails were sent' % (run_id, str(datetime.today())))

        # if datetime.today().minute < 10:
        #     build_output_price_file()
        # else:
        #     logging.info('{} -- didnt run output file build'.format(run_id))            
    

    except getopt.GetoptError:
        # print help information and exit:
        logging.info('{} -- ERRORED OUT AT {}'.format(run_id, str(err))) # will print something like "option -a not recognized"
        sys.exit(2)
