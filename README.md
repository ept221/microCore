# tinySoC
tinySoC is a small system on a chip consisting of an 8-bit CPU, an 80 column VGA graphics card, GPIO and counter/timer peripherals, all implemented on an ice40 FPGA.

## The CPU
![datapath](resources/datapath.jpg)
The CPU is an 8-bit RISC core, with a Harvard architecture. It has a 16-bit wide instruction memory, an 8-bit wide data memory, and both have a 16-bit address. The CPU has 16 general purpose 8-bit registers along with a 4-bit status register. The processor is not fully pipelined, but does fetch the next instruction while executing the current one. Most instructions execute in a single clock cycle, but a few take two or three.

## The GPU
![gpu](resources/gpu.jpg)
The GPU operates in a monochrome 80 column text mode, and outputs a VGA signal at a resolution of 640 by 480 at 60 frames per second. The GPU contains an ASCII buffer which the user can write to in order to display messages on the screen. A control register allows the user to set the text to one of 7 colours, and to enable an interrupt to the CPU which fires every time a frame finishes and enters the blanking period.

## The Instruction Set
![instruction set part 1](resources/instruction_set_part_1.jpg)
![instruction set part 2](resources/instruction_set_part_2.jpg)

## The Assembler

The assembler is case insensitive.

### Comments
Comments begin with semicolons.
```assembly
        .code
        ldi r0, 1 ; This is a comment
```

### Constants
Constants are in decimal by default, but hexadecimal and binary are also supported. Constants can also be negative and are stored in two's complement form.
```assembly
        .code
        ldi r0, 10     ; Decimal constant
        ldi r0, 0x0A   ; Hexadecimal constant
        ldi r0, 0b1010 ; Binary constant
        ldi r0, -10    ; A negative constant
```

### Label Definitions
Label definitions may be any string ending with a colon, as long as the string is not in the form of a constant or is one of the reserved keywords

```assembly
        .code
        ldi r0, 10
loop:   adi r0, -1
        jnz loop
        hlt
```

### Directives

#### .org
Sets the origin to the given address. Only forward movement of the origin is permitted.
```assembly
        .code
        ldi r0, 1
        out r0, 0
        jmp foo
        
        .org 0x0B
foo:    out r0, 1
        hlt
        
;*************************************************************************
; Assembles to the following:
; Address        Label          Code                     Source                      
; ------------------------------------------------------------------------
; 0x0000                        0b0000000000010001       LDI R0, 1                                         
; 0x0001                        0b0000000000000100       OUT R0, 0                                         
; 0x0002                        0b0000000010111000       JMP FOO                                           
; 0x0003                        0b0000000000001011                                                         
; 0x000B         FOO:           0b0000000000010100       OUT R0, 1                                         
; 0x000C                        0b0000000011110000       HLT
```

#### .db
Writes one or more data bytes sequentially into data memory.
```assembly
        .code
        ldi r0, 1
        out r0, 0
        out r0, 1
        hlt
        
        .data
        .db 0x01, 0x44, 0x73

;*************************************************************************
; Assembles to the following:
; Address        Label          Code                     Source                
; ------------------------------------------------------------------------
; 0x0000                        0b0000000000010001       LDI R0, 1                                         
; 0x0001                        0b0000000000000100       OUT R0, 0                                         
; 0x0002                        0b0000000000010100       OUT R0, 1                                         
; 0x0003                        0b0000000011110000       HLT                                               
;
; Address        Label          Data                                 
; ------------------------------------------
; 0x0000                        0x01                                         
; 0x0001                        0x44                                         
; 0x0002                        0x73    
```

#### .string
Writes a null terminated ASCII string into data memory. Double quotes and backslashes must be escaped with a backslash.

```assembly
        .code
        ldi r0, 1
        out r0, 0
        out r0, 1
        hlt
        
        .data
        .string "The robot says \"Hi!\""
        
;*************************************************************************
; Assembles to the following:
; Address        Label          Code                     Source                       
; ------------------------------------------------------------------------
; 0x0000                        0b0000000000010001       LDI R0, 1                                         
; 0x0001                        0b0000000000000100       OUT R0, 0                                         
; 0x0002                        0b0000000000010100       OUT R0, 1                                         
; 0x0003                        0b0000000011110000       HLT                                               
;
; Address        Label          Data                    
; ------------------------------------------
; 0x0000                        0x54                                         
; 0x0001                        0x68                                         
; 0x0002                        0x65                                         
; 0x0003                        0x20                                         
; 0x0004                        0x72                                         
; 0x0005                        0x6F                                         
; 0x0006                        0x62                                         
; 0x0007                        0x6F                                         
; 0x0008                        0x74                                         
; 0x0009                        0x20                                         
; 0x000A                        0x73                                         
; 0x000B                        0x61                                         
; 0x000C                        0x79                                         
; 0x000D                        0x73                                         
; 0x000E                        0x20                                         
; 0x000F                        0x22                                         
; 0x0010                        0x48                                         
; 0x0011                        0x69                                         
; 0x0012                        0x21                                         
; 0x0013                        0x22
; 0x0014                        0x00
```

#### .define
Equates a symbol with a number.
```assembly
        .code
        .define foo, 5
        ldi r0, foo
        hlt
        
;*************************************************************************
; Assembles to the following:        
; Address        Label          Code                     Source                                    
; ------------------------------------------------------------------------
; 0x0000                        0b0000000001010001       LDI R0, FOO                                       
; 0x0001                        0b0000000011110000       HLT  
```

### Expressions
Anytime an instruction or directive requires a numerical argument, an expression can be used.
Supported operations inside expressions include addition and subtraction. The location counter $ is also made available. Expressions may contain symbols, but must resolve within two passes of the assembler, and if used for directive arguments, must resolve in a single pass.

