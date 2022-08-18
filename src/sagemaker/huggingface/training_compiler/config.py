# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
"""Configuration for the SageMaker Training Compiler."""
from __future__ import absolute_import
import logging
from packaging.specifiers import SpecifierSet
from packaging.version import Version
from typing import Union

from sagemaker.training_compiler.config import TrainingCompilerConfig as BaseConfig
from sagemaker.workflow.entities import PipelineVariable

logger = logging.getLogger(__name__)


class TrainingCompilerConfig(BaseConfig):
    """The SageMaker Training Compiler configuration class."""

    SUPPORTED_INSTANCE_CLASS_PREFIXES = ["p3", "g4dn", "p4d", "g5"]

    def __init__(
        self,
        enabled: Union[bool, PipelineVariable] = True,
        debug: Union[bool, PipelineVariable] = False,
    ):
        """This class initializes a ``TrainingCompilerConfig`` instance.

        `Amazon SageMaker Training Compiler
        <https://docs.aws.amazon.com/sagemaker/latest/dg/training-compiler.html>`_
        is a feature of SageMaker Training
        and speeds up training jobs by optimizing model execution graphs.

        You can compile Hugging Face models
        by passing the object of this configuration class to the ``compiler_config``
        parameter of the :class:`~sagemaker.huggingface.HuggingFace`
        estimator.

        Args:
            enabled (bool): Optional. Switch to enable SageMaker Training Compiler.
                The default is ``True``.
            debug (bool): Optional. Whether to dump detailed logs for debugging.
                This comes with a potential performance slowdown.
                The default is ``False``.

        **Example**: The following code shows the basic usage of the
        :class:`sagemaker.huggingface.TrainingCompilerConfig()` class
        to run a HuggingFace training job with the compiler.

        .. code-block:: python

            from sagemaker.huggingface import HuggingFace, TrainingCompilerConfig

            huggingface_estimator=HuggingFace(
                ...
                compiler_config=TrainingCompilerConfig()
            )

        .. seealso::

            For more information about how to enable SageMaker Training Compiler
            for various training settings such as using TensorFlow-based models,
            PyTorch-based models, and distributed training,
            see `Enable SageMaker Training Compiler
            <https://docs.aws.amazon.com/sagemaker/latest/dg/training-compiler-enable.html>`_
            in the `Amazon SageMaker Training Compiler developer guide
            <https://docs.aws.amazon.com/sagemaker/latest/dg/training-compiler.html>`_.

        """

        super(TrainingCompilerConfig, self).__init__(enabled=enabled, debug=debug)

    @classmethod
    def validate(
        cls,
        estimator,
    ):
        """Checks if SageMaker Training Compiler is configured correctly.

        Args:
            estimator (:class:`sagemaker.huggingface.HuggingFace`): An estimator object.
                If SageMaker Training Compiler is enabled, it will validate whether
                the estimator is configured to be compatible with Training Compiler.

        Raises:
            ValueError: Raised if the requested configuration is not compatible
                        with SageMaker Training Compiler.
        """

        super(TrainingCompilerConfig, cls).validate(estimator)

        if estimator.image_uri:
            error_helper_string = (
                "Overriding the image URI is currently not supported "
                "for SageMaker Training Compiler."
                "Specify the following parameters to run the Hugging Face training job "
                "with SageMaker Training Compiler enabled: "
                "transformer_version, tensorflow_version or pytorch_version, and compiler_config."
            )
            raise ValueError(error_helper_string)

        if estimator.distribution:
            pt_xla_present = "pytorch_xla" in estimator.distribution
            pt_xla_enabled = estimator.distribution.get("pytorch_xla", {}).get("enabled", False)
            if pt_xla_enabled:
                if estimator.tensorflow_version:
                    error_helper_string = (
                        "Distribution mechanism 'pytorch_xla' is currently only supported for "
                        "PyTorch >= 1.11 when Training Compiler is enabled. Received "
                        "tensorflow_version={} which is unsupported."
                    )
                    raise ValueError(error_helper_string.format(estimator.tensorflow_version))
                elif estimator.pytorch_version:
                    if Version(estimator.pytorch_version) in SpecifierSet("< 1.11"):
                        error_helper_string = (
                            "Distribution mechanism 'pytorch_xla' is currently only supported for "
                            "PyTorch >= 1.11 when Training Compiler is enabled. Received "
                            "pytorch_version={} which is unsupported."
                        )
                        raise ValueError(error_helper_string.format(estimator.pytorch_version))
            if not pt_xla_present:
                if estimator.pytorch_version:
                    if Version(estimator.pytorch_version) in SpecifierSet(">= 1.11"):
                        error_helper_string = (
                            "'pytorch_xla' is the only distribution mechanism currently supported "
                            "for PyTorch >= 1.11 when Training Compiler is enabled. Received "
                            "distribution={} which is unsupported."
                        )
                        raise ValueError(error_helper_string.format(estimator.distribution))
        elif estimator.instance_count and estimator.instance_count > 1:
            if estimator.pytorch_version:
                if Version(estimator.pytorch_version) in SpecifierSet(">= 1.11"):
                    logger.warning(
                        "Consider setting 'distribution' to 'pytorch_xla' for distributed "
                        "training with PyTorch >= 1.11 with Training Compiler enabled. This "
                        "will become the default configuration in the future."
                    )
