import numpy as np
import keras
from keras.models import Sequential, Model
from keras.layers import Dense, Bidirectional, Input, add, concatenate, Lambda, TimeDistributed
from keras.layers import LSTM, Flatten, Conv1D, LocallyConnected1D, CuDNNLSTM, CuDNNGRU, MaxPooling1D, GlobalAveragePooling1D, GlobalMaxPooling1D
from keras.models import *
from keras.layers import *
from keras.callbacks import *
from keras.initializers import *
from keras.layers.embeddings import Embedding
from keras.callbacks import ModelCheckpoint
from sklearn.preprocessing import OneHotEncoder
from keras.layers.normalization import BatchNormalization
from keras.layers.advanced_activations import ELU
import tensorflow as tf
import argparse
from keras.callbacks import CSVLogger
from keras import backend as K

np.random.seed(0)
tf.set_random_seed(0)


def res_block(inp, units=512, activation='relu'):
    x = res = inp

    # x = BatchNormalization()(res)
    x = Activation(activation)(x)
    x = Dense(units)(x)

    # x = BatchNormalization()(x)
    x = Activation(activation)(x)
    x = Dense(units)(x)

    out = add([x, res])

    return out


def biGRU_big(bs,time_steps,alphabet_size):

  jump = 16
  def my_shape(input_shape):
     return tuple((input_shape[0],int(np.ceil(float(input_shape[1])/jump)),input_shape[2]))

  def slice_shape(input_shape):
     
     return tuple((input_shape[0],20))

  if alphabet_size >= 1 and alphabet_size <=3:
      inputs_bits = Input(shape=(time_steps,))
      x = Embedding(alphabet_size, 8,)(inputs_bits)
      x = Bidirectional(GRU(8, stateful=False, return_sequences=True, reset_after=True))(x)
      x = Bidirectional(GRU(8, stateful=False, return_sequences=True, reset_after=True))(x)
      x = Lambda(lambda tensor: tensor[:,::-jump,:][:,::-1,:], output_shape=my_shape)(x)
      flat = Flatten()(x)
      prelogits = x = Dense(16, activation='relu')(flat)
      x = Add()([Dense(alphabet_size)(x),  Dense(alphabet_size)(flat)])
      new_logits = Add()([Dense(alphabet_size)(prelogits),  Dense(alphabet_size)(flat)]) 
      s1 = Activation('softmax', name="1")(x)

      model_prev = Model(inputs_bits, s1)
      d = emb = Embedding(alphabet_size, 16)(inputs_bits)
      # d = Bidirectional(GRU(128, stateful=False, return_sequences=True))(emb)
      # d = Bidirectional(GRU(64, stateful=False, return_sequences=True))(d)
      d = Flatten()(d)
      flat2 = d = Concatenate()([d, flat])
      d = Dense(1024, activation='relu')(flat2)
      # d = Dense(1024, activation='relu')(d)
      d = res_block(d, 1024, 'relu')
      d = res_block(d, 1024, 'relu')
      
      e = Dense(1024, activation='relu')(flat2)
      e = Dense(1024, activation='relu')(e)

      next_layer = Concatenate()([Dense(alphabet_size)(flat2), Dense(alphabet_size)(d), Dense(alphabet_size)(e), new_logits])
      next_layer = Dense(alphabet_size)(next_layer)
      s1 = Activation('softmax', name="1")(next_layer)
      # s2 = Activation('softmax', name="2")(Add()([Dense(alphabet_size)(flat2), Dense(alphabet_size)(d)]))
      # s3 = Activation('softmax', name="3")(logits)

      model = Model(inputs_bits, s1)

      return model, model_prev

  if alphabet_size >= 4 and alphabet_size <=8:
      inputs_bits = Input(shape=(time_steps,))
      x = emb = Embedding(alphabet_size, 8,)(inputs_bits)
      x = Bidirectional(GRU(32, stateful=False, return_sequences=True, reset_after=True))(x)
      x = Bidirectional(GRU(32, stateful=False, return_sequences=True, reset_after=True))(x)
      x = Lambda(lambda tensor: tensor[:,jump-1::jump,:], output_shape=my_shape)(x)
      flat = Flatten()(x)
      prelogits = x = Dense(16, activation='relu')(flat)
      x = Add(name='logits')([Dense(alphabet_size)(x),  Dense(alphabet_size)(flat)])
      new_logits = Add(name='logits-new')([Dense(alphabet_size)(prelogits),  Dense(alphabet_size)(flat)])
      s1 = Activation('softmax', name="1")(x)

      model_prev = Model(inputs_bits, s1)
      d = emb = Embedding(alphabet_size, 16)(inputs_bits)
      # d = Bidirectional(GRU(128, stateful=False, return_sequences=True))(emb)
      # d = Bidirectional(GRU(64, stateful=False, return_sequences=True))(d)
      d = Flatten()(d)
      flat2 = d = Concatenate()([d, flat])
      d = Dense(1024, activation='relu')(flat2)
      # d = Dense(1024, activation='relu')(d)
      d = res_block(d, 1024, 'relu')
      d = res_block(d, 1024, 'relu')
      
      e = Dense(1024, activation='relu')(flat2)
      e = Dense(1024, activation='relu')(e)

      next_layer = Concatenate()([Dense(alphabet_size)(flat2), Dense(alphabet_size)(d), Dense(alphabet_size)(e), new_logits])
      next_layer = Dense(alphabet_size)(next_layer)
      s1 = Activation('softmax', name="1")(next_layer)
      # s2 = Activation('softmax', name="2")(Add()([Dense(alphabet_size)(flat2), Dense(alphabet_size)(d)]))
      # s3 = Activation('softmax', name="3")(logits)

      model = Model(inputs_bits, s1)

      return model, model_prev

  if alphabet_size >= 10 and alphabet_size < 128:
      inputs_bits = Input(shape=(time_steps,))
      x = Embedding(alphabet_size, 16,)(inputs_bits)
      x = Bidirectional(GRU(128, stateful=False, return_sequences=True, reset_after=True))(x)
      x = Bidirectional(GRU(128, stateful=False, return_sequences=True, reset_after=True))(x)
      x = Lambda(lambda tensor: tensor[:,::-jump,:][:,::-1,:], output_shape=my_shape)(x)
      flat = Flatten()(x)
      prelogits = x = Dense(128, activation='relu')(flat)
      x = Add()([Dense(alphabet_size)(x),  Dense(alphabet_size)(flat)])
      new_logits = Add()([Dense(alphabet_size)(prelogits),  Dense(alphabet_size)(flat)])
      s1 = Activation('softmax', name="1")(x)

      model_prev = Model(inputs_bits, s1)
      d = emb = Embedding(alphabet_size, 32)(inputs_bits)
      # d = Bidirectional(GRU(256, stateful=False, return_sequences=True))(emb)
      # d = Bidirectional(GRU(128, stateful=False, return_sequences=True))(d)
      d = Flatten()(d)
      flat2 = d = Concatenate()([d, flat])
      
      d = Dense(2048, activation='relu')(flat2)
      d = res_block(d, 2048, 'relu')
      d = res_block(d, 2048, 'relu')
  
      e = Dense(2048, activation='relu')(flat2)
      e = Dense(2048, activation='relu')(e)
 
      next_layer = Concatenate()([Dense(alphabet_size)(flat2), Dense(alphabet_size)(d), Dense(alphabet_size)(e), new_logits]) 
      
      next_layer = Dense(alphabet_size)(next_layer)
      s1 = Activation('softmax', name="1")(next_layer)
      # s2 = Activation('softmax', name="2")(Add()([Dense(alphabet_size)(flat2), Dense(alphabet_size)(d)]))

      model = Model(inputs_bits, s1)

      return model, model_prev

  if alphabet_size >= 128:
      inputs_bits = Input(shape=(time_steps,))
      x = Embedding(alphabet_size, 16,)(inputs_bits)
      x = Bidirectional(GRU(128, stateful=False, return_sequences=True, reset_after=True))(x)
      x = Bidirectional(GRU(128, stateful=False, return_sequences=True, reset_after=True))(x)
      x = Lambda(lambda tensor: tensor[:,::-jump,:][:,::-1,:], output_shape=my_shape)(x)
      flat = Flatten()(x)
      prelogits = x = Dense(256, activation='relu')(flat)
      x = Add()([Dense(alphabet_size)(x),  Dense(alphabet_size)(flat)])
      new_logits = Add()([Dense(alphabet_size)(prelogits),  Dense(alphabet_size)(flat)])
      s1 = Activation('softmax', name="1")(x)

      model_prev = Model(inputs_bits, s1)
      d = emb = Embedding(alphabet_size, 32)(inputs_bits)
      # d = Bidirectional(GRU(256, stateful=False, return_sequences=True))(emb)
      # d = Bidirectional(GRU(128, stateful=False, return_sequences=True))(d)
      d = Flatten()(d)
      flat2 = d = Concatenate()([d, flat])

      d = Dense(2048, activation='relu')(flat2)
      d = res_block(d, 2048, 'relu')
      d = res_block(d, 2048, 'relu')

      e = Dense(2048, activation='relu')(flat2)
      e = Dense(2048, activation='relu')(e)

      next_layer = Concatenate()([Dense(alphabet_size)(flat2), Dense(alphabet_size)(d), Dense(alphabet_size)(e), new_logits])

      next_layer = Dense(alphabet_size)(next_layer)
      s1 = Activation('softmax', name="1")(next_layer)
      # s2 = Activation('softmax', name="2")(Add()([Dense(alphabet_size)(flat2), Dense(alphabet_size)(d)]))

      model = Model(inputs_bits, s1)

      return model, model_prev


def biGRU_jump(bs,time_steps,alphabet_size):
  jump = 16
  def my_shape(input_shape):
     return tuple((input_shape[0],int(np.ceil(float(input_shape[1])/jump)),input_shape[2]))

  if alphabet_size >= 1 and alphabet_size <=3:
      inputs_bits = Input(shape=(time_steps,))
      x = Embedding(alphabet_size, 8,)(inputs_bits)
      x = Bidirectional(CuDNNGRU(8, stateful=False, return_sequences=True))(x)
      x = Bidirectional(CuDNNGRU(8, stateful=False, return_sequences=True))(x)
      x = Lambda(lambda tensor: tensor[:,::-jump,:][:,::-1,:], output_shape=my_shape)(x)
      flat = Flatten()(x)
      prelogits = x = Dense(16, activation='relu')(flat)
      x = Add()([Dense(alphabet_size)(x),  Dense(alphabet_size)(flat)])
      s1 = Activation('softmax', name="1")(x)

      return Model(inputs_bits, s1) 
  
  if alphabet_size >= 4 and alphabet_size <=8:
      inputs_bits = Input(shape=(time_steps,))
      x = Embedding(alphabet_size, 8,)(inputs_bits)
      x = Bidirectional(CuDNNGRU(32, stateful=False, return_sequences=True))(x)
      x = Bidirectional(CuDNNGRU(32, stateful=False, return_sequences=True))(x)
      x = Lambda(lambda tensor: tensor[:,::-jump,:][:,::-1,:], output_shape=my_shape)(x)
      flat = Flatten()(x)
      prelogits = x = Dense(16, activation='relu')(flat)
      x = Add()([Dense(alphabet_size)(x),  Dense(alphabet_size)(flat)])
      s1 = Activation('softmax', name="1")(x)

      return Model(inputs_bits, s1)

  if alphabet_size >= 10 and alphabet_size < 128:
      inputs_bits = Input(shape=(time_steps,))
      x = Embedding(alphabet_size, 16,)(inputs_bits)
      x = Bidirectional(CuDNNGRU(128, stateful=False, return_sequences=True))(x)
      x = Bidirectional(CuDNNGRU(128, stateful=False, return_sequences=True))(x)
      x = Lambda(lambda tensor: tensor[:,::-jump,:][:,::-1,:], output_shape=my_shape)(x)
      flat = Flatten()(x)
      prelogits = x = Dense(128, activation='relu')(flat)
      x = Add()([Dense(alphabet_size)(x),  Dense(alphabet_size)(flat)])
      s1 = Activation('softmax', name="1")(x)

      return Model(inputs_bits, s1)

  if alphabet_size >= 128:
      inputs_bits = Input(shape=(time_steps,))
      x = Embedding(alphabet_size, 16,)(inputs_bits)
      x = Bidirectional(CuDNNGRU(128, stateful=False, return_sequences=True))(x)
      x = Bidirectional(CuDNNGRU(128, stateful=False, return_sequences=True))(x)
      x = Lambda(lambda tensor: tensor[:,::-jump,:][:,::-1,:], output_shape=my_shape)(x)
      flat = Flatten()(x)
      prelogits = x = Dense(256, activation='relu')(flat)
      x = Add()([Dense(alphabet_size)(x),  Dense(alphabet_size)(flat)])
      s1 = Activation('softmax', name="1")(x)

      return Model(inputs_bits, s1)

def biGRU(bs,time_steps,alphabet_size):
  inputs_bits = Input(shape=(time_steps,))
  x   = Embedding(alphabet_size, 8,)(inputs_bits)
  x = Bidirectional(CuDNNGRU(8, stateful=False, return_sequences=True))(x)
  # x = TimeDistributed(Dense(8, activation='relu'))(x)
  x = Bidirectional(CuDNNGRU(8, stateful=False, return_sequences=False))(x)
  # x = TimeDistributed(Dense(8, activation='relu'))(x)
  # x = Lambda(lambda tensor: tensor[:,::-jump,:][:,::-1,:], output_shape=my_shape)(x)
  # x = Bidirectional(CuDNNGRU(8, stateful=False, return_sequences=True))(x)
  x = Dense(8, activation='relu')(x)
  x = Dense(alphabet_size)(x)

  s1 = Activation('softmax', name="1")(x)

  model = Model(inputs_bits, s1)

  return model

def FC(bs,time_steps,alphabet_size):
  inputs_bits = Input(shape=(time_steps,))
  x  = Embedding(alphabet_size, 8,)(inputs_bits)
  flat = Flatten()(x)
  x = Dense(128, activation='relu')(flat)
  x = Dense(128, activation='relu')(x)
  x = Dense(alphabet_size)(x)

  s1 = Activation('softmax', name="1")(x)

  model = Model(inputs_bits, s1)

  return model

