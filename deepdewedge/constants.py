# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:     you (you@yourinstitution.email)
# *
# * your institution
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'you@yourinstitution.email'
# *
# **************************************************************************

DEEPDEWEDGE_HOME = 'DEEPDEWEDGE_HOME'
V0_2_2 = '0.2.2'
V0_3_0 = '0.3.0'
DEEPDEWEDGE_DEFAULT_VERSION = V0_3_0
DEEPDEWEDGE = 'deepdewedge'
DEEPDEWEDGE_ENV_NAME = '%s-%s' % (DEEPDEWEDGE, DEEPDEWEDGE_DEFAULT_VERSION)
DEEPDEWEDGE_ENV_ACTIVATION = 'DEEPDEWEDGE_ENV_ACTIVATION'
DEFAULT_ACTIVATION_CMD = 'conda activate %s' % DEEPDEWEDGE_ENV_NAME
DEEPDEWEDGE_CUDA_LIB = 'DEEPDEWEDGE_CUDA_LIB'

TRAIN_DATA_DIR = 'train_data'
TRAIN_DATA_FN = 'train_data.npz'
VALIDATION_DATA_FN = 'val_data.npz'
MEAN_STD_FN = 'mean_std.npz'
TRAIN_DATA_CONFIG = 'training_data_config'
DEEPDEWEDGE_MODEL = 'deepdewedge_model'
DEEPDEWEDGE_MODEL_TGZ = DEEPDEWEDGE_MODEL + '.tar.gz'
PREDICT_CONFIG = 'predict_config'
