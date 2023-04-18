#!/usr/bin/python3
import webbrowser
from math import cos, sqrt, pi
import argparse
import requests
import json

from geopy import distance, GoogleV3
from geographiclib.geodesic import Geodesic

from decouple import config

import pandas as pd
import os
import folium
from  folium.plugins import SemiCircle, TimeSliderChoropleth

import Levenshtein


# Static
PREFIX = "https://opencellid.org/cell/getInArea?key="
PARAM = "&format=json"
OPENCELLID_KEY = config("OPENCELLID_KEY")
GOOGLE_MAPS_KEY = config('GOOGLE_MAPS_KEY')

# Class that represents a coordinate
#50.46630528113815, 30.615234111143295
class Coord:
    def __init__(self, lat=0, lon=0):
        self.lat = lat
        self.lon = lon

    # Constructor to parse coordinates from string in format: 'lat,lon'
    @classmethod
    def from_str(self, s):
        try:
            lat, lon = map(float, s.split(','))
            return self(lat, lon)
        except ValueError:
            print("Error: could not parse location, quitting.")
            quit()

    # Takes number of decimal numbers, default 5
    # Returns Cooridnate as str in format: lat,lon
    def to_str(self, d=5):
        return str(round(self.lat, d)) + ',' + str(round(self.lon, d))

    # Takes a  area size in km^2.
    # Returns coordiantes of the corners of the sqare with given area,
    # surrounding the center
    def square_from_point(self, area=1.0):
        c = 111.3  # km/°
        a = sqrt(area) / 2  # km

        lat_del = a / c
        lon_del = a / (c * cos(self.lat * (pi / 180)))

        p_max = Coord(self.lat + lat_del, self.lon + lon_del)
        p_min = Coord(self.lat - lat_del, self.lon - lon_del)
        return (p_max, p_min)

    def get_coordinates(self):
        return self.lat, self.lon

    def distance(self, point):
        try:
            return distance.distance((self.lat, self.lon), (point.lat, point.lon)).meters
        except ValueError:
            return None


    def azimuth(self,point):
        pass


def azimuth(point_1:Coord, point_2: Coord):
    try:
        brng = Geodesic.WGS84.Inverse(point_1.lat, point_1.lon, point_2.lat, point_2.lon)['azi1']
        brng = (brng + 360) % 360
        return brng
    except ValueError:
        return  None

class GeoCodingService():
    def __init__(self):
        super().__init__()
        self.geolocator = GoogleV3(api_key=GOOGLE_MAPS_KEY)

    def get_coord(self, address):
        location = self.geolocator.geocode(address)
        if location:
            self.address = address
            return (location.latitude, location.longitude)
        else:
            raise ValueError(f'для адреси {address} на вдалося отримати координати')

    def get_address_from_coord(self, lat, long):
        return self.geolocator.reverse(f"{lat}, {long}", language = 'uk')




class CoordWithAddress(Coord):
    url = "https://maps.googleapis.com/maps/api/geocode/json"

    def __init__(self, address):

        super().__init__()
        self.geolocator = GoogleV3(api_key=GOOGLE_MAPS_KEY)
        location = self.geolocator.geocode(address)
        if location:
            self.lat = location.latitude
            self.lon = location.longitude
            self.address = address
        else:
            raise ValueError(f'для адреси {address} на вдалося отримати координати')



    def get_address_from_coord(self, lat, long):
        return self.geolocator.reverse(f"{lat}, {long}")





        # # url = "https://maps.googleapis.com/maps/api/geocode/json"
        # params = {"address": address, "key": GOOGLE_MAPS_KEY}
        # response = requests.get(self.url, params=params).json()
        # if response["status"] == "OK":
        #     location = response["results"][0]["geometry"]["location"]
        #     self.lat = location["lat"]
        #     self.lon = location["lng"]
        #     self.address = address
        #
        # else:
        #     raise ValueError(f'для адреси {address} на вдалося отримати координати')




class Tower():

    def __init__(self, cellid, coord: Coord, lac, mcc, mnc, radio):
        self.cellid = cellid
        self.coord = coord
        self.lac = lac
        self.mcc = mcc
        self.mnc = mnc
        self.radio = radio

    def __str__(self):
        return "{cid:9d} | {lat:8f}, {lon:8f} | {lac:5d} | {mcc:3d} | {mnc:d} | {radio}".format(
            cid=self.cellid,
            lat=self.coord.lat,
            lon=self.coord.lon,
            lac=self.lac,
            mcc=self.mcc,
            mnc=self.mnc,
            radio=self.radio)


class TrafficDataSet():

    def __init__(self, file_path = None, address_column_name = None):
        if not file_path is None:
            self.df = self.read_dataset(file_path)
        self.address_column_name = address_column_name
        self.file_path = file_path

    def get_towers_address(self, col_name = None):
        """
        Метод отримує відсортований набір унікальних адрес базових станцій.
        :param col_name:
        :return:
        """
        if col_name is None:
            col_name = self.address_column_name
        towers_address = list(self.df[col_name].unique().astype(str))
        towers_address = sorted(towers_address)
        #print('кількість базових станцій = ', len(towers_address))
        #print (towers_address)
        return towers_address

    def read_dataset(self, file_path, skiprows=10):
        self.df = pd.read_excel(file_path, skiprows=skiprows)
        print(self.df.head())
        return self.df

    def get_coord_from_address(self, ds_towers_address):
        address_coord={}
        address_coord_lat = {}
        address_coord_lon = {}


        for tower_address in ds_towers_address:
            try:
                address_coord[tower_address] = CoordWithAddress(tower_address)
                address_coord_lat[tower_address] = CoordWithAddress(tower_address).lat
                address_coord_lon[tower_address] = CoordWithAddress(tower_address).lon

            except ValueError as e:
                print (e)
                address_coord[tower_address] = (0,0)

        self.uniq_tower_address_with_coord_dict=address_coord
        self.uniq_tower_lat_dict = address_coord_lat
        self.uniq_tower_lon_dict = address_coord_lon

    def add_coord_to_dataframe_and_save_to_file(self):

        if self.uniq_tower_address_with_coord_dict:
            self.df['lat'] = self.df[self.address_column_name].map(self.uniq_tower_lat_dict)
            self.df['lon'] = self.df[self.address_column_name].map(self.uniq_tower_lon_dict)

        file_name = self.generate_file_name()
        self.df.to_excel(file_name)






    def count_dist_tower_and_coord(self, point:Coord):

        self.df['dist'] = self.df.apply(lambda row: point.distance(Coord(row['lat'], row['lon'])), axis=1)
        self.df['azimuth'] = self.df.apply(lambda row: azimuth(Coord(row['lat'], row['lon']), point),   axis=1)
        self.df['azimuth_in_range'] = self.df.apply(lambda row: check_azimuth_difference(row['azimuth'], row['Азимут'] ), axis=1)

    def count_connection_group_by_day(self, distance = 1500 ):

        # Групування результату за датою
        df_filtered = self.df[(self.df['azimuth_in_range'] == True) &
                              (self.df['dist']< 1500) &
                              (self.df['Дата та час'].dt.hour >= 0 ) &
                              (self.df['Дата та час'].dt.hour < 6)]
        grouped_df = df_filtered.groupby(pd.Grouper(key='Дата та час', freq='D')).count()
        print(grouped_df)
        return grouped_df

    def generate_file_name(self):
        file_name = os.path.basename(self.file_path)
        file_path = os.path.dirname(self.file_path)
        file_name_without_extension = os.path.splitext(file_name)[0]
        extension = os.path.splitext(file_name)[1]
        i = 1
        file_exist = True
        while file_exist:
            file_name_to_save = file_path + os.sep + file_name_without_extension + '_' + str(i) + extension
            file_exist = os.path.exists(file_name_to_save)

        return file_name_to_save

    def get_count_connection_by_tower(self):
        count_conn = self.df.groupby(self.address_column_name)['Дата та час'].count()
        return count_conn
    def get_max_connection_by_tower(self):

        return self.get_count_connection_by_tower().max()


    def preparing_data(self):

        unique_coord = {}

        for index, row in self.df.iterrows():
            if not (row['lat'], row['lon']) in unique_coord:
                unique_coord[(row['lat'], row['lon'])] = row[self.address_column_name]
            else:
                address_in_dict =  unique_coord[(row['lat'], row['lon'])]
                address_in_df = row[self.address_column_name]
                distance = Levenshtein.distance(address_in_dict, address_in_df)
                print (f'схожість строк = {distance} {address_in_dict} {address_in_df}')
                if distance < 3 and distance >0:
                    self.df.loc[self.df[self.address_column_name] == address_in_df, self.address_column_name] = address_in_dict
                    print('виконанна заміна')



    def put_towers_to_map(self):

        kyiv_map = folium.Map(
            location=[50.448726282306026, 30.51963482592583],
            zoom_start=12,

        )

        count_conn = self.get_count_connection_by_tower()
        max_conn = self.get_max_connection_by_tower()
        uniq_address={}
        for index, row in self.df.iterrows():
            if not row[self.address_column_name] in uniq_address:
                try:
                    uniq_address[row[self.address_column_name]]=[row['lat'], row['lon']]

                    if count_conn.loc[row[self.address_column_name]] > max_conn*0.3:
                        icon_color = 'red'
                        print(f'встановлено червоний кольор {max_conn} , {count_conn.loc[row[self.address_column_name]]}')
                        print(f'{row[self.address_column_name]}')

                    else:
                        icon_color = 'blue'
                        #print(f'к-кість з\'єднань {count_conn.loc[row[self.address_column_name]]} - max {max_conn}')

                    if True:
                        folium.Marker([row['lat'], row['lon']],
                                      popup=f'<h4> {row[self.address_column_name]} </h4> '
                                            f'<h5> кількість з\'єднань {count_conn.loc[row[self.address_column_name]]} </h5>',
                                      icon = folium.Icon(icon='tower', icon_color=icon_color),
                                      ).add_to(kyiv_map)

                except ValueError:
                    print (f"помилка  розміщення на мапі: {row[self.address_column_name]} {row['lat']} {row['lon']}")
                except KeyError:
                    print(f"помилка  розміщення на мапі: {row[self.address_column_name]} {row['lat']} {row['lon']}")


        html_page = f'{os.path.dirname(self.file_path)}/map.html'
        kyiv_map.save(html_page)
        # open in browser.
        webbrowser.open(html_page, new=1)

    def put_trafic_to_map(self):
        kyiv_map = folium.Map(
            location=[50.448726282306026, 30.51963482592583],
            zoom_start=12,

        )
        for index, row in self.df.iterrows():
            pass


class TraficMap():
    def __init__(self, location = [50.448726282306026, 30.51963482592583], zoom_start = 12, distance= 1000):
        self.map = folium.Map(
            location=location,
            zoom_start=zoom_start,
        )
        self.distance = distance


    def add_basic_point(self, location:Coord, address_name):
        folium.Marker([location.lat, location.lon],
                      popup=f'<h4> {address_name} </h4> ',
                      icon=folium.Icon(icon='home', icon_color='red'),
                      ).add_to(self.map)

    def add_trafic_segment(self, row):
        semi_circle = SemiCircle(
            location=[row['lat'], row['lon']],
            radius=self.distance,
            direction=row['Азимут'],
            arc = 120,
            line_color='#FF0000',
            fill_color='#FFA500',
            fill_opacity=0.5,
            popup=f"<h5> {row['Дата та час']} </h5>"
        )
        semi_circle.add_to(self.map)

    def add_trafic_data(self, df):
        for index, row in df.iterrows():
            self.add_trafic_segment(row)


    def save(self, file_name):
        self.map.save(file_name)








def get_cells(lat, lon, area=0.1):


    loc = Coord(lat, lon)
    p_max, p_min = loc.square_from_point(area)

    # api request
    url = PREFIX + OPENCELLID_KEY + "&BBOX=" + p_min.to_str() + ',' + p_max.to_str() + PARAM
    api_result = requests.get(url)

    api_result = json.loads(api_result.text)
    #print(api_result)

    # if api_result['error']:
    #    print("Error while reading opencellid API:\n{}".format(api_result['error']))
    #    quit()

    # pretty printing
    print(str(api_result['count']) + ' Stations Found')
    print("{:^10}|{:^10}, {:^10}|{:^7}|{:^5}|{:^3}| radio".format(
        "cellid", "lat", "lon", "lac", "mcc", "mnc"))
    print("{:->11}{:->23}{:->8}{:->6}{:->4}------".format("+", "+", "+", "+", "+"))

    cells= []
    for cell in api_result['cells']:
        tower = Tower(cellid=cell['cellid'],
                      coord=Coord(cell['lat'], cell['lon']),
                        lac=cell['lac'],
                        mcc=cell['mcc'],
                        mnc=cell['mnc'],
                        radio=cell['radio'])
        cells.append(tower)

        print("{cid:9d} | {lat:8f}, {lon:8f} | {lac:5d} | {mcc:3d} | {mnc:d} | {radio}".format(
            cid=cell['cellid'],
            lat=cell['lat'],
            lon=cell['lon'],
            lac=cell['lac'],
            mcc=cell['mcc'],
            mnc=cell['mnc'],
            radio=cell['radio']))

    return cells

def check_azimuth_difference(chack_azimuth, call_azimuth, arc = 60):
    difference = abs(chack_azimuth - call_azimuth)
    if difference > 180:
        difference = 360 - difference
    return difference <= arc



def main():
    parser = argparse.ArgumentParser(prog='area')
    parser.add_argument('-p', '--position', type=str, required=True,
                        help="Center position of the area. Format: lat,lon as floats")
    parser.add_argument('-k', '--key', type=str, required=True,
                        help="Your apikey")
    parser.add_argument('-a', '--area', type=float, default=0.1,
                        help="Size of the are in km²")

    args = parser.parse_args()
    loc = Coord.from_str(args.position)
    p_max, p_min = loc.square_from_point(args.area)

    # api request
    url = PREFIX + args.key + "&BBOX=" + p_min.to_str() + ',' + p_max.to_str() + PARAM
    api_result = requests.get(url)

    api_result = json.loads(api_result.text)
    print(api_result)

    # if api_result['error']:
    #    print("Error while reading opencellid API:\n{}".format(api_result['error']))
    #    quit()

    # pretty printing
    print(str(api_result['count']) + ' Stations Found')
    print("{:^10}|{:^10}, {:^10}|{:^7}|{:^5}|{:^3}| radio".format(
        "cellid", "lat", "lon", "lac", "mcc", "mnc"))
    print("{:->11}{:->23}{:->8}{:->6}{:->4}------".format("+", "+", "+", "+", "+"))

    for cell in api_result['cells']:
        print("{cid:9d} | {lat:8f}, {lon:8f} | {lac:5d} | {mcc:3d} | {mnc:d} | {radio}".format(
            cid=cell['cellid'],
            lat=cell['lat'],
            lon=cell['lon'],
            lac=cell['lac'],
            mcc=cell['mcc'],
            mnc=cell['mnc'],
            radio=cell['radio']))


if __name__ == "__main__":
    main()