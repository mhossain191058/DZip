from __future__ import print_function
import numpy as np
import keras
import os 
os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"]="1"
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from keras.models import *
from keras.layers import *
from keras.callbacks import *
from keras.initializers import *
from math import sqrt
import keras.regularizers as regularizers
from keras.layers.embeddings import Embedding
import tensorflow as tf
import argparse
from keras import backend as K
from utils import *
from models import *
import sys
import pandas as pd

def iterate_minibatches(inputs, targets, batchsize, n_classes, shuffle=False):
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
        yield inputs[excerpt], keras.utils.to_categorical(targets[excerpt], num_classes=n_classes)
        
def fit_model(X, Y, bs, ARNN):
    y = Y
    optim = tf.train.AdamOptimizer(learning_rate=5e-4, beta1=0.)
    ARNN.compile(loss=loss_fn, optimizer=optim, metrics=['acc'])
    
    i = 0
    loss_list = []
    for batch_x, batch_y in iterate_minibatches(X, y, bs, n_classes, shuffle=False):
        i = i+1
        out = ARNN.test_on_batch(batch_x, batch_y)
        loss_list.append(out[0])
        out = ARNN.train_on_batch(batch_x, batch_y)
        # out2 = ARNN.train_on_batch(batch_x, [batch_y, batch_y])
        # out = ARNN.train_on_batch(batch_x, [batch_y, batch_y])
        if i%10==0:
            sys.stdout.flush()
            print('Batch {}/{} Average bits per character (bpc) = {:4f}'.format(i, len(y)//bs, np.mean(loss_list)), end='\r')
            if i%100000==0:
                np.save('ARNN_{}_losslist_{}'.format(FLAGS.file_name, FLAGS.mode), np.array(loss_list))
    print("----------------------------------------------------------------------------------")
    print("Compressing model parameters bith bsc")
    print("----------------------------------------------------------------------------------")
    os.system("./bsc e {}_{} {}_{}.bsc".format(FLAGS.file_name, FLAGS.PRNN, FLAGS.file_name, FLAGS.PRNN))
    print("----------------------------------------------------------------------------------")
    print("\n\n\n")
    print("**********DZip finished*********")
    print("----------------------------------------------------------------------------------")
    model_size = os.stat("{}_{}.bsc".format(FLAGS.file_name, FLAGS.PRNN)).st_size
    bs_results = pd.read_csv("log_{}_{}_bootstrap".format(FLAGS.file_name, FLAGS.PRNN))
    model_bpc = model_size*8.0/len(sequence)
    com_bpc = np.mean(loss_list)
    bs_bpc = bs_results['loss'].iloc[-1]

    print("Model Size {} bytes".format(model_size))
    print("----------------------------------------------------------------------------------")
    print('Combined Model: Average bits per character (bpc) = {:4f} [Bitstream {} bpc + Model {} bpc]'.format(com_bpc+model_bpc, com_bpc, model_bpc))
    print("Logged to Combined_{}_losslist_{}".format(FLAGS.file_name, FLAGS.mode))
    print("----------------------------------------------------------------------------------")
    print('Bootstrap Model: Average bits per character (bpc) = {:4f} [Bitstream {} bpc + Model {} bpc]'.format(bs_bpc+model_bpc, bs_bpc, model_bpc))
    print("Logged to log_{}_{}_bootstrap".format(FLAGS.file_name, FLAGS.PRNN))
    print("----------------------------------------------------------------------------------")
    np.save('Combined_{}_losslist_{}'.format(FLAGS.file_name, FLAGS.mode), np.array(loss_list))


batch_size=128
sequence_length=64

def get_argument_parser():
    parser = argparse.ArgumentParser();
    parser.add_argument('--file_name', type=str, default='xor10',
                        help='The name of the input file')
    parser.add_argument('--ARNN', type=str, default='biGRU_big',
                        help='Name for the ARNN architecture')
    parser.add_argument('--PRNN', type=str, default='biGRU_jump',
                        help='Name for the PRNN architecture')
    parser.add_argument('--gpu', type=str, default='1',
                        help='Name for the log file')
    parser.add_argument('--mode', type=str, default='sa',
                        help='Mode: sa -> semi adaptive uses pretrained NN as prior \n or a -> trains from scratch')
    return parser

parser = get_argument_parser()
FLAGS = parser.parse_args()
os.environ["CUDA_VISIBLE_DEVICES"]=FLAGS.gpu

semiadaptive = FLAGS.mode == 'sa'

sequence = np.load(FLAGS.file_name + ".npy")
n_classes = len(np.unique(sequence))
sequence = sequence

X, Y = generate_single_output_data(sequence, batch_size, sequence_length)

ARNN, PRNN = eval(FLAGS.ARNN)(batch_size, sequence_length, n_classes)

optim = keras.optimizers.Adam(lr=1e-3, beta_1=0.9, beta_2=0.999, decay=0.0, amsgrad=False)
PRNN.compile(loss=loss_fn, optimizer=optim, metrics=['acc'])
if semiadaptive:
    print("Loading Weights")
    PRNN.load_weights("{}_{}".format(FLAGS.file_name, FLAGS.PRNN))

    for l in PRNN.layers:
        l.trainable = False

# ARNN.summary()

fit_model(X, Y, batch_size, ARNN)
