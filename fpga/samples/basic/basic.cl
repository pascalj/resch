kernel void pe_0(const int cost, global int* out) {
    float val = 23;
    for(int i = 0; i < cost; i++) {
        val *= i;
    }
    *out = val;
}
kernel void pe_1(const int cost) {
}
