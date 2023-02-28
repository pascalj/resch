kernel void pe_0(const int cost, global const int *restrict data,
                 const int data_size, global int *restrict out) {
  float val = 23;
  // Data loading
  for(int i = 0; i < data_size; i++) {
    val = data[i];
  }
  // Processing
  for (int i = 0; i < cost; i++) {
    val += i;
  }
  *out = val;
}
kernel void pe_1(const int cost, global const int *restrict data,
                 const int data_size, global int *restrict out) {
  float val = 23;
  // Data loading
  for(int i = 0; i < data_size; i++) {
    val = data[i];
  }
  // Processing
  for (int i = 0; i < cost; i++) {
    val += i;
  }
  *out = val;
}
