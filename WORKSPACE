workspace(name = "com_icl")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "io_abseil_py",
    urls = ["https://github.com/abseil/abseil-py/archive/c99edd8e3dffe3667a9f086db86aa259927ac429.zip"],
    strip_prefix = "abseil-py-c99edd8e3dffe3667a9f086db86aa259927ac429",
)

http_archive(
    name = "six_archive",
    urls = [
        "http://mirror.bazel.build/pypi.python.org/packages/source/s/six/six-1.10.0.tar.gz",
        "https://pypi.python.org/packages/source/s/six/six-1.10.0.tar.gz",
    ],
    sha256 = "105f8d68616f8248e24bf0e9372ef04d3cc10104f1980f54d57b2ce73a5ad56a",
    strip_prefix = "six-1.10.0",
    build_file = "@io_abseil_py//third_party:six.BUILD",
)

# === PIP Python Integration ===
http_archive(
    name = "rules_python",
    url = "https://github.com/bazelbuild/rules_python/releases/download/0.1.0/rules_python-0.1.0.tar.gz",
    sha256 = "b6d46438523a3ec0f3cead544190ee13223a52f6a6765a29eae7b7cc24cc83a0",
)

load("@rules_python//python:repositories.bzl", "py_repositories")

py_repositories()

load("@rules_python//python:pip.bzl", "pip_install")

pip_install(
    python_interpreter = "python3",
    requirements = "//:requirements.txt",
)

# === gRPC ===
http_archive(
    name = "com_github_grpc_grpc",
    strip_prefix = "grpc-1.34.0",
    urls = ["https://github.com/grpc/grpc/archive/v1.34.0.zip"],
)

load("@com_github_grpc_grpc//bazel:grpc_deps.bzl", "grpc_deps")

grpc_deps()

load("@com_github_grpc_grpc//bazel:grpc_extra_deps.bzl", "grpc_extra_deps")

grpc_extra_deps()

load("@com_github_grpc_grpc//bazel:grpc_python_deps.bzl", "grpc_python_deps")

grpc_python_deps()

