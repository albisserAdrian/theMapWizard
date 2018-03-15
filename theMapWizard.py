#! python3
"""
Filename: theMapWizard.py
Description: Generates a google map image from user defined coordinates using 
custom styles. Based on a script by by heltonbiker.
Author: Adrian Albisser
Date created: 06/06/2017
Date Last modified: 15/03/2018
Version: 1.0
"""

import os
import json
import re
import glob
import time
import random
import urllib.parse
from urllib.request import urlopen
from math import log, exp, tan, atan, pi, ceil
from PIL import Image

##################################################################################
### Important Variables
##################################################################################

# Your google maps api key
GOOGLE_MAPS_API_KEY = ""

# Earth Radius Google Maps uses
EARTH_RADIUS = 6378137
# Calculate circumference = PI*2r 
EARTH_CIRCUMFERENCE = 2 * pi * EARTH_RADIUS
# Google Map Tile is 256px
INITIAL_RESOLUTION = EARTH_CIRCUMFERENCE / 256.0
ORIGIN_SHIFT = EARTH_CIRCUMFERENCE / 2.0
# Scale affects the number of pixels that are returned.
SCALE = 1
# Size of individual image
MAX_SIZE = 600


##################################################################################
### Functions
##################################################################################

def program_intro():
    # Title to display at the top
    print("                                                                             ")
    print("           ████████╗██╗  ██╗███████╗    ███╗   ███╗ █████╗ ██████╗           ") 
    print("           ╚══██╔══╝██║  ██║██╔════╝    ████╗ ████║██╔══██╗██╔══██╗          ")
    print("              ██║   ███████║█████╗      ██╔████╔██║███████║██████╔╝          ")
    print("              ██║   ██╔══██║██╔══╝      ██║╚██╔╝██║██╔══██║██╔═══╝           ")
    print("              ██║   ██║  ██║███████╗    ██║ ╚═╝ ██║██║  ██║██║               ")
    print("              ╚═╝   ╚═╝  ╚═╝╚══════╝    ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝               ")
    print("                  ██╗    ██╗██╗███████╗ █████╗ ██████╗ ██████╗               ")
    print("                 ██║    ██║██║╚══███╔╝██╔══██╗██╔══██╗██╔══██╗               ")
    print("                 ██║ █╗ ██║██║  ███╔╝ ███████║██████╔╝██║  ██║               ")
    print("                 ██║███╗██║██║ ███╔╝  ██╔══██║██╔══██╗██║  ██║               ")
    print("                 ╚███╔███╔╝██║███████╗██║  ██║██║  ██║██████╔╝               ")
    print("                  ╚══╝╚══╝ ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝                ")
    print("                                                                             ")
    print("#############################################################################")
    print("###                        Author: Adrian Albisser                        ###")
    print("###                             Version: 1.0                              ###")
    print("#############################################################################")
    print("")


def get_user_coordinates(corner):
    # Validate coordinates
    while True:
        try:
            coordinates = input("Enter coordinates for {0} corner: ".format(corner))
            pattern = re.compile("^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$")
            if pattern.match(coordinates) is not None:
                return coordinates
            else:
                print("Invalid coordinates. Please try again!")
        except ValueError:
            print("Invalid input. Please try again!")


def get_user_number(description,range):
    # Validate number in range
    while True:
        try:
            number = int(input(description))
            if number >= 1 and number <= range:
                return number
            else:
                print("Invalid number. Please try again!")
        except ValueError:
            print("Invalid input. Please try again!")


def get_json_styles():
    # Returns list of files in root folder
    style_list = []
    for file in glob.glob("*.json"):
        style_list.append(file)
    return style_list


def encode_json_url(json_style_file):
    # Encodes json to url
    with open(json_style_file) as data_file:
        styles = json.load(data_file)

    style_url = ""

    for i in styles:
        style_url = style_url + "&style="
        if "featureType" in i:
            style_url = style_url + "feature:" + i["featureType"] + "%7C"
        if "elementType" in i:
            style_url = style_url + "element:" + i["elementType"] + "%7C"
        for style in i["stylers"]:
            if "color" in style:
                color = style["color"]
                color = color[1:]
                style_url = style_url + "color:0x" + color  + "%7C"
            if "saturation" in style:
                style_url = style_url + "saturation:" + str(style["saturation"])  + "%7C"
            if "lightness" in style:
                style_url = style_url + "lightness:" + str(style["lightness"]) + "%7C"
            if "visibility" in style:
                style_url = style_url + "visibility:" + style["visibility"] + "%7C"
            if "weight" in style:
                style_url = style_url + "weight:" + str(style["weight"]) + "%7C"
        style_url = style_url[:-3]

    return style_url

def latlontopixels(lat, lon, zoom):
    # Translates coordinates to pixels
    mx = (lon * ORIGIN_SHIFT) / 180.0
    my = log(tan((90 + lat) * pi/360.0))/(pi/180.0)
    my = (my * ORIGIN_SHIFT) /180.0
    res = INITIAL_RESOLUTION / (2**zoom)
    px = (mx + ORIGIN_SHIFT) / res
    py = (my + ORIGIN_SHIFT) / res
    return px, py

def pixelstolatlon(px, py, zoom):
    # Translates pixels back to coordinates
    res = INITIAL_RESOLUTION / (2**zoom)
    mx = px * res - ORIGIN_SHIFT
    my = py * res - ORIGIN_SHIFT
    lat = (my / ORIGIN_SHIFT) * 180.0
    lat = 180 / pi * (2*atan(exp(lat*pi/180.0)) - pi/2.0)
    lon = (mx / ORIGIN_SHIFT) * 180.0
    return lat, lon

##################################################################################
### Program
##################################################################################

# Print intro title
program_intro()

# Get coordinates from user
upper_left =  get_user_coordinates("upper left")
lower_right = get_user_coordinates("lower right")
print("")

# Define zoom level
zoom = get_user_number("Enter zoom (1 to 21): ",21)
print("")

# Print list of google maps style found in root folder
print("List of Google Maps style files:")

style_list = get_json_styles()
count = 0
for i in style_list:
    count = count + 1
    print("    " + str(count) + ". " + i)

print("")

selected_Style = get_user_number("Select a style file: ",count)
print("")

ullat, ullon = map(float, upper_left.split(","))
lrlat, lrlon = map(float, lower_right.split(","))

# Convert coordinates to pixels
ulx, uly = latlontopixels(ullat, ullon, zoom)
lrx, lry = latlontopixels(lrlat, lrlon, zoom)

# Calculate pixel dimension of final image
dx, dy = lrx - ulx , uly - lry

# Calculate rows and columns
cols, rows = int(ceil(dx/MAX_SIZE)), int(ceil(dy/MAX_SIZE))

# Calculate pixel dimensions of each small image
bottom = 120
width = int(ceil(dx/cols))
height = int(ceil(dy/rows))
extra_height = height + bottom

total_rows_cols = rows*cols
percentage = float(100 / (total_rows_cols+1))
count_final = 1

# Loop through image coordinates and stitch them together
final = Image.new("RGB", (int(dx), int(dy)))
for x in range(cols):
    for y in range(rows):
        dxn = width * (0.5 + x)
        dyn = height * (0.5 + y)
        latn, lonn = pixelstolatlon(ulx + dxn, uly - dyn - bottom/2, zoom)
        position = ",".join((str(latn), str(lonn)))
        print(str(round(percentage*count_final,1))+"% -> Column:", x, "Row:", y,"Position:", position)
        urlparams = urllib.parse.urlencode({"center": position,
                                        "zoom": str(zoom),
                                        "format": "png",
                                        "maptype": "roadmap",
                                        "size": "%dx%d" % (width, extra_height),
                                        "scale": SCALE
                                        })
        
        url = "https://maps.googleapis.com/maps/api/staticmap?" + urlparams + encode_json_url(style_list[int(selected_Style)-1]) + "&key=" + GOOGLE_MAPS_API_KEY
        f=urllib.request.urlopen(url)
        im=Image.open(f)
        final.paste(im, (int(x*width), int(y*height)))
        count_final = count_final + 1
        
        # Random sleep
        time.sleep(random.randint(1,5))

print("100% Done!")
print("")
print("Saving image...")    

# Generate image name and save file
file_name = "map " + time.strftime("%Y-%m-%d %H %M %S" + ".png")
final.save(file_name,"PNG")
path_to_file = os.getcwd()

print("Image saved to: " + path_to_file + "\\" + file_name)
print("")
print("Enjoy!")
input("Press Enter to exit...")
