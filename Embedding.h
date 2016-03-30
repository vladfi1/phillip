#ifndef _Embedding
#define _Embedding

#pragma once

#include <sys/types.h>
#include <vector>

//#include <functional>
//template <class T> using Embedding = std::function<void(T, std::vector<float>&)>;

template <typename T> struct Embedding
{
  virtual std::size_t size() const;
  virtual void writeEmbedding(const T& data, std::vector<float>& buffer) const;
};

// False -> 0, True -> 1
struct BoolEmbedding : Embedding<bool>
{
  std::size_t size() const { return 1; };
  void writeEmbedding(const bool& data, std::vector<float>& buffer) const;
};

// "singleton"
extern const BoolEmbedding boolEmbedding;

// one-hot embedding in a certain range
struct RangeEmbedding : Embedding<uint>
{
  const uint max;
  
  RangeEmbedding(uint max) : max(max) {}
  
  std::size_t size() const { return max; }
  
  void writeEmbedding(const uint& data, std::vector<float>& buffer) const;
};

struct FloatEmbedding : Embedding<float>
{
  std::size_t size() const { return 1; }
  
  void writeEmbedding(const float& data, std::vector<float>& buffer) const
  {
    buffer.push_back(data);
  }
};

// "singleton"
extern const FloatEmbedding floatEmbedding;

#endif

