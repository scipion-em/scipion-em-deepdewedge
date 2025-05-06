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

from pyworkflow.constants import BETA
from pyworkflow.protocol import params
from pyworkflow.utils import Message
from pyworkflow.object import Integer

from pwem.protocols import EMProtocol

from deepdewedge import Plugin

PROGRAM_PREPARE_STAR = 'prepare_data'
PROGRAM_FIT_MODEL = 'fit-model'
PROGRAM_REFINE_MODEL = 'refine-tomogram'

class DeepDeWedgeDenoising(EMProtocol):
    """
    This protocol will print hello world in the console
    IMPORTANT: Classes names should be unique, better prefix them
    """
    _label = 'deepDeWedge denoising'
    _devStatus = BETA
    tomoList = []

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('oddEvenImported', params.BooleanParam,
                      default=False,
                      label="Are odd-even associated to the Tomograms?")

        form.addParam('inputTomograms', params.PointerParam,
                      condition='oddEvenImported == False',
                      label="Are odd-even associated to the Tomograms?")

        form.addParam('evenTomos', params.PointerParam,
                      pointerClass='SetOfTomograms',
                      condition='not areEvenOddLinked',
                      label='Even tomograms',
                      allowsNull=True,
                      important=True,
                      help='Set of tomograms reconstructed from the even frames of the tilt'
                           'series movies.')
        form.addParam('oddTomos', params.PointerParam,
                      pointerClass='SetOfTomograms',
                      condition='not areEvenOddLinked',
                      label='Odd tomograms',
                      allowsNull=True,
                      important=True,
                      help='Set of tomogram reconstructed from the odd frames of the tilt'
                           'series movies.')

        form.addParam('inputTomoMasks', params.PointerParam, pointerClass='SetOfTomoMasks',
                      allowsNull=True,
                      label="Mask (Optional)",
                      help='List of binary masks that outline the region of interest in the '
                           'tomograms to guide subtomogram extraction. The DeepDeWedge reconstruction'
                           ' of areas outside the mask may be less accurate. If no masks are provided, '
                           'the entire tomogram is used for subtomogram extraction')

        form.addParam('boxsize', params.IntParam,
                      label='Subtomo Size',
                      allowsNull=True,
                      help='Size of the cubic subtomograms to extract for model fitting. This value must'
                           ' be divisible by 2^{num_downsample_layers}, where {num_downsample_layers} '
                           'is the number of downsampling layers used in the U-Net')

        form.addParam('validationFraction', params.FloatParam,
                      label='Validation fraction',
                      default = 0.1,
                      important=True,
                      help='Fraction of subtomograms to use for validation. Increasing this '
                           'fraction will decrease the number of subtomograms used for model fitting' )

        #TODO: Only if mask are provided
        form.addParam('minNonZeroMaskSubtomo', params.FloatParam,
                      label='Validation fraction',
                      default = 0.3,
                      help='Minimum fraction of voxels in a subtomogram that correspond to '
                           'nonzero voxels in the mask. If mask_files are provided, this '
                           'parameter has to be provided as well. If no mask_files are '
                           'provided, this parameter is ignored')

        line = form.addLine('Subtomo Extraction strides',
                             help="List of 3 integers specifying the 3D Strides used for subtomogram extraction."
                                  " If set to None, stride 'subtomo_size' is used in all 3 directions."
                                  " Smaller strides result in more sub-tomograms being extracted.")

        line.addParam('strideX', params.IntParam, allowsNull=True, label='High')
        line.addParam('strideY', params.IntParam, allowsNull=True, label='Low')
        line.addParam('strideZ', params.IntParam, allowsNull=True, label='Step',
                      expertLevel=params.LEVEL_ADVANCED)

        group = form.addGroup('Model Fit')
        group.addParam('epochs', params.IntegerParam,
              label='Number of epochs',
              default = 1,
              important=True,
              help='Number of epochs to fit the model.' )
        group.addParam('batchSize', params.IntegerParam,
              label='Batch size',
              default = 1,
              important=True,
              help='Batch size for the optimizer.' )
        group.addParam('mwAngle', params.FloatParam,
              label='Missing Wedge angle (deg)',
              default = -1,
              help='Width of the missing wedge in degrees.' )
        group.addParam('numworkers', params.IntegerParam,
              label='Number of CPU',
              default = -1,
              help='Number of CPU workers to use for data loading.'
                   'If fitting is slow, try increasing this number')
        group.addParam('distributedBackend', params.BooleanParam,
              label='Fit in Multiple GPU?',
              default = True,
              help='Distributed backend to use when fitting on '
                   'multiple GPUs, e.g, nccl (default) or gloo. '
                   'Ignored if fitting on a single GPU. [default: nccl]')

        group2 = form.addGroup('Refine Tomogram')
        group2.addParam('recomputeNormalization', params.BooleanParam,
              label='Fit in Multiple GPU?',
              default = True,
              help='Whether to recompute the mean and variance used to normalize '
                   'the tomo0s and tomo1s (see Appendix B in the paper). '
                   'If `False`, the mean and variance of model inputs calculated '
                   'during model fitting will be used.'
                   'If `True`, the average model input mean and variance will '
                   'be computed for each tomogram individually. We recommend '
                   'setting this to to `True`. If you apply a model to a tomogram '
                   'that was not used for model fitting or if the means and '
                   'variances of the tomograms during model fitting are considerably '
                   'different, recomputing the normalization is expected to be '
                   'very beneficial for tomogram refinement.')

    # --------------------------- STEPS functions ------------------------------
    def _insertAllSteps(self):
        self.tomoList = self._insertFunctionStep(self.createTomoListStep)

        for tom in self.tomoList:
            self._insertFunctionStep(self.prepareDataForDeepDeWedge, tom)
            self._insertFunctionStep(self.createOutputStep)


    def createTomoListStep(self):
        if self.oddEvenImported.get():
            pass
        else:
            for t in self.inputTomograms.get():
                tsId = t.getTsId()
                odd, even = t.getHalfMaps().split(',')
                self.tomoList.append([tsId, odd, even])

    def prepareDataForDeepDeWedge(self, tomo):
        tsId = tomo[0]
        fnOdd = tomo[1]
        fnEven = tomo[2]
        fnMask = None

        params  = ' --tomo0_files %s ' % fnOdd
        params += ' --tomo1_files %s ' % fnEven
        params += ' --subtomo_size %i ' % self.boxsize.get()
        params += ' --subtomo_extraction_strides %i ' % (a, b, c)
        params += ' --val-fraction %f ' % self.validationFraction.get()

        params += ' --mask_files %s ' % fnMask
        params += ' --min_nonzero_mask_fraction_in_subtomo %f ' % (a, b, c)

        Plugin.runDeepdewedge(self, Plugin.getProgram(PROGRAM_PREPARE_STAR), args=params)

    def fittingModelStep(self, tomo):
        tsId = tomo[0]
        fnOdd = tomo[1]
        fnEven = tomo[2]
        fnMask = None

        params = ' --num-epochs %i ' % self.epochs.get()
        params += ' --subtomo_size %i ' % self.boxsize.get()
        params += ' --batch-size %i ' % self.batchSize.get()
        params += ' --mw-angle %f ' % mwAngle
        params += ' --subtomo-dir %s 'subtomoDir

        #TODO: Add --gpu and --num-workers
        #TODO: Check and add --unet-params-dict
        #TODO: Check and add --adam-params-dict
        Plugin.runDeepdewedge(self, Plugin.getProgram(PROGRAM_FIT_MODEL), args=params)
                                                                                                                                                                                      │

    def refineModelStep(self, tomo):

        params  = ' --tomo0_files %s ' % fnOdd
        params += ' --tomo1_files %s ' % fnEven
        params += ' --model-checkpoint-file % ' fnModel
        params += ' --subtomo_size %i ' % self.boxsize.get()
        params += ' --mw-angle %f ' % mwAngle
        params += ' --subtomo-overlap %f ' % subtomoOverlap
        params += ' --recompute-normalization'
        params += ' --batch-size %i ' % batchSize
        params += ' --output_dir %s ' % outputDrir
        #TODO: Add --num-workers  and --gpu
        Plugin.runDeepdewedge(self, Plugin.getProgram(PROGRAM_REFINE_MODEL), args=params)

    def createOutputStep(self):
        #TODO

    # --------------------------- INFO functions -----------------------------------
    def _validate(self):
        errors = []
        return errors

    def _summary(self):
        """ Summarize what the protocol has done"""
        summary = []
        return summary

    def _methods(self):
        methods = []
        return methods
