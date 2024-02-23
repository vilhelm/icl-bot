package(default_visibility = ["//visibility:public"])

load("@icl_pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_binary", "py_library")

py_library(
    name = "game_manager",
    srcs = ["game_manager.py"],
    deps = [
        "@abseil-py//absl/logging",
        requirement("pandas"),
        requirement("scipy"),
        requirement("trueskill"),
    ],
)

py_binary(
    name = "inhouse",
    srcs = ["inhouse.py"],
    python_version = "PY3",
    deps = [
        ":rater",
        ":riot_client",
        "//protos:inhouse_py_pb2",
        "//protos:inhouse_py_pb2_grpc",
        "@abseil-py//absl:app",
        "@abseil-py//absl/flags",
        "@abseil-py//absl/logging",
        requirement("grpcio"),
        requirement("grpcio-reflection"),
        requirement("pandas"),
    ],
)

py_library(
    name = "riot_client",
    srcs = ["riot_client.py"],
    deps = [
        "@abseil-py//absl/logging",
        requirement("requests"),
    ],
)

py_binary(
    name = "rater",
    srcs = ["rater.py"],
    deps = [
        ":game_manager",
        "@abseil-py//absl:app",
        "@abseil-py//absl/flags",
    ],
)
