PLATFORM ?= xilinx_u280_gen3x16_xdma_1_202211_1 
TARGET ?= sw_emu
FLAGS ?= -DNUM_PES=9

basic.xclbin: basic.xo
	v++ $(FLAGS) -l  -t $(TARGET) --platform $(PLATFORM) -o basic.xclbin basic.xo

basic.xo: basic.cl
	v++ $(FLAGS) -c  -t $(TARGET) --platform $(PLATFORM) -o basic.xo basic.cl

.PHONY: clean
clean:
	rm -rf *.log *.xo *.xclbin v++_*
