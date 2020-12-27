package(default_visibility = ["//visibility:public"])

load("@rules_proto//proto:defs.bzl", "proto_library")
load("@com_github_grpc_grpc//bazel:python_rules.bzl", "py_grpc_library", "py_proto_library")

proto_library(
    name = "inhouse_proto",
    srcs = ["inhouse.proto"],
    deps = [],
)

py_proto_library(
    name = "inhouse_py_pb2",
    deps = [":inhouse_proto"],
)

py_grpc_library(
    name = "inhouse_py_pb2_grpc",
    srcs = [":inhouse_proto"],
    deps = [":inhouse_py_pb2"],
)
