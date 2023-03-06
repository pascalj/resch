#ifndef NUM_PES
#define NUM_PES 1
#endif

#define BUFSIZE 16

#define PASTER(x, y) x##_##y
#define EVALUATOR(x, y) PASTER(x, y)

#define PE_CLONE_1 CLONE_PES(1)
#define PE_CLONE_2 PE_CLONE_1 CLONE_PES(2)
#define PE_CLONE_3 PE_CLONE_2 CLONE_PES(3)
#define PE_CLONE_4 PE_CLONE_3 CLONE_PES(4)
#define PE_CLONE_5 PE_CLONE_4 CLONE_PES(5)
#define PE_CLONE_6 PE_CLONE_5 CLONE_PES(6)
#define PE_CLONE_7 PE_CLONE_6 CLONE_PES(7)
#define PE_CLONE_8 PE_CLONE_7 CLONE_PES(8)
#define PE_CLONE_9 PE_CLONE_8 CLONE_PES(9)
#define GEN_PES() EVALUATOR(PE_CLONE, NUM_PES)

#define CLONE_PES(INDEX)                                                       \
  kernel void pe_##INDEX(const int cost, global const int *restrict data,      \
                         const int data_size, global int *restrict out) {      \
    float val = 23;                                                            \
    float local_buf[BUFSIZE];                                                  \
    for (int i = 0; i < data_size; i++) {                                      \
      local_buf[i % BUFSIZE] += data[i];                                       \
    }                                                                          \
    val = local_buf[cost % BUFSIZE];                                           \
    for (int i = 0; i < cost; i++) {                                           \
      val += i;                                                                \
    }                                                                          \
    *out = val;                                                                \
  }

GEN_PES()
