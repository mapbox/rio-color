import rasterio as rio
import numpy as np
import sys
from math import exp, ceil

__version__ = '0.0.0'

# The type to be used for all intermediate math
# operations. Should be a float because values will
# be scaled to the range 0..1 for all work.
math_type = np.float32

epsilon = np.finfo(math_type).eps

# The largest value representable by uint16:
max_int = np.iinfo(np.uint16).max


def to_math_type(arr):
  '''Convert an array from uint16 to 0..1, scaling down linearly'''
  return arr.astype(math_type)/max_int

def to_uint16(arr):
  '''Convert an array from 0..1 to uint16, scaling up linearly'''
  return (arr*max_int).astype(np.uint16)


# Color manipulation functions

def sigmoidal(arr, bias, contrast):

  alpha, beta = bias, contrast
  # We use the names a and b to match documentation.
  
  if alpha == 0:
    alpha = epsilon
  
  if beta == 0:
    return arr
  
  np.seterr(divide='ignore', invalid='ignore')
  
  if beta > 0:
    # Forward sigmoidal function:
    # (This is really badly documented in the wild/internet.
    # @virginiayung is the only person I trust to understand it.)
    numerator   = 1/(1+np.exp(beta*(alpha-arr))) - 1/(1+np.exp(beta*alpha))
    denominator = 1/(1+np.exp(beta*(alpha - 1))) - 1/(1+np.exp(beta*alpha))
    return numerator / denominator
  else:
    # Inverse sigmoidal function:
    # todo: account for 0s
    # todo: formatting ;)
    return (
      (beta*alpha) - np.log(
        (
          1 / (
            (arr/(1 + np.exp( beta*alpha - beta )))
            - (arr / (1 + np.exp( beta*alpha )))
            + (1 / (1 + np.exp( beta*alpha )))
          )
        )
        - 1)
      ) / beta



def gamma(arr, g):
  return arr**(1.0/g)


# Utility functions

def simple_atmo(rgb, haze, contrast, bias):
  '''A simple, non-adaptive atmospheric correction function.'''
	
  rgb = to_math_type(rgb)
	
  bias /= 100.0 # easier to express in the range 0..100
  
  gamma_b = 1 - haze
  gamma_g = 1 - (haze*(1/3.0))

  rgb[1] = gamma(rgb[1], gamma_g)  
  rgb[2] = gamma(rgb[2], gamma_b)

  return to_uint16(
    sigmoidal(rgb, midpoint, contrast)
  )