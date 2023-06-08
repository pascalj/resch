#define BUFSIZE 16

kernel void pe_0(const int cost, global const int *restrict data,
                 const int data_size, global int *restrict out) {
  float val = 23;
  // Data loading
  float local_buf[BUFSIZE];
  for(int i = 0; i < data_size; i++) {
    local_buf[i % BUFSIZE] += data[i];
  }
  // Processing
  val = local_buf[cost % BUFSIZE];
  for (int i = 0; i < cost; i++) {
    val += i;
  }
  *out = val;
}
kernel void pe_1(const int cost, global const int *restrict data,
                 const int data_size, global int *restrict out) {
  float val = 23;
  // Data loading
  float local_buf[BUFSIZE];
  for(int i = 0; i < data_size; i++) {
    local_buf[i % BUFSIZE] += data[i];
  }
  // Processing
  val = local_buf[cost % BUFSIZE];
  for (int i = 0; i < cost; i++) {
    val += i;
  }
  *out = val;
}
