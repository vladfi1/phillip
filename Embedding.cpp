#include "Embedding.h"
#include <iostream>

void BoolEmbedding::writeEmbedding(const bool& data, std::vector<float>& buffer) const
{
  buffer.push_back(data ? 1 : 0);
}

const BoolEmbedding boolEmbedding;

void RangeEmbedding::writeEmbedding(const uint& data, std::vector<float>& buffer) const
{
  if (data >= max)
  {
    std::cout << "Warning: embedding range exceeded!" << std::endl;
  }
  
  for (uint i = 1; i < data; ++i)
  {
    buffer.push_back(0);
  }
  
  buffer.push_back(1);
  
  for (uint i = data; i < max; ++i)
  {
    buffer.push_back(0);
  }
}

const FloatEmbedding floatEmbedding;

