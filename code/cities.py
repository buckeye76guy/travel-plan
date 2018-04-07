from functions import get_credentials, distanceMatrix, getDuration
import re

def cities():
    cities = "../data/cities.txt"

    with open(cities, 'r') as f:
        cities = f.readlines()

    return [city.strip() for city in cities]

# print(cities())

def all_durations(cities):
    mykey = get_credentials('../credentials/apkeys.txt').get('WeekendTravels')
    results = distanceMatrix(mykey, origin='Peoria, IL', destination=cities)
    durations = getDuration(results)

    # had to remove hawaii from the list since you cannot drive to hawaii
    return durations


def cities_within_six_hours(durations, threshold=6*60*60):
    return [re.sub(', USA', '', el[0]) for el in durations if el[1] <= threshold]

print(cities_within_six_hours(all_durations(cities())))