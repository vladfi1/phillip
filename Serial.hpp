#include <fstream>
#include <cstring>

// in-memory buffer for writing data
// TODO: find out whether something like this exists in the stl/boost
class WriteBuffer {
private:  
  std::size_t capacity;
  std::size_t size;
  char* buf;

public:
  WriteBuffer(std::size_t cap) : capacity(cap), size(0), buf(new char[capacity]) {}
  WriteBuffer() : WriteBuffer(64) {}
  
  ~WriteBuffer() { delete buf; }
  
  std::size_t getCapacity() { return capacity; }
  std::size_t getSize() { return size; }
  const char* getBuf() { return buf; }
  
  void reset() { size = 0; }
  
  void reserve(std::size_t new_capacity) {
    char* new_buf = new char[new_capacity];
    memcpy(new_buf, buf, size);
    delete buf;
    buf = new_buf;
    capacity = new_capacity;
  }
  
  template <typename T>
  void write(const T& data) {
    std::size_t new_size = size + sizeof(T);
    if (new_size > capacity) {
      reserve(2 * new_size);
    }
    
    memcpy(buf + size, &data, sizeof(T));
    size = new_size;
  }
  
  void writeFile(const string& filename) {
    ofstream fout;
    fout.open(filename, ios::binary | ios::out);
    fout.write(buf, size);
    fout.close();
  }
};

/* Example usage

struct Point {
  float x;
  float y;
  
  Point() : x(0.0), y(0.0) {}
  
  Point(float _x, float _y) : x(_x), y(_y) {}
};

struct Segment {
  Point p1, p2;
};

int main() {
  WriteBuffer b(10);
  
  Segment s;
  s.p1.x = 1;
  s.p1.y = 2;
  s.p2.x = 3;
  s.p2.y = 4;
  
  //Point p(1.0, 2.0);
  
  b.write(s);
  
  ofstream fout;
  fout.open("file.bin", ios::binary | ios::out);
  
  fout.write(b.getBuf(), b.getSize());
  
  fout.close();
  return 0;
}

*/
