#include <vector>
#include <utility>

#include "tensorflow/core/public/session.h"
#include "tensorflow/core/platform/env.h"

#include "GameState.h"

using namespace tensorflow;
using namespace std;

typedef vector<pair<string, Tensor>> feed_dict;

template <typename T>
void feed(const string&, const T&, feed_dict&);

// TODO: use "traits" to collapse these into one implementation?
// The only thing we need is to get the right DT_TYPE constant.
template<>
void feed(const string& name, const float& f, feed_dict& inputs) {
  Tensor t(DT_FLOAT, TensorShape());
  t.scalar<float>()() = f;
  inputs.push_back({name, t});
}

template<>
void feed(const string& name, const bool& b, feed_dict& inputs) {
  Tensor t(DT_BOOL, TensorShape());
  t.scalar<bool>()() = b;
  inputs.push_back({name, t});
}

//FIXME: no DT_UINT32
template<>
void feed(const string& name, const uint& u, feed_dict& inputs) {
  Tensor t(DT_INT32, TensorShape());
  t.scalar<uint>()() = u;
  inputs.push_back({name, t});
}

#define FEED(field) feed(name + "/" + #field, fed.field, inputs)

template<>
void feed(const string& name, const PlayerMemory& fed, feed_dict& inputs) {
  FEED(percent);
  //FEED(stock);
  FEED(facing);
  FEED(x);
  FEED(y);
  FEED(action);
  FEED(action_counter);
  FEED(action_frame);
  FEED(character);
  FEED(invulnerable);
  FEED(hitlag_frames_left);
  FEED(hitstun_frames_left);
  FEED(jumps_left);
  FEED(charging_smash);
  FEED(on_ground);
  FEED(speed_air_x_self);
  FEED(speed_ground_x_self);
  FEED(speed_y_self);
  FEED(speed_x_attack);
  FEED(speed_y_attack);
};

template<>
void feed(const string& name, const GameMemory& fed, feed_dict& inputs) {
  FEED(player_one);
  FEED(player_two);

  //FEED(player_two_pointer_x);
  //FEED(player_two_pointer_y);

  //FEED(frame);
  //FEED(menu_state);
  FEED(stage);
};

Session* startSession(const string& graph_file) {
  Session* session;
  Status status = NewSession(SessionOptions(), &session);
  if (!status.ok()) {
    std::cout << status.ToString() << std::endl;
    return nullptr;
  }

  // Read in the protobuf graph we exported
  // (The path seems to be relative to the cwd. Keep this in mind
  // when using `bazel run` since the cwd isn't where you call
  // `bazel run` but from inside a temp folder.)
  GraphDef graph_def;
  status = ReadBinaryProto(Env::Default(), graph_file, &graph_def);
  if (!status.ok()) {
    std::cout << status.ToString() << std::endl;
    return nullptr;
  }

  // Add the graph to the session
  status = session->Create(graph_def);
  if (!status.ok()) {
    std::cout << status.ToString() << std::endl;
    return nullptr;
  }
  
  return session;
}
