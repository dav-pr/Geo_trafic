""" This module contained funtionals for reading geo data from inner"""

import plotly.express as px
import pandas as pd



if __name__ == '__main__':

    us_cities = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/us-cities-top-1k.csv")

    fig = px.scatter_mapbox(us_cities, lat="lat", lon="lon", hover_name="City", hover_data=["State", "Population"],
                            color_discrete_sequence=["fuchsia"], zoom=3, height=600)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.show()

