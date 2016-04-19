#include <sys/types.h>
#include <stdio.h>
#include <stdlib.h>
#include <iostream>
#include <fstream>
#include <sys/stat.h>
#include <unistd.h>
#include <pwd.h>

#include <chrono>
#include <thread>
#include <random>

#include "GameState.h"
#include "MemoryWatcher.h"
#include "Controller.h"
//#include "Serial.hpp"

#include "tensorflow/core/public/session.h"
#include "tensorflow/core/platform/env.h"

#include "tf.hpp"
#include "Serial.hpp"

using namespace std;
using namespace tensorflow;

void FirstTimeSetup()
{
    struct passwd *pw = getpwuid(getuid());
    string home_path = string(pw->pw_dir);
    string legacy_config_path = home_path + "/.dolphin-emu";
    string mem_watcher_path;
    string pipe_path;

    struct stat buffer;
    if(stat(legacy_config_path.c_str(), &buffer) != 0)
    {
        //If the legacy app path is not present, see if the new one is
        const char *env_XDG_DATA_HOME = getenv("XDG_DATA_HOME");
        if(env_XDG_DATA_HOME == NULL)
        {
            //Try $HOME/.local/share next
            string backup_path = home_path + "/.local/share/dolphin-emu";
            if(stat(backup_path.c_str(), &buffer) != 0)
            {
                cout << "ERROR: $XDG_DATA_HOME was empty and so was $HOME/.dolphin-emu and $HOME/.local/share/dolphin-emu " \
                    "Are you sure Dolphin is installed? Make sure it is, and then run the CPU again." << endl;
                exit(-1);
            }
            else
            {
                mem_watcher_path = backup_path;
                mem_watcher_path += "/MemoryWatcher/";
                pipe_path = backup_path;
                pipe_path += "/Pipes/";
            }
        }
        else
        {
            mem_watcher_path = env_XDG_DATA_HOME;
            mem_watcher_path += "/MemoryWatcher/";
            pipe_path = env_XDG_DATA_HOME;
            pipe_path += "/Pipes/";
        }
    }
    else
    {
        mem_watcher_path = legacy_config_path + "/MemoryWatcher/";
        pipe_path = legacy_config_path + "/Pipes/";
    }

    //Create the MemoryWatcher directory if it doesn't already exist
    if(stat(mem_watcher_path.c_str(), &buffer) != 0)
    {
        if(mkdir(mem_watcher_path.c_str(), 0775) != 0)
        {
            cout << "ERROR: Could not create the directory: \"" << mem_watcher_path << "\". Dolphin seems to be installed, " \
                "But this is not working for some reason. Maybe permissions?" << endl;
            exit(-1);
        }
        cout << "WARNING: Had to create a MemoryWatcher directory in Dolphin just now. " \
            "You may need to restart Dolphin and the CPU in order for this to work. (You should only see this warning once)" << endl;
    }

    ifstream src("Locations.txt", ios::in);
    ofstream dst(mem_watcher_path + "/Locations.txt", ios::out);
    dst << src.rdbuf();

    //Create the Pipes directory if it doesn't already exist
    if(stat(pipe_path.c_str(), &buffer) != 0)
    {
        if(mkdir(pipe_path.c_str(), 0775) != 0)
        {
            cout << "ERROR: Could not create the directory: \"" << pipe_path << "\". Dolphin seems to be installed, " \
                "But this is not working for some reason. Maybe permissions?" << endl;
            exit(-1);
        }
        cout << "WARNING: Had to create a Pipes directory in Dolphin just now. " \
            "You may need to restart Dolphin and the CPU in order for this to work. (You should only see this warning once)" << endl;
    }
}

template <typename rng>
bool flip(float p, rng& generator)
{
    bernoulli_distribution dist(p);
    return dist(generator);
}

template <typename rng>
float normal(float mean, float stddev, rng& generator)
{
  normal_distribution<float> dist(mean, stddev);
  return dist(generator);
}

template <typename rng>
float uniform(float a, float b, rng& generator)
{
  uniform_real_distribution<float> dist(a, b);
  return dist(generator);
}

template <typename rng>
float epsilonGreedy(float epsilon, float control, rng& generator)
{
  if(flip(epsilon, generator)) {
    return uniform(0, 1, generator);
  } else {
    return control;
  }
}

template <typename rng>
void getControl(Session* session, const GameMemory& memory, ControllerState& controllerState, rng& generator)
{
    feed_dict inputs;
    feed("predict/state", memory, inputs);
    
    vector<tensorflow::Tensor> outputs;

    Status status = session->Run(inputs, {"predict/action"}, {}, &outputs);
    if (!status.ok()) {
      cout << status.ToString() << endl;
      return;
    }
    
    auto control = outputs[0].vec<float>();
    
    //cout << control(0) << endl;
    
    controllerState.buttonA = flip(control(0), generator);
    controllerState.buttonB = flip(control(1), generator);
    controllerState.buttonX = flip(control(2), generator);
    controllerState.buttonY = flip(control(3), generator);
    controllerState.buttonL = flip(control(4), generator);
    controllerState.buttonR = flip(control(5), generator);
    
    float epsilon = 0.1;
    
    controllerState.analogL = epsilonGreedy(epsilon, control(6), generator);
    controllerState.analogR = epsilonGreedy(epsilon, control(7), generator);

    controllerState.mainX = epsilonGreedy(epsilon, control(8), generator);
    controllerState.mainY = epsilonGreedy(epsilon, control(9), generator);

    controllerState.cX = epsilonGreedy(epsilon, control(10), generator);
    controllerState.cY = epsilonGreedy(epsilon, control(11), generator);
}

// TODO: configure from command line
int main(int argc, char* argv[])
{
    //Do some first-time setup
    FirstTimeSetup();
    
    minstd_rand generator;
    
    //GameState *state = GameState::Instance();
    Controller controller("phillip");

    MemoryWatcher watcher;
    GameMemory memory;
    ControllerState controllerState;
    
    string graphFile = "models/simpleDQN.pb";
    
    uint last_frame = 0;
    uint record_count = 0;
    
    const uint recordFrames = 60 * 60;
    
    WriteBuffer writeBuffer;
    
    for(;; ++record_count)
    {
        Session* session = startSession(graphFile);
        
        for(uint frame = 0; frame < recordFrames;)
        {
            //controller->pressButton(Controller::BUTTON_D_RIGHT);
            while(!watcher.ReadMemory(memory)) {}
            //controller->releaseButton(Controller::BUTTON_D_RIGHT);
            
            if (memory.frame > last_frame + 1)
            {
                cout << "Missed frames " << last_frame + 1 << "-" << memory.frame - 1 << endl;
            }
            
            last_frame = memory.frame;
            
            if (memory.menu_state == IN_GAME)
            {
                getControl(session, memory, controllerState, generator);
                //cout << controllerState.mainX << endl;
                //cout << controllerState.mainX << endl;
                controller.sendState(controllerState);
                
                writeBuffer.write(memory);
                writeBuffer.write(controllerState);
                //fout.write(reinterpret_cast<char*>(&memory), sizeof(GameMemory));
                //fout.write(reinterpret_cast<char*>(&controllerState), sizeof(ControllerState));
                ++frame;
            } else {
              controller.emptyInput();
            }
        }
        
        // name recording based on stage/characters?
        string recordFile = "experience/" + to_string(record_count % 10);
        
        cout << "Writing experience to " << recordFile << endl;
        
        writeBuffer.writeFile(recordFile);
        writeBuffer.reset();
        
        session->Close();
    }
    
    return EXIT_SUCCESS;
}
