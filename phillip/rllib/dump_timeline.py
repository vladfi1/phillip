import ray
import sys

ray.init(redis_address="localhost:%s" % sys.argv[1])
ray.global_state.chrome_tracing_dump(filename="/tmp/timeline.json")

