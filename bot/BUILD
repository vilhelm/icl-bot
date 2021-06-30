package(default_visibility = ["//visibility:public"])

load("@pip//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_binary")

py_binary(
    name = "inhouse_bot",
    srcs = ["inhouse_bot.py"],
    python_version = "PY3",
    deps = [
        "//protos:inhouse_py_pb2",
        "//protos:inhouse_py_pb2_grpc",
        "//server:game_manager",
        "@io_abseil_py//absl:app",
        "@io_abseil_py//absl/flags",
        "@io_abseil_py//absl/logging",
        requirement("discord.py"),
        requirement("discord-py-slash-command"),
        requirement("disputils"),
    ],
)
