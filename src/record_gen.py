#!/usr/bin/env python

import pickle
import numpy as np
from math import cos, pow, sin, sqrt
import csv
from operator import add, mul
import datetime

import stl
from stl import mesh
from mpl_toolkits import mplot3d
from matplotlib import pyplot

from record_globals import precision, tau, samplingRate,rpm, downsampling, thetaIter, diameter, radIncr, rateDivisor
from record_globals import radius, innerHole, innerRad, outerRad, rH, amplitude, depth, bevel, gW, incrNum
from record_globals import truncate, _3DShape

from basic_shape_gen import setzpos, shape_to_mesh, generatecircumference

# horizontial_modulation
def hm(x, y, gH):
  v0, v1 = radius - x,  radius - y
  m = sqrt(pow(v0, 2) + pow(v1, 2))
  h = (gH * (v0 / m), gH * (v1 / m), 0)
  return h

#Outer Upper vertex
def ou(r, a, b, theta, rH, gH) -> tuple:
  w = r + a * b
  x, y = w * cos(theta), w * sin(theta)
  v, h = (x, y, rH), hm(x, y, gH)  #v, h = (r + x, r + y, gH), hm(x, y, gH)
  return h[0] + v[0], h[1] + v[1], rH

#Inner Upper vertex
def iu(r, a, b, theta, rH, gH) -> tuple:
  w = r - gW - a * b
  x, y = w * cos(theta), w * sin(theta)
  v, h = (x, y, rH), hm(x, y, gH)  #v, h = (r + x, r + y, gH), hm(x, y, gH)
  return h[0] + v[0], h[1] + v[1], rH
  
#Outer Lower vertex
def ol(r, theta, gH) -> tuple:
  x, y = r * cos(theta), r * sin(theta)
  v, h = (x, y, gH), hm(x, y, gH)  #v, h = (r + x, r + y, gH), hm(x, y, gH)
  return h[0] + v[0], h[1] + v[1], rH  - 0.25

#Inner Lower vertex
def il(r, theta, gH) -> tuple:
  w = r - gW
  x, y = r * cos(theta), r * sin(theta)
  v, h = (x, y, gH), hm(x, y, gH)  #v, h = (r + x, r + y, gH), hm(x, y, gH)
  return h[0] + v[0], h[1] + v[1], rH - 0.25

def grooveHeight(audio_array, samplenum):
  baseline = rH-depth-amplitude
  return truncate(baseline*audio_array[int(rateDivisor*samplenum)], precision)

# r is the radial postion of the vertex beign drawn
def draw_spiral(audio_array, r, shape = _3DShape()):

  # Print number of grooves to draw
  # totalGrooveNum = len(audio_array) // (rateDivisor * thetaIter)

  #Inner while for groove position
  lastEdge = None
  index = samplenum = 0
  gH = grooveHeight(audio_array, samplenum)

  s1 = [ou(radius, amplitude, bevel, 0, rH, gH), iu(radius, amplitude, bevel, 0, rH, gH)]
  s2 = [ol(radius, 0, gH), il(radius, 0, gH)]
  shape.add_vertices(s1 + s2)
  shape.tristrip(s1, s2)
  while rateDivisor*samplenum < (len(audio_array)-rateDivisor*thetaIter+1):
      grooveOuterUpper = []
      grooveOuterLower = []
      grooveInnerUpper = []
      grooveInnerLower = []

      theta = 0
      while theta < tau:
          gH = grooveHeight(audio_array, samplenum)
          if index == 0:
              grooveOuterUpper.append(ou(r, amplitude, bevel, theta, rH, gH))
          grooveOuterLower.append(iu(r, amplitude, bevel, theta, rH, gH))
          grooveInnerUpper.append(ol(r, theta, gH))
          grooveInnerLower.append(il(r, theta, gH))
          r -= radIncr
          theta += incrNum
          samplenum += 1

      gH = grooveHeight(audio_array, samplenum)
      outer = grooveOuterUpper + grooveOuterLower
      inner = grooveInnerUpper + grooveInnerLower
      shape.add_vertices(outer + inner)

      lastEdge = grooveOuterUpper if index == 0 else inner

      if index == 0:
          #Draw triangle to close outer part of record
          shape.tristrip(lastEdge, grooveOuterUpper)
          shape.tristrip(grooveOuterUpper, grooveOuterLower)
          
          #Complete beginning cap if necessary
          s1 = [ou(r, amplitude, bevel, theta, rH, gH), iu(r, amplitude, bevel, theta, rH, gH)]
          shape.add_vertices(s1)
          shape.tristrip(s1,s1)
      else:
          shape.tristrip(lastEdge, grooveOuterLower)
      
      shape.tristrip(grooveOuterLower, grooveInnerLower)
      shape.tristrip(grooveInnerLower, grooveInnerUpper)

      index += 1
      print("Groove drawn: {}".format(index))
      
  # Draw groove cap
  stop1 = [ou(r, amplitude, bevel, 0, rH, gH), iu(r, amplitude, bevel, 0, rH, gH)]
  stop2 = [ol(r, 0, gH), il(r, 0, gH)]
  cap = stop1 + stop2
  shape.add_vertices(cap)

  #Draw triangles
  shape.tristrip(stop1,stop2)

  #Fill in around cap
  stop3 = [lastEdge[-1], (r+innerRad, r, rH)]
  shape.add_vertex(stop3[1])
  shape.tristrip(stop1, stop3)

  #Close remaining space between last groove and center hole
  remainingSpace, _ = setzpos(generatecircumference(0, innerRad))
  edgeOfGroove, _ = setzpos(generatecircumference(0, r))
  shape.add_vertices(remainingSpace + edgeOfGroove)

  shape.tristrip(remainingSpace, edgeOfGroove)

  return shape

# Main function
def main(filename, stlname):

  # Read in array of bytes as float
  lst = [x for x in csv.reader(open(filename, 'rt', newline=''), delimiter=',')][0]
  lst = [float(x) for x in lst if x != '']

  # Normalize the values
  m = pow(max(lst), 2)
  normalizedDepth = [truncate(x / m, precision) for x in lst]

  shapefile = open("pickle/{}_shape.p".format(rpm), 'rb')
  recordShape = pickle.load(shapefile)
  shapefile.close()
  
  print("Pre-engraving vertices: " + str(len(recordShape.get_vertices())))
  print("Pre-engraving faces: " + str(len(recordShape.get_faces())))

  ## For debugging
  # shape_to_mesh(draw_spiral(normalizedDepth, outerRad, recordShape)).save("grooves.stl")

  shape = draw_spiral(normalizedDepth, outerRad, recordShape)
  full_mesh = shape_to_mesh(shape)

  full_mesh.save("stl/" + stlname + ".stl", mode=stl.Mode.BINARY)

#Run program
if __name__ == '__main__':
    now = datetime.datetime.now()
    main("audio/sample.csv", "sample_engraved")
    print("Time taken: " + str(datetime.datetime.now() - now)[5:9])
