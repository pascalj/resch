extern "C" {
void pe_NUM(const int* in, int* out, const int size) {
        long sum = 0;
        for(int i = 0; i < size; i++) {
                sum += in[i];
        }
        *out = sum;
}
}
