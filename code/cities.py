import re
import pandas as pd
import numpy as np
from functions import (get_credentials, distanceMatrix, getDuration, getPrice, expedia, firstFriday)
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta

def cities():
    cities = "../data/cities.txt"

    with open(cities, 'r') as f:
        cities = f.readlines()

    return [city.strip() for city in cities]

# print(cities())

def capitals():
    capitals = "../data/capitals.txt"
    
    with open(capitals, 'r') as f:
        capitals = f.readlines()
        
    return [capital.strip() for capital in capitals]

# print(capitals())


def all_durations(cities):
    mykey = get_credentials('../credentials/apkeys.txt').get('WeekendTravels')
    results = distanceMatrix(mykey, origin='Peoria, IL', destination=cities)
    durations = getDuration(results)

    # had to remove hawaii from the list since you cannot drive to hawaii
    return durations


def cities_within_six_hours(durations, threshold=6*60*60):
    return [re.sub(', USA', '', el[0]) for el in durations if el[1] <= threshold]

# print(cities_within_six_hours(all_durations(cities())))

# prices = [getPrice(expedia("Peoria, IL", capital, dt(2018,5,12))) for capital in capitals()]
# print(prices)

def durations_only():
    airport_data = "../data/airportCodes.csv"
    df = pd.read_csv(airport_data)

    # cities
    cities = df["City"].tolist()

    # get the travl time in seconds - driving time
    durations = all_durations(cities) # list of tuples (city, duration)

    durations = [el[1] for el in durations] # in seconds. Hawaii should have "N/A"
    dur_df = pd.DataFrame(columns=['City', 'Duration'])
    dur_df['City'] = cities
    dur_df['Duration'] = durations

    return dur_df


def main():
    airport_data = "../data/airportCodes.csv"
    df = pd.read_csv(airport_data)

    start_date = firstFriday() + relativedelta(days=7) # second friday of the year

    # direction is independent of the day if all goes well
    cities = df["City"].tolist()
    airports = df['Airport'].tolist()

    # assuming I travel every friday. 50 states including start date. so 350=7*50 not includded
    flight_dates = [start_date + relativedelta(days=el) for el in range(0,350,7)]

    new_df = pd.DataFrame(columns=['City', 'Date', 'Airport'])
    new_df['Date'] = np.tile(flight_dates, 50)
    new_df['City'] = np.repeat(cities, 50)
    new_df['Airport'] = np.repeat(airports, 50)

    # apply cost function
    def cost_on_row(row):
        return getPrice(expedia("PIA", row['Airport'], row['Date']))

    new_df['Cost'] = new_df.apply(cost_on_row, axis=1)


    return new_df

if __name__ == '__main__':
    df = main()
    df.to_csv("../data/finalData.csv", index=False)