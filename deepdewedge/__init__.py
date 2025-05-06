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
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

import pwem
import os
from pyworkflow.utils import Environ
from deepdewedge.constants import DEEPDEWEDGE_ENV_ACTIVATION, DEFAULT_ACTIVATION_CMD, DEEPDEWEDGE_ENV_NAME, \
    DEEPDEWEDGE_DEFAULT_VERSION, DEEPDEWEDGE_HOME, DEEPDEWEDGE_CUDA_LIB, DEEPDEWEDGE

_logo = "icon.png"
_references = ['Wiedemann2024']
__version__ = "1.0.0"


class Plugin(pwem.Plugin):
    _homeVar = DEEPDEWEDGE_HOME
    _url = 'https://github.com/scipion-em/scipion-em-deepdewedge'

    @classmethod
    def _defineVariables(cls):
        # DEEPDEWEDGE does NOT need EmVar because it uses a conda environment.
        cls._defineVar(DEEPDEWEDGE_ENV_ACTIVATION, DEFAULT_ACTIVATION_CMD)
        cls._defineVar(DEEPDEWEDGE_CUDA_LIB, pwem.Config.CUDA_LIB)

    @classmethod
    def getDeepdewedgeEnvActivation(cls):
        return cls.getVar(DEEPDEWEDGE_ENV_ACTIVATION)

    @classmethod
    def getEnviron(cls, gpuId='0'):
        """ Setup the environment variables needed to launch deepdewedge. """
        environ = Environ(os.environ)
        if 'PYTHONPATH' in environ:
            # this is required for python virtual env to work
            del environ['PYTHONPATH']

        environ.update({'CUDA_VISIBLE_DEVICES': gpuId})

        cudaLib = environ.get(DEEPDEWEDGE_CUDA_LIB, pwem.Config.CUDA_LIB)
        environ.addLibrary(cudaLib)
        return environ

    @classmethod
    def defineBinaries(cls, env):
        DEEPDEWEDGE_INSTALLED = '%s_%s_installed' % (DEEPDEWEDGE, DEEPDEWEDGE_DEFAULT_VERSION)
        installationCmd = cls.getCondaActivationCmd()
        # try to get CONDA activation command
        # Create the environment
        installationCmd += ' git clone https://github.com/MLI-lab/DeepDeWedge && '
        installationCmd += 'conda create -y -n %s python=3.10.13 pip=23.2.1 -c conda-forge && ' % DEEPDEWEDGE_ENV_NAME

        # Activate new the environment
        installationCmd += 'conda activate %s && ' % DEEPDEWEDGE_ENV_NAME

        # Install the rest of dependencies
        installationCmd += 'conda install pytorch==2.2.0 pytorch-cuda=11.8 -c pytorch -c nvidia && '
        installationCmd += 'cd /home/vilas/software/software/em/deepdewedge-0.3.0/DeepDeWedge && '
        installationCmd += 'pip install -r requirements.txt && '

        # Install deepdewedge
        installationCmd += 'pip install . && '

        # Flag installation finished
        installationCmd += 'touch %s' % DEEPDEWEDGE_INSTALLED

        deepdewedge_commands = [(installationCmd, DEEPDEWEDGE_INSTALLED)]

        envPath = os.environ.get('PATH', "")  # keep path since conda likely in there
        installEnvVars = {'PATH': envPath} if envPath else None

        env.addPackage(DEEPDEWEDGE,
                       version=DEEPDEWEDGE_DEFAULT_VERSION,
                       tar='void.tgz',
                       commands=deepdewedge_commands,
                       neededProgs=cls.getDependencies(),
                       vars=installEnvVars,
                       default=bool(cls.getCondaActivationCmd()))

    @classmethod
    def getDependencies(cls):
        # try to get CONDA activation command
        condaActivationCmd = cls.getCondaActivationCmd()
        neededProgs = []
        if not condaActivationCmd:
            neededProgs.append('conda')

        return neededProgs

    @classmethod
    def runDeepdewedge(cls, protocol, program, args, cwd=None, gpuId='0'):
        """ Run Deepdewedge command from a given protocol. """
        fullProgram = '%s %s && %s' % (cls.getCondaActivationCmd(),
                                       cls.getDeepdewedgeEnvActivation(),
                                       program)
        protocol.runJob(fullProgram, args, env=cls.getEnviron(gpuId=gpuId), cwd=cwd, numberOfMpi=1)
