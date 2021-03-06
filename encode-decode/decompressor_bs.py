# 
# Compression application using adaptive arithmetic coding
# 
# Usage: python adaptive-arithmetic-compress.py InputFile OutputFile
# Then use the corresponding adaptive-arithmetic-decompress.py application to recreate the original input file.
# Note that the application starts with a flat frequency table of 257 symbols (all set to a frequency of 1),
# and updates it after each byte encoded. The corresponding decompressor program also starts with a flat
# frequency table and updates it after each byte decoded. It is by design that the compressor and
# decompressor have synchronized states, so that the data can be decompressed properly.
# 
# Copyright (c) Project Nayuki
# 
# https://www.nayuki.io/page/reference-arithmetic-coding
# https://github.com/nayuki/Reference-arithmetic-coding
#
from __future__ import print_function 
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import OneHotEncoder
import keras
from keras.layers import *
from keras.models import *
from keras.layers import *
from keras.callbacks import *
from keras.initializers import *
from keras.layers.embeddings import Embedding
from keras.models import load_model
from keras.layers.normalization import BatchNormalization
import tensorflow as tf
import numpy as np
import argparse
import contextlib
import arithmeticcoding_fast
import json
from tqdm import tqdm
import struct
from models import *
from utils import *
import tempfile
import shutil
import sys

# 1. Set the `PYTHONHASHSEED` environment variable at a fixed value
import os
os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
os.environ['PYTHONHASHSEED']=str(0)

# 2. Set the `python` built-in pseudo-random generator at a fixed value
import random
random.seed(0)

np.random.seed(0)
tf.set_random_seed(0)

parser = argparse.ArgumentParser(description='Input')
parser.add_argument('-model', action='store', dest='model_weights_file',
					help='model file')
parser.add_argument('-model_name', action='store', dest='model_name',
					help='model file')
parser.add_argument('-batch_size', action='store', dest='batch_size', type=int,
					help='model file')
parser.add_argument('-input', action='store', dest='file_prefix',
					help='compressed file')
parser.add_argument('-output', action='store',dest='output_file',
					help='decompressed_file')
parser.add_argument('-gpu', action='store', dest='gpu_id', default="",
					help='params file')
parser.add_argument('-data_params', action='store', dest='params_file',
                                        help='params file')
args = parser.parse_args()

os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_id

from keras import backend as K
session_conf = tf.ConfigProto(intra_op_parallelism_threads=1, inter_op_parallelism_threads=1)
sess = tf.Session(graph=tf.get_default_graph(), config=session_conf)
K.set_session(sess)

def iterate_minibatches(inputs, targets, batchsize, shuffle=False):
	assert inputs.shape[0] == targets.shape[0]
	if shuffle:
		indices = np.arange(inputs.shape[0])
		np.random.shuffle(indices)
	for start_idx in range(0, inputs.shape[0] - batchsize + 1, batchsize):
		# if(start_idx + batchsize >= inputs.shape[0]):
		#   break;

		if shuffle:
			excerpt = indices[start_idx:start_idx + batchsize]
		else:
			excerpt = slice(start_idx, start_idx + batchsize)
		yield inputs[excerpt], targets[excerpt]

def predict_lstm(length, timesteps, bs, alphabet_size, model_name):
	ARNN, PRNN = eval(model_name)(bs, timesteps, alphabet_size)
	PRNN.load_weights(args.model_weights_file)

	series = np.zeros((length), dtype=np.int64)
	data = strided_app(series, timesteps+1, 1)
	X = data[:, :-1]
	y_original = data[:, -1:]
	l = int(len(X)/bs)*bs


	f = open(args.file_prefix + ".dzip", 'rb')
	bitin = arithmeticcoding_fast.BitInputStream(f)
	dec = arithmeticcoding_fast.ArithmeticDecoder(32, bitin)
	prob = np.ones(alphabet_size)/alphabet_size
	cumul = np.zeros(alphabet_size+1, dtype = np.uint64)
	cumul[1:] = np.cumsum(prob*10000000 + 1)
	for j in range(timesteps):
		series[j] = dec.read(cumul, alphabet_size)

	cumul = np.zeros((1, alphabet_size+1), dtype = np.int64)
	index = timesteps
	for bx, by in iterate_minibatches(X[:l], y_original[:l], 1):
		prob = PRNN.predict(bx, batch_size=1)
		cumul[:,1:] = np.cumsum(prob*10000000 + 1, axis = 1)
		series[index] = dec.read(cumul[0, :], alphabet_size)
		symbols_read = index-timesteps + 1
		index = index+1
		sys.stdout.flush()
		print("{}/{}".format(index, length), end="\r")

	
	
	if len(X[l:]) > 0:
		for bx, by in iterate_minibatches(X[l:], y_original[l:], 1):
			prob = PRNN.predict(bx, batch_size=1)
			cumul = np.zeros((1, alphabet_size+1), dtype = np.uint64)
			cumul[:,1:] = np.cumsum(prob*10000000 + 1, axis = 1)
			series[index] = dec.read(cumul[0, :], alphabet_size)
			index = index+1
			sys.stdout.flush()
			print("{}/{}".format(index, length), end="\r")
	np.save('test', series)
	bitin.close()
	f.close()
	return series

def main():
	with open(args.params_file, 'r') as f:
		param_dict = json.load(f)
	
	len_series = param_dict['len_series']
	batch_size = param_dict['bs']
	timesteps = param_dict['timesteps']
	id2char_dict = param_dict['id2char_dict'] 
	n_classes = len(id2char_dict)
	print(n_classes, len_series)
	
	series = np.zeros(len_series,dtype=np.uint8)
	series = predict_lstm(len_series, timesteps, batch_size, n_classes, args.model_name)

	f = open(args.output_file,'w')
	f.write(''.join([id2char_dict[str(s)] for s in series]))
	f.close()
	print("Decompressed file saved to {}".format(args.output_file))


if __name__ == "__main__":
		main()

