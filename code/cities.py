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

def durations_only(airport_data = "../data/airportCodes.csv"):
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


def main(airport_data = "../data/airportCodes.csv", year=2019):
    df = pd.read_csv(airport_data)

    start_date = firstFriday(year) + relativedelta(days=7) # second friday of the year

    # direction is independent of the day if all goes well
    cities = df["City"].tolist()
    airports = df['Airport'].tolist()

    # assuming I travel every friday. 50 states including start date. so 350=7*50 not includded
    flight_dates = [start_date + relativedelta(days=el) for el in range(0,350,7)]
    today = dt.today()
    flight_dates = [pd.to_datetime(date) for date in flight_dates if date > today]

    new_df = pd.DataFrame(columns=['City', 'Date', 'Airport'])
    new_df['Date'] = np.tile(flight_dates, len(cities))
    new_df['City'] = np.repeat(cities, len(flight_dates))
    new_df['Airport'] = np.repeat(airports, len(flight_dates))

    # apply cost function
    def cost_on_row(row):
        return getPrice(expedia("PIA", row['Airport'], row['Date']))

    new_df['Cost'] = new_df.apply(cost_on_row, axis=1)
    # costs = []
    # for _, row in new_df.iterrows():
    #     costs.append(getPrice(expedia("PIA", row['Airport'], pd.to_datetime(row['Date']))))
    #
    # new_df['Cost'] = costs

    return new_df

def merger(dur_df, cost_df):
    # assuming durtions and cost data are available.
    merged_df = cost_df.merge(dur_df, how='left', on='City')
    merged_df['Cost'] = merged_df['Cost'].replace('[\$,]', '', regex=True).astype(float)

    merged_df_group = merged_df.groupby('City').agg({"Cost":np.mean})

    # imputation
    def impute(row):
        return merged_df_group.loc[row['City'], 'Cost']

    merged_df_imputed = merged_df.apply(lambda row: row.fillna(impute(row)), axis=1)

    merged_df_best_day = dict()
    dates = merged_df_imputed['Date'].unique().tolist()
    dates = [pd.to_datetime(date) for date in dates]
    cities = merged_df_imputed['City'].unique().tolist()
    all_nan_cities = merged_df_imputed.groupby('City').agg({'Cost': lambda x: all(pd.isnull(x)),
                                                            'Date': lambda x: all(pd.isnull(x))})

    all_nan_dates = all_nan_cities[all_nan_cities['Date'] == True]
    all_nan_dates = all_nan_dates.index.values.tolist()

    all_nan_cities = all_nan_cities[all_nan_cities['Cost'] == True]
    all_nan_cities = all_nan_cities.index.values.tolist()

    cities_for_dict = []
    dates_for_dict = []
    if len(cities) == len(dates):
        for date in dates:
            temp = merged_df_imputed[(merged_df_imputed['Date'] == date) &
                                     (merged_df_imputed['City'].isin(cities))]
            # minimum cost on this day
            min_cost = temp['Cost'].min()

            # if we had all NaN on this day skip it.
            if pd.isnull(min_cost):
                city = all_nan_cities[0]
                cities_for_dict.append(city)
                all_nan_cities.remove(city)
                continue  # we will have to add cities with NAN at the end

            # the first city with this minimum cost
            city = temp.loc[temp['Cost'] == min_cost, "City"].iloc[0]
            cities_for_dict.append(city)
            cities.remove(city)

        if len(cities_for_dict) != len(dates):
            cities_for_dict.extend(all_nan_cities)

        merged_df_best_day['Best Day'] = dates
        merged_df_best_day['City'] = cities_for_dict

        merged_df_best_day = pd.DataFrame(merged_df_best_day)
    elif len(cities) < len(dates):
        for city in cities:
            temp = merged_df_imputed[(merged_df_imputed['City'] == city) &
                                     (merged_df_imputed['Date'].isin(dates))]
            min_cost = temp['Cost'].min()
            if pd.isnull(min_cost):
                date = all_nan_dates[0]
                dates_for_dict.append(date)
                all_nan_dates.remove(date)
                continue

            date = temp.loc[temp['Cost'] == min_cost, "Date"].iloc[0]
            dates_for_dict.append(date)
            dates.remove(date)

        merged_df_best_day['Best Day'] = dates_for_dict
        merged_df_best_day['City'] = cities

        merged_df_best_day = pd.DataFrame(merged_df_best_day)
    else:
        # Makes no sense
        return None


    full_data = merged_df_imputed.merge(merged_df_best_day, how='left', on='City')

    return full_data

if __name__ == '__main__':
    df = main()
    df.to_csv("../data/finalData.csv", index=False)