module io(input wire clk,
          input wire [7:0] din,
          input wire [7:0] address,
          input wire w_en,
          input wire r_en,
          output wire [7:0] dout,
          output wire [7:0] io_pins,
);
    //***************************************************************
    // Manually Instantiate Pin Primitives Ror Tri-state Control
    
    SB_IO #(
        .PIN_TYPE(6'b 1010_01),
        .PULLUP(1'b 0)
    ) io_block_instance0 [7:0](
        .PACKAGE_PIN(io_pins),
        .OUTPUT_ENABLE(dir),
        .D_OUT_0({out1,out0,port[5:0]}),
        .D_IN_0(pins)
    );
    //***************************************************************
    // GPIO 
    reg [7:0] dir;
    reg [7:0] port;
    wire [7:0] pins;
    //***************************************************************
    // Memory Map
    always @(posedge clk) begin
        case(address)
            8'h00: begin                            // DIR
                if(w_en)
                    dir <= din;
                if(r_en)
                    dout <= dir;
            end
            8'h01: begin                            // PORT
                if(w_en)
                    port <= din;
                if(r_en)
                    dout <= port;
            end
            8'h02: begin                            // PINS
                if(r_en)
                    dout <= pins;
            end
            8'h03: begin                            // scaleFactor LSB
                if(w_en)
                    scaleFactor[7:0] <= din;
                if(r_en)
                    dout <= scaleFactor[7:0];
            end
            8'h04: begin                            // scaleFactor MSB       
                if(w_en)
                    scaleFactor[15:8] <= din;
                if(r_en)
                    dout <= scaleFactor[15:8];
            end
            8'h05: begin                            // counterControl
                if(w_en)
                    counterControl <= din;
                if(r_en)
                    dout <= counterControl;
            end
            8'h06: begin                            // cmpr0
                if(w_en)
                    cmpr0 <= din;
                if(r_en)
                    dout <= cmpr0;
            end
            8'h07: begin                            // cmpr1
                if(w_en)
                    cmpr1 <= din;
                if(r_en)
                    dout <= cmpr1;
            end
        endcase
    end
    //***************************************************************
    // Counter/Timer
    reg [7:0] counter;
    reg [15:0] prescaler;
    reg [15:0] scaleFactor;
    reg [7:0] cmpr0;
    reg [7:0] cmpr1;
    reg [7:0] counterControl = 0;
    wire match0;
    wire match1;
    wire scaled;
    reg out0;
    reg out1;

    // prescaler
    always @(posedge clk) begin
        prescaler <= prescaler + 1;
        if(prescaler == scaleFactor) begin
            scaled <= 1;
            prescaler <= 0;
        end
        else begin
            scaled <= 0;
        end
    end

    // counter
    always @(posedge clk) begin
        if(scaled) begin
            counter <= counter + 1;
            if(counterControl[1:0] == 2'b00) begin                  // CTC mode
                if(match0) begin                            // On match0:
                    counter <= 0;                           // Reset the counter
                    out0 <= ~out0;                          // Toggle the output
                end
            end
            else if(counterControl[1:0] == 2'b01) begin              // PWM mode
                if(counter == 8'd255) begin                 // If finished 255 cycles, on next edge (start of zero), set the outputs to 1
                    out0 <= 1;
                    out1 <= 1;
                end
                else begin
                    if(match0) begin                        // On match0:
                        out0 <= 0;                          // clear out0
                    end
                    if(match1) begin                        // On match1:
                        out1 <= 0;                          // clear out1
                    end
                end
            end
        end
    end

    // comparators
    assign match0 = (counter == cmpr0) ? 1 : 0;
    assign match1 = (counter == cmpr1) ? 1 : 0;
    //***************************************************************
endmodule