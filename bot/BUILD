package(default_visibility = ["//visibility:public"])

load("@icl_pip_deps//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_binary")

py_binary(
    name = "inhouse_bot",
    srcs = ["inhouse_bot.py"],
    deps = [
        "//protos:inhouse_py_pb2",
        "//protos:inhouse_py_pb2_grpc",
        "@abseil-py//absl:app",
        "@abseil-py//absl/flags",
        "@abseil-py//absl/logging",
        "//server:game_manager",
        requirement("discord.py"),
        requirement("disputils"),
    ],
)
