# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class PyOnnxruntime(CMakePackage, PythonExtension):
    """ONNX Runtime is a performance-focused complete scoring
    engine for Open Neural Network Exchange (ONNX) models, with
    an open extensible architecture to continually address the
    latest developments in AI and Deep Learning. ONNX Runtime
    stays up to date with the ONNX standard with complete
    implementation of all ONNX operators, and supports all
    ONNX releases (1.2+) with both future and backwards
    compatibility."""

    homepage = "https://github.com/microsoft/onnxruntime"
    git = "https://github.com/microsoft/onnxruntime.git"
    submodules = True

    license("MIT")

    version("1.17.1", tag="v1.17.1", commit="8f5c79cb63f09ef1302e85081093a3fe4da1bc7d")
    version("1.10.0", tag="v1.10.0", commit="0d9030e79888d1d5828730b254fedc53c7b640c1")
    version("1.7.2", tag="v1.7.2", commit="5bc92dff16b0ddd5063b717fb8522ca2ad023cb0")

    depends_on("c", type="build")  # generated
    depends_on("cxx", type="build")  # generated

    variant("cuda", default=False, description="Build with CUDA support")

    # cmake/CMakeLists.txt
    depends_on("cmake@3.26:", when="@1.17:", type="build")
    depends_on("cmake@3.1:", type="build")
    # Needs absl/strings/has_absl_stringify.h
    # cxxstd=20 may also work, but cxxstd=14 does not
    depends_on("abseil-cpp@20240116.0: cxxstd=17", when="@1.17:")

    extends("python")
    depends_on("python", type=("build", "run"))
    depends_on("py-pip", type="build")
    depends_on("py-wheel", type="build")
    depends_on("py-setuptools", type="build")
    depends_on("py-pybind11", type="build")

    # requirements.txt
    depends_on("py-coloredlogs", when="@1.17:", type=("build", "run"))
    depends_on("py-flatbuffers", type=("build", "run"))
    depends_on("py-numpy@1.16.6:", type=("build", "run"))
    depends_on("py-packaging", type=("build", "run"))
    depends_on("py-protobuf", type=("build", "run"))
    depends_on("py-sympy@1.1:", type=("build", "run"))

    depends_on("protobuf")
    # https://github.com/microsoft/onnxruntime/pull/11639
    depends_on("protobuf@:3.19", when="@:1.11")
    depends_on("py-cerberus", type=("build", "run"))
    depends_on("py-onnx", type=("build", "run"))
    depends_on("py-onnx@:1.15.0", type=("build", "run"), when="@:1.17.1")
    depends_on("zlib-api")
    depends_on("libpng")
    depends_on("cuda", when="+cuda")
    depends_on("cudnn", when="+cuda")
    depends_on("iconv", type=("build", "link", "run"))
    depends_on("re2+shared")

    # Adopted from CMS experiment's fork of onnxruntime
    # https://github.com/cms-externals/onnxruntime/compare/5bc92df...d594f80
    patch("cms.patch", level=1, when="@1.7.2")
    # https://github.com/cms-externals/onnxruntime/compare/0d9030e...7a6355a
    patch("cms_1_10.patch", when="@1.10")
    # https://github.com/microsoft/onnxruntime/issues/4234#issuecomment-698077636
    # only needed when iconv is provided by libiconv
    patch("libiconv.patch", level=0, when="@1.7.2 ^libiconv")
    patch("libiconv-1.10.patch", level=0, when="@1.10.0 ^libiconv")
    # https://github.com/microsoft/onnxruntime/commit/de4089f8cbe0baffe56a363cc3a41595cc8f0809.patch
    patch("gcc11.patch", level=1, when="@1.7.2")
    # https://github.com/microsoft/onnxruntime/pull/16257
    patch(
        "https://github.com/microsoft/onnxruntime/commit/a3a443c80431c390cbf8855e9c7b2a95d413cd54.patch?full_index=1",
        sha256="537c43b061d31bf97d2778d723a41fbd390160f9ebc304f06726e3bfd8dc4583",
        when="@1.10:1.15",
    )

    dynamic_cpu_arch_values = ("NOAVX", "AVX", "AVX2", "AVX512")

    variant(
        "dynamic_cpu_arch",
        default="AVX512",
        values=dynamic_cpu_arch_values,
        multi=False,
        description="AVX support level",
    )

    generator("ninja")
    root_cmakelists_dir = "cmake"
    build_directory = "."

    def setup_build_environment(self, env):
        value = self.spec.variants["dynamic_cpu_arch"].value
        value = self.dynamic_cpu_arch_values.index(value)
        env.set("MLAS_DYNAMIC_CPU_ARCH", str(value))

    def setup_run_environment(self, env):
        value = self.spec.variants["dynamic_cpu_arch"].value
        value = self.dynamic_cpu_arch_values.index(value)
        env.set("MLAS_DYNAMIC_CPU_ARCH", str(value))

    def cmake_args(self):
        define = self.define
        define_from_variant = self.define_from_variant

        args = [
            define("onnxruntime_ENABLE_PYTHON", True),
            define("onnxruntime_BUILD_SHARED_LIB", True),
            define_from_variant("onnxruntime_USE_CUDA", "cuda"),
            define("onnxruntime_BUILD_CSHARP", False),
            define("onnxruntime_USE_TVM", False),
            define("onnxruntime_ENABLE_MICROSOFT_INTERNAL", False),
            define("onnxruntime_USE_TENSORRT", False),
            define("onnxruntime_CROSS_COMPILING", False),
            define("onnxruntime_USE_FULL_PROTOBUF", True),
            define("onnxruntime_DISABLE_CONTRIB_OPS", False),
        ]

        if self.spec.satisfies("+cuda"):
            args.extend(
                (
                    define("onnxruntime_CUDA_HOME", self.spec["cuda"].prefix),
                    define("onnxruntime_CUDNN_HOME", self.spec["cudnn"].prefix),
                    define("CMAKE_CUDA_FLAGS", "-cudart shared"),
                    define("CMAKE_CUDA_RUNTIME_LIBRARY", "Shared"),
                    define("CMAKE_TRY_COMPILE_PLATFORM_VARIABLES", "CMAKE_CUDA_RUNTIME_LIBRARY"),
                )
            )

        return args

    @run_after("install")
    def install_python(self):
        """Install everything from build directory."""
        args = std_pip_args + ["--prefix=" + prefix, "."]
        with working_dir(self.build_directory):
            pip(*args)
