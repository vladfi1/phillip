cc_binary(
    name = "loader",
    srcs = ["loader.cc"],
    deps = [
        ":ssbm",
        "//tensorflow/core:tensorflow",
    ]
)

cc_library(
    name = "ssbm",
    srcs = ["GameState.cpp", "Controller.cpp", "MemoryWatcher.cpp"],
    hdrs = ["GameState.h", "Controller.h", "MemoryWatcher.h"]
)

cc_binary(
    name = "cpu",
    srcs = ["cpu.cpp", "tf.hpp", "Serial.hpp"],
    deps = [
        ":ssbm",
        "//tensorflow/core:tensorflow",
    ]
)
