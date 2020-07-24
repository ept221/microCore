;*************************************************
        .define gpu_addr, 0x2000
        .define gpu_ctrl_reg, 0x80
        .define gpu_isr_vector, 0x20
;*************************************************      
        .code

        ldi r0, 0b00011000
        out r0, gpu_ctrl_reg

        ldi r2, gpu_addr[l]
        ldi r3, gpu_addr[h]

        ldi r0, text[l]                 ; comment here lol
        ldi r1, text[h]

loop:   lri r4, p0
        cpi r4, 0
        jz end ; this is a test

        sri r4, p2
        jmp loop

end:    hlt
;*************************************************
        .data

text:   .string "GitHub repo at: https://github.com/ept221"
;*************************************************