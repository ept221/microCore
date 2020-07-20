lint: 
	verilator --lint-only -Wall src/cpu/alu.v src/cpu/control.v src/cpu/cpu.v src/cpu/regFile.v src/gpu/gpu.v src/gpu/pll.v src/gpu/vga.v src/io/io.v src/memory/d_ram.v src/memory/i_ram.v src/soc/top.v

sim:
	mkdir -p build/sim
	iverilog -o build/sim/sim.vvp src/cpu/alu.v src/cpu/control.v src/cpu/cpu.v src/cpu/regFile.v src/sim/test_tb.v src/memory/d_ram.v src/memory/i_ram.v src/io/io.v src/sim/SB_IO.v
	vvp build/sim/sim.vvp
	mv test_tb.vcd build/sim/test_tb.vcd
	open -a Scansion build/sim/test_tb.vcd

synth: src/soc/top.v
	mkdir -p build/synth
	yosys -p "synth_ice40 -json build/synth/hardware.json" src/cpu/alu.v src/cpu/control.v src/cpu/cpu.v src/cpu/regFile.v src/gpu/gpu.v src/gpu/pll.v src/gpu/vga.v src/io/io.v src/memory/d_ram.v src/memory/i_ram.v src/soc/top.v

pnr: build/synth/hardware.json
	mkdir -p build/pnr
	nextpnr-ice40 --lp8k --package cm81 --json build/synth/hardware.json --pcf src/soc/pins.pcf --asc build/pnr/hardware.asc  --pcf-allow-unconstrained --freq 16

pack: build/pnr/upload.asc
	mkdir -p build/binary
	icepack build/pnr/upload.asc build/binary/upload.bin

upload: build/binary/upload.bin
	tinyprog -p build/binary/upload.bin

clean_code:
	rm -rf build/assembled build/images build/pnr/upload.asc build/binary

clean:
	rm -rf build