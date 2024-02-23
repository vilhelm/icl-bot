package(default_visibility = ["//visibility:public"])

load("@rules_proto//proto:defs.bzl", "proto_library")
load("@rules_python//python:proto.bzl", "py_proto_library")

load("@rules_proto_grpc_python//:defs.bzl", "python_grpc_library")

proto_library(
    name = "inhouse_proto",
    srcs = ["inhouse.proto"],
)

py_proto_library(
    name = "inhouse_py_pb2",
    deps = [":inhouse_proto"],
)

python_grpc_library(
    name = "inhouse_py_pb2_grpc",
    protos = [":inhouse_proto"],
)
