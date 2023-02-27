PLATFORM ?= xilinx_u280_gen3x16_xdma_1_202211_1 
TARGET ?= sw_emu

basic.xclbin: basic.xo
	v++ -l  -t $(TARGET) --platform $(PLATFORM) -o basic.xclbin basic.xo

basic.xo: basic.cl
	v++ -c  -t $(TARGET) --platform $(PLATFORM) -o basic.xo basic.cl

.PHONY: clean
clean:
	rm -rf *.log *.xo *.xclbin v++_*
