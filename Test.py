import unittest



from opencellid_service import CoordWithAddress, Coord, TrafficDataSet, GeoCodingService, get_cells, azimuth, \
    check_azimuth_difference, TraficMap
import Levenshtein
from  folium.plugins import SemiCircle, TimeSliderChoropleth, MarkerCluster
import folium

class TestCoordWithAddress(unittest.TestCase):

    def test_azimitn(self):
        point1 = Coord(50.4218266, 30.7049994)
        point2 = Coord(50.4218266, 30.7049994)
        az = azimuth(point1, point2)
        print(az)

        point1 = Coord(50.4218266, 30.7049994)
        point2 = Coord(50.42197012039068, 30.70822877762935)
        az = azimuth(point1, point2)
        print(az)

    def test_azimut(self):
        tower = Coord(50.46621758686562, 30.61527026448282) #Шалет
        adress = Coord(50.46855313570581, 30.603747494373835) # місто Київ, вул. Воскресенська, буд. 14-Б
        az = azimuth(tower, adress)
        print(az)

        az = azimuth(adress, tower)
        print(az)


    def test_get_coordinates(self):
        # Перевіряємо, чи повертає None для некоректної адреси
        with self.assertRaises(ValueError):
            address = "Some non-existent address"
            CoordWithAddress(address).get_coordinates()

        # Перевіряємо, чи повертає коректні координати для коректної адреси
        address = "1600 Amphitheatre Parkway, Mountain View, CA"
        coords = CoordWithAddress(address).get_coordinates()
        self.assertEqual(coords, (37.4223878, -122.0841877))

        # Перевіряємо, чи повертає коректні координати для коректної адреси
        address = "МІСТО КИЇВ, ВУЛ. МІСТА ШАЛЕТТ, 1"
        coords = CoordWithAddress(address).get_coordinates()
        self.assertEqual(coords, (50.46620970000001, 30.6152663))

        # Перевіряємо, чи повертає коректні координати для коректної адреси
        address = "МІСТО КИЇВ, ВУЛ. Бориспільська, 27а"
        coords = CoordWithAddress(address).get_coordinates()
        self.assertEqual(coords, (50.4218266, 30.7049994))

    def test_get_home_coord(self):
        address = "місто Київ, вул. Воскресенська, буд. 14-Б"
        coords = CoordWithAddress(address).get_coordinates()
        print (f'{address, coords}' )
        self.assertEqual(coords, (50.4686032, 30.6030372))

        address = "місто Бровари, вул. Київська, буд. 265/2"
        coords = CoordWithAddress(address).get_coordinates()
        print(f'{address, coords}')
        self.assertEqual(coords, (50.5252634, 30.7906036))

    def test_get_cells(self):
        address_home = ["місто Київ, вул. Воскресенська, буд. 14-Б","місто Бровари, вул. Київська, буд. 265/2"]
        cells_adress = []
        for item in address_home:
            coords = CoordWithAddress(item).get_coordinates()
            print (f'адреса {item}')
            cells_adress.append(get_cells(coords[0], coords[1], 2))

        geoloc_service = GeoCodingService()
        iniq_adress =set()
        for item in cells_adress:
            for cell in item:
                lat = cell.coord.lat
                lon = cell.coord.lon
                address_tower=geoloc_service.get_address_from_coord(lat, lon)
                if not address_tower.address in iniq_adress:
                    iniq_adress.add(address_tower.address)
                    print(f'адреса башти {address_tower}, {lat}, {lon}')






    def test_distance(self):
        cell1 = Coord(50.466091, 30.614973)
        cell2 = Coord(50.466332, 30.615938)
        dist=cell1.distance(cell2)
        self.assertEqual(dist, 73.57309371481297)

    def test_readfromfile(self):
        ds=TrafficDataSet('/Volumes/SP PHD U3/Documents/Трафіки/МТС/GD_22_16994.xlsx')

    def test_get_toweradress_and_save(self):
        ds=TrafficDataSet('/Volumes/SP PHD U3/Documents/Трафіки/МТС/GD_22_16994.xlsx')
        ds.address_column_name = 'БС'
        address_towers = ds.get_towers_address('БС')

        ds.get_coord_from_address(address_towers)
        ds.add_coord_to_dataframe_and_save_to_file()

    def test_get_toweradress_and_print(self):
        ds=TrafficDataSet()
        ds.read_dataset('/Volumes/SP PHD U3/Documents/Трафіки/МТС/GD_22_16994_1.xlsx', skiprows=0)
        ds.address_column_name = 'БС'
        address_towers = ds.get_towers_address('БС')
        print('кількість базових станцій = ', len(address_towers))
        print(address_towers)

    def test_get_tower_coord(self):
        ds = TrafficDataSet()
        ds.read_dataset('/Volumes/SP PHD U3/Documents/Трафіки/МТС/GD_22_16994_1.xlsx', skiprows=0)
        ds.address_column_name = 'БС'
        address_towers = ds.get_towers_address('БС')
        geoloc_service = GeoCodingService()
        for address in address_towers:
            try:
                coords = geoloc_service.get_coord(address)
            except:
                print(f'для адреси {address} координати не визначені')
                coords = None

            if not coords is None:
                check_address = geoloc_service.get_address_from_coord(coords[0], coords[1])
                distance = Levenshtein.distance(address, check_address)
                print(f'адреса {address} коорд {coords}, Левенштейн {distance}, {check_address}')



    def test_generate_filename(self):
        ds = TrafficDataSet()
        ds.file_path = '/Volumes/SP PHD U3/Documents/Трафіки/МТС/GD_22_16994.xlsx'
        print(ds.generate_file_name())

    def test_show_map(self):
        ds = TrafficDataSet()

        ds.file_path = '/Volumes/SP PHD U3/Documents/Трафіки/МТС/'
        ds.address_column_name = 'БС'
        ds.put_towers_to_map()
        res = ds.get_count_connection_by_tower()
        #print(res)

    def test_preparing_data(self):
        ds = TrafficDataSet()
        ds.read_dataset('/Volumes/SP PHD U3/Documents/Трафіки/МТС/GD_22_16994_1.xlsx', skiprows=0)
        ds.file_path = '/Volumes/SP PHD U3/Documents/Трафіки/МТС/'
        ds.address_column_name = 'БС'
        ds.preparing_data()

    def test_count_dist(self):
        df = TrafficDataSet()
        df.file_path = '/Volumes/SP PHD U3/Documents/Трафіки/МТС/GD_22_16994_1.xlsx'
        df.read_dataset(df.file_path, skiprows=0)
        address = "місто Київ, вул. Воскресенська, буд. 14-Б"
        coords = CoordWithAddress(address).get_coordinates()
        print(f'{address, coords}')
        self.assertEqual(coords, (50.4686032, 30.6030372))
        df.count_dist_tower_and_coord(Coord(coords[0], coords[1]))
        file_name = df.generate_file_name()
        df.df.to_excel(file_name)

    def test_count_connection_group_by_day(self):
        df = TrafficDataSet()
        df.file_path = '/Volumes/SP PHD U3/Documents/Трафіки/МТС/GD_22_16994_1_1.xlsx'
        df.read_dataset(df.file_path, skiprows=0)
        grouped_df = df.count_connection_group_by_day(1000)
        grouped_df.to_excel('/Volumes/SP PHD U3/Documents/Трафіки/МТС/По днях.xlsx')


    def test_check_azimuth_difference(self):

        self.assertTrue(check_azimuth_difference(360, 60))
        self.assertTrue(check_azimuth_difference(120, 60))
        self.assertTrue(check_azimuth_difference(340, 0))
        self.assertTrue(check_azimuth_difference(60, 0))

        self.assertTrue(check_azimuth_difference(50, 350))
        self.assertTrue(check_azimuth_difference(290, 350))

        self.assertTrue(check_azimuth_difference(60, 120))
        self.assertTrue(check_azimuth_difference(180, 120))

        self.assertTrue(check_azimuth_difference(70, 10))
        self.assertTrue(check_azimuth_difference(359, 10))

        self.assertFalse(check_azimuth_difference(359, 60))
        self.assertFalse(check_azimuth_difference(121, 60))
        self.assertFalse(check_azimuth_difference(299, 0))
        self.assertFalse(check_azimuth_difference(61, 0))

        self.assertFalse(check_azimuth_difference(51, 350))
        self.assertFalse(check_azimuth_difference(289, 350))

        self.assertFalse(check_azimuth_difference(59, 120))
        self.assertFalse(check_azimuth_difference(181, 120))

        self.assertFalse(check_azimuth_difference(71, 10))
        self.assertFalse(check_azimuth_difference(309, 10))

    def test_semi_color(self):

        address = "місто Київ, вул. Воскресенська, буд. 14-Б"
        #coords = CoordWithAddress(address).get_coordinates()
        #print(f'{address, coords}')
        #self.assertEqual(coords, (50.4686032, 30.6030372))

        map = TraficMap()
        map.add_basic_point(location=Coord(50.4686032, 30.6030372), address_name=address)
        row ={'Дата та час':'01.01.2020  00:28:04',
              'Азимут':290,
              'lat': 50.4662097,
              'lon': 30.6152663,
        }
        map.add_trafic_segment(row)
        map.save('/Volumes/SP PHD U3/Documents/Трафіки/МТС/map.html')

    def test_time_stamp(self):
        df = TrafficDataSet()
        df.file_path = '/Volumes/SP PHD U3/Documents/Трафіки/МТС/GD_22_16994_1_1.xlsx'
        df.read_dataset(df.file_path, skiprows=0)
        df_filtered = df.df[(df.df['azimuth_in_range'] == True) &
                              (df.df['dist'] < 1000) &
                              (df.df['Дата та час'].dt.hour >= 0) &
                              (df.df['Дата та час'].dt.hour < 6)]
        map = TraficMap()
        address = "місто Київ, вул. Воскресенська, буд. 14-Б"
        map.add_basic_point(location=Coord(50.4686032, 30.6030372), address_name=address)
        map.add_trafic_data(df_filtered)

        # time_slider = TimeSliderChoropleth(
        #     data=df_filtered.to_json(date_format='iso'),
        #     styledict ={'2020-01-01': {'color':'red'}}
        #
        # ).add_to(map.map)

        folium.LayerControl().add_to(map.map)
        map.save('/Volumes/SP PHD U3/Documents/Трафіки/МТС/map.html')

    def test_chat_gpt(self):
        m = TraficMap()
        m1=folium.Marker([45.523, -122.675], popup='Portland, OR')
        m2=folium.Marker([45.523, -121.675], popup='Another marker')
        m3=folium.Marker([45.523, -123.675], popup='Another marker')

        # mCluster = folium.MarkerCluster(name="Stores").add_to(mymap)
        mCluster_hg = MarkerCluster(name="home goods").add_to(m.map)
        mCluster_bea = MarkerCluster(name="beauty")
        mCluster_ele = MarkerCluster(name="electronics")

        mCluster_hg.add_child(m1)
        mCluster_ele.add_child(m2)
        mCluster_bea.add_child(m3)

        mCluster_ele.add_child(mCluster_bea)
        mCluster_ele.add_to(m.map)
        mCluster_bea.add_to(m.map)



        # Створення об'єкту folium.LayerControl() та додавання його до карти
        folium.LayerControl().add_to(m.map)
        m.save('/Volumes/SP PHD U3/Documents/Трафіки/МТС/map_chatgpt.html')

if __name__ == '__main__':
    unittest.main()