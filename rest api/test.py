from flask import Flask, jsonify, abort
from flask_restful import Api, Resource, reqparse
from geopy.geocoders import Nominatim
import rasterio as rio
import glob
import json


def address_to_latlon(location):
    try:
        loc = Nominatim(user_agent='test_1')
        location = loc.geocode(location)
        data = location.latitude, location.longitude
    except AttributeError:
        data = None, None

    return data

#load config
with open('config.json', 'r') as f:
    config = json.load(f)

def raster_read(latitude, longitude):
    #might change read file function
    # add looping for files end with tif, return raster path and pixel value might have many raster file

    raster_folder = config['raster_folder']
    print(raster_folder)
    files = glob.glob(f'{raster_folder}/*.tif')

    outputs = []
    for file in files:
        # open the raster file
        with rio.open(file) as raster_data:
        # read first band
            raster_value = raster_data.read(1)
            rowIndex, colIndex = raster_data.index(longitude, latitude)
            try:
                pixel_value = raster_value[rowIndex, colIndex]
                #change to more dynamic(depth)
                raster_data = {'raster_name': file, 'depth': int(pixel_value)}
                outputs.append(raster_data)
            except IndexError:
                outputs = []
    return outputs



app = Flask(__name__)
api = Api(app)


input_post_args = reqparse.RequestParser()
# input_post_args.add_argument("raster_path", type=str, help='raster file is needed', required=True)
input_post_args.add_argument("address", type=str, help='address is needed', required=True)


class Output(Resource):
    def get(self):
        return {'data': {'message': 'no output for this method'}}, 200

    def post(self):
        args = input_post_args.parse_args()
        address = args['address']
        # raster_path = args['raster_path']
        latitude, longitude = address_to_latlon(location=address)
        if latitude is None:
            abort(404, description="Address is unrecognizable")
        #catch error 2 AttributeError: 'NoneType' object has no attribute 'latitude'
        raster_output = raster_read(latitude=latitude, longitude=longitude)
        #catch error 1 index IndexError: index -5048 is out of bounds for axis 0 with size 3601
        if not raster_output:
            abort(404, description="address is out of range for raster image")
        output = {'data': {'address': address,
                           # 'raster_path': raster_path,
                           'latitude': latitude,
                           'longitude': longitude,},
                  'raster_output': raster_output}

        return jsonify(output)

api.add_resource(Output, '/output')

if __name__ == '__main__':
    app.run(debug=True)


### might encounter problem
#1. nominatim not very suitable for product base (cant do many request, not very reliable and cannot locate many addresses esp duopharma).

