import requests
import json
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup


def get_credentials(path, flavor='api'):
    """
    Get app key from api credential file or usernames and password
    :param path: string, i.e. location to a credential file
    :param flavor: either 'api' or 'regular'. api expect just appname and key. regular, appname, user and password
    :return: a dictionay with appname as key and either api as value or (user, password) as value depending on flavor
    """
    creds = dict()
    with open(path, 'r') as f:
        for line in f.readlines():
            try:
                if flavor == 'api':
                    app, key = line.split(':')
                    creds[app] = key
                else:
                    db, value = line.split(':')
                    creds[db] = tuple(value.split(','))
            except:
                pass

    return creds

# print(get_credentials('../credentials/apkeys.txt'))
mykey = get_credentials('../credentials/apkeys.txt').get('WeekendTravels')


def geocode(key, address='Peoria, IL'):
    """
    Geocode a location in the US
    :param key: a valid app key
    :param address: a string representing a location in the US. default: Peoria, IL
    :return: a json object as returned by the google api: https://maps.googleapis.com/maps/api/geocode
    """
    url = 'https://maps.googleapis.com/maps/api/geocode/json?'
    # full_url = '%s&address=%s&key=%s' % (url, address, key)
    # result = requests.get(full_url).json()
    result = requests.get(url, {'address':address, 'key':key}).json()

    return result


def getPlaceId(result):
    """
    Get the place id as needed by the google api
    :param result: a result from the geocode function
    :return: a string value if properly geocded using Google API or None if failure
    """
    if result.get('status','') == 'OK':
        return result.get('results')[0].get('place_id')
    else:
        return None

# print(getPlaceId(geocode(mykey)))


def distanceMatrix(key, origin, destination, units='imperial', avoid=('tolls', 'ferries')):
    """
    Get the driving distance and duration from a single origin and one or more destinations.
    :param key: a valid google app key
    :param origin: a single string representing a location in the US
    :param destination: a string or list of strings or tuple of strings denoting locations in the US
    :param units: either imperial or metrics. default imperial
    :param avoid: either a string or list of restrictions i.e. tools, ferries, highways
    :return: json result from google distance matrix api https://maps.googleapis.com/maps/api/distancematrix
    """
    if not isinstance(origin, str):
        return {'status':'NOMNOM'}

    origin_placeid = getPlaceId(geocode(key, origin))

    if origin_placeid is None:
        return {'status':'NOMNOM'}

    if isinstance(destination, str):
        destin_placeid = getPlaceId(geocode(key, destination))
        if destin_placeid is None:
            return {'status':'NOMNOM'}

    elif isinstance(destination, list) or isinstance(destination, tuple):
        destin_placeid = map(lambda x: getPlaceId(geocode(key, x)), destination)
        destin_placeid = [str(el) for el in destin_placeid if el is not None] # None would not make sense

        if len(destin_placeid) == 0:
            return {'status': 'NOMNOM'}

        destin_placeid = '|place_id:'.join(destin_placeid)

    if avoid is None:
        avoid = ''
    elif isinstance(avoid, str):
        pass
    elif isinstance(avoid, list) or isinstance(avoid, tuple):
        avoid = '|'.join(avoid)
    else:
        avoid = ''

    url = 'https://maps.googleapis.com/maps/api/distancematrix/json?'

    result = requests.get(url, {'units':units,
                                'origins': 'place_id:%s' % origin_placeid,
                                'destinations': 'place_id:%s' % destin_placeid,
                                'avoid':avoid,
                                'key':key}).json()
    return result

# print(distanceMatrix(mykey, 'Peoria, IL', 'Chicago, IL'))
# print(distanceMatrix(mykey, 'Peoria, IL', 'Chicago, IL', avoid=None))
# print(distanceMatrix(mykey, 'Peoria, IL', 'Chicago, IL', avoid='highways'))
# print(distanceMatrix(mykey, 'Peoria, IL', 'Chicago, IL', avoid=3))
# print(getPlaceId(geocode(mykey)))
# print(getPlaceId(geocode(mykey, 'Columbs, OH')))
# print(getPlaceId(geocode(mykey, 'Chicago, IL')))


def getDuration(result):
    """
    Get the driving duration
    :param result: a result from the distanceMatrix function
    :return: list of tuples like: (destination, duration in seconds)
    """
    if result.get('status','') == 'OK':
        if len(result.get('destination_addresses',[])) == 1:
            return list(zip(result.get('destination_addresses'),
                            [result.get('rows')[0].get('elements')[0].get('duration').get('value')]))
        else:
            dests = result.get('destination_addresses')
            durations = [el.get('duration').get('value') for el in result.get('rows')[0].get('elements')]

            return list(zip(dests, durations))
    else:
        return None

# print(getDuration(distanceMatrix(mykey, 'Peoria, IL', 'Chicago, IL', avoid='highways')))

def expedia(origin, destination, start_dt, rtrn=None):
    url = "https://www.expedia.com/Flights-Search?"
    rtrn = start_dt + relativedelta(days=2) if rtrn is None else rtrn
    origin = "from:%s,to:%s,departure:%sTANYT" % (origin, destination, start_dt.strftime("%m/%d/%Y"))
    destination = "from:%s,to:%s,departure:%sTANYT" % (destination, origin, rtrn.strftime("%m/%d/%Y"))
    headers = {'mode':'search',
               'trip':'roundtrip',
               'leg1':origin,
               'leg2':destination,
               'passengers': 'adults:1,children:0,seniors:0,infantinlap:N',
               'options': 'cabinclass:economy',
               'origref': 'www.expedia.com'
               }

    resp = requests.get(url, headers, verify=False)
    return resp

''' This header definitely worked
headers = {'mode':'search',
           'trip':'roundtrip',
           'leg1':'from:Peoria, IL, United States (PIA),to:Columbus, OH (CMH-John Glenn Columbus Intl.),departure:05/01/2018TANYT',
           'leg2':'from:Columbus, OH (CMH-John Glenn Columbus Intl.),to:Peoria, IL, United States (PIA),departure:05/01/2018TANYT&',
           'passengers':'adults:1,children:0,seniors:0,infantinlap:N',
           'options':'cabinclass:economy',
           'origref':'www.expedia.com'
            }
'''

def getPrice(resp):
    if resp.status_code != 200:
        return 'N/A'

    soup = BeautifulSoup(resp.text, "lxml")
    json_string = soup.find_all(id='cachedResultsJson')

    if len(json_string) == 0:
        return 'N/A'

    json_string = json_string[0].text.encode('utf-8')
    json_obj = json.loads(json_string)

    metadata = json_obj.get('metaData',{})
    return metadata.get('formattedCheapestRoundedUpPrice', 'N/A')

# print(getPrice(expedia('Peoria, IL', 'Columbus, OH', dt(2018,5,12))))