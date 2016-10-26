#This encoder is random noise

import tensorflow as tf
from lib.util.ops import *
from lib.util.globals import *

def sample(config):
  z_dim = config['z_dim']
  encoded_z = tf.random_uniform([config['batch_size'], z_dim],-1, 1,dtype=config['dtype'])
  z_mu = None
  z_sigma = None
  z = tf.random_uniform([config['batch_size'], z_dim],-1, 1,dtype=config['dtype'])
  return z, encoded_z, None, None


