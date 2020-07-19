##############################################################################################################
import re
import sys
import table
import argparse
##############################################################################################################
# Support Classes
class Symbol:

    def __init__(self):
        self.labelDefs = {}
        self.expr = []
        self.defs = {}

class Code:

    def __init__(self):
        self.code_data = []
        self.code_address = 0
        self.data_data = []
        self.data_address = 0
        self.code_label = ""
        self.data_label = ""

        self.codeSegment = False
        self.dataSegment = False
        self.segment = ""

    def write_code(self, line, data, code_string, status):

        if(self.code_address > 65535):
            error("Cannot write past 0xFFFF. Out of program memory!",line)
            sys.exit(2)

        self.code_data.append([line, str(line[0][0]), format(self.code_address,'04X'),self.code_label,data, code_string, status])
        self.code_label = ""
        self.code_address += 1

    def write_data(self, line, data):
        self.data_data.append([line, str(line[0][0]), format(self.data_address,'04X'),self.data_label,data])
        self.data_label = ""
        self.data_address += 1
##############################################################################################################
# File reading functions
def read(name):
    # This function reads in lines from the asm file
    # It processes them and puts them into the form:
    # [[Line_number, Program_Counter] [body] [comment]]
    # Line_number corrisponds to the line on the 
    # source code. the Program_Counter is incremented
    # every time there is a non-empty line (even a comment
    # counts as non empty). Note that two consecutive PC
    # locations do NOT nessisarily corrispond to two
    # consecutive address locations

    # [[Line_number, Program_Counter] [body] 'comment']
    
    file = open(name, 'r')
    lines = []
    lineNumber = 0
    pc = 0
    
    for lineNumber, line in enumerate(file, start = 1):
        line = line.strip()
        if(line):
            block = []
            rest = [] 												   # The input line without the comment
            comment = ''
            commentIndex = line.find(";")
            if(commentIndex != -1):
                comment = line[commentIndex:]
                rest = line[:commentIndex].strip()
            else:
                rest = line

            block.append([lineNumber, pc])
            if(rest): 												   # If we have code after we strip any comment out
                split_rest = re.split(r'(\+|-|,|"|\s|(?:\[(?:l|L|h|H)\]))\s*', rest)
                split_rest = list(filter(None, split_rest))
                block.append(split_rest)
            else:
                block.append([])
            block.append(comment)
            lines.append(block)
            pc += 1
            
    file.close()
    return lines
##############################################################################################################
def lexer(lines):
    tokens = []
    string = ""
    stringCapture = False
    codeLines = [x for x in lines if len(x[1])]                # codeLines only includes lines with code,
    for line in codeLines:                                     # so if a line only has comments, then
        tl = []                                                 # then it's out
        for word in line[1]:
            if(stringCapture == False):
                word = word.strip()
                word = word.upper()
                if word == "\"":
                    tl.append(["<quote>", word])
                    stringCapture = True
                elif(re.match(r'^\s*$',word)):
                    continue
                elif word in table.mnm_r_i:
                    tl.append(["<mnm_r_i>", word])
                elif word in table.mnm_r_l:
                    tl.append(["<mnm_r_l>", word])
                elif word in table.mnm_r_r:
                    tl.append(["<mnm_r_r>", word])
                elif word in table.mnm_r:
                    tl.append(["<mnm_r>", word])
                elif word in table.mnm_r_rp:
                    tl.append(["<mnm_r_rp>", word])
                elif word in table.mnm_rp:
                    tl.append(["<mnm_rp>", word])
                elif word in table.mnm_a:
                    tl.append(["<mnm_a>", word])
                elif word in table.mnm_n:
                    tl.append(["<mnm_n>", word])
                elif word in table.mnm_m:
                    tl.append(["<mnm_m>", word])
                elif word in table.drct_0:
                    tl.append(["<drct_0>", word])
                elif word in table.drct_1:
                    tl.append(["<drct_1>", word])
                elif word in table.drct_2:
                    tl.append(["<drct_2>", word])
                elif word in table.drct_m:
                    tl.append(["<drct_m>", word])
                elif word in table.drct_s:
                    tl.append(["<drct_s>", word])
                elif word == "[L]" or word == "[H]":
                    tl.append(["<selector>", word])
                elif word == ",":
                    tl.append(["<comma>", word])
                elif word == "+":
                    tl.append(["<plus>", word])
                elif word == "-":
                    tl.append(["<minus>", word])
                elif re.match(r'^R((1*)[02468])|(R16)$',word):
                    tl.append(["<reg_even>", word])
                elif re.match(r'^R((1*)[13579])|(R15)$',word):
                    tl.append(["<reg_odd>", word])
                elif re.match(r'^.+:$',word):
                    tl.append(["<lbl_def>", word])
                elif(re.match(r'^(0X)[0-9A-F]+$', word)):
                    tl.append(["<hex_num>", word])
                elif(re.match(r'^[0-9]+$', word)):
                    tl.append(["<dec_num>", word])
                elif(re.match(r'^(0B)[0-1]+$', word)):
                    tl.append(["<bin_num>", word]) 
                elif(re.match(r'^[A-Z_]+[A-Z_]*$', word)):
                    tl.append(["<symbol>", word])
                elif word == "$":
                    tl.append(["<lc>", word])
                else:
                    tl.append(["<idk_man>", word])
                    error("Unknown token: " + word, line)
                    return [0 , 0]
            else:
                slash_count = 0
                if(word == "\""):
                    for x in reversed(tl[-1][1]):
                        if x == "\\":
                            slash_count += 1
                        else:
                            break
                    if(slash_count % 2 == 0):
                        tl.append(["<quote>", word])
                        stringCapture = False
                    else:
                        tl.append(["<string_seg>", word])
                else:
                    tl.append(["<string_seg>", word])
        tokens.append(tl)
    return [codeLines, tokens]
##############################################################################################################
def error(message, line):
    print("Error at line " + str(line[0][0]) + ": " + message)
##############################################################################################################
def parse_expr(tokens, symbols, code, line):
    data = ["<expr>"]
    er = ["<error>"]
    if not tokens:
        return 0
    ##################################################
    while(tokens):
        if(tokens[0][0] in {"<plus>", "<minus>"}):              # If we have an operator
            data.append(tokens.pop(0))                          # Get the operator
        elif(len(data) > 1):                                    # Else if we have a valid expression but the token we looked at wasn't an operator 
            return data
        if(len(data) > 1 and (not tokens)):                     # If we just saw an operator or don't have an expression yet, but we have no tokens
            error("Expression missing number/symbol!",line)
            return er
        if(tokens[0][0] not in {"<hex_num>", "<dec_num>", "<bin_num>", "<symbol>", "<lc>"}): # If we just saw an operator or don't have an expression yet, but next token isn't a number
            if(tokens[0][0] in {"<plus>", "<minus>"}):
                error("Expression has extra operator!",line)
                return er
            if(tokens[0][0] == "<selector>"):
                error("Expression has bad selector!",line)
                return er
            if(len(data) > 1):
                error("Expression has bad identifier!",line)
                return er
            else:
                return 0
        data.append(tokens.pop(0))                              # Get the number
        if(tokens and tokens[0][0] == "<selector>"):
            data.append(tokens.pop(0))

    return data
##############################################################################################################
def expr_to_str(expr):
    expr_str = expr[0][1]
    if(expr[0][0] != "<plus>" and expr[0][0] != "<minus>" and len(expr) != 1 and expr[1][0] != "<selector>"):
        expr_str = expr_str + " "

    for i, x in enumerate(expr[1:-1], start = 1):
        expr_str = expr_str + x[1]
        if(expr[i+1][0] != "<selector>"):
            expr_str += " "
    if(len(expr) != 1):
        expr_str = expr_str + expr[-1][1]
    return expr_str
##############################################################################################################
def evaluate(expr, symbols, address):
    ##################################################
    def modify(val, selector):
        if(selector == "[L]"):
            return int(format(val, '016b')[8:16],base=2)
        elif(selector == "[H]"):
            return int(format(val, '016b')[0:8],base=2)
        else:
            return val
    ##################################################

    sign, pop, numpos, result = 1, 2, -1, 0
    while(expr):
        ##################################################
        if(len(expr) >= 3 and expr[-1][0] == "<selector>"):
            pop = 3
            numpos = -2
            selector = expr[-1][1]
            if(expr[-3][0] == "<plus>"):
                sign = 1
            else:
                sign = -1
        elif(len(expr) == 2 and expr[-1][0] == "<selector>"):
            pop = 2
            numpos = -2
            selector = expr[-1][1]
            sign = 1
        elif(len(expr) >= 2):
            pop = 2
            numpos = -1
            selector = ""
            if(expr[-2][0] == "<plus>"):
                sign = 1
            else:
                sign = -1
        else:
            pop = 1
            numpos = -1
            selector = ""
            sign = 1
        ##################################################
        if(expr[numpos][0] == "<hex_num>"):
            result += sign*modify(int(expr[numpos][1], base=16),selector)
            expr = expr[:-pop]
        elif(expr[numpos][0] == "<dec_num>"):
            result += sign*modify(int(expr[numpos][1], base=10),selector)
            expr = expr[:-pop]
        elif(expr[numpos][0] == "<bin_num>"):
            result += sign*modify(int(expr[numpos][1], base=2),selector)
            expr = expr[:-pop]
        elif(expr[numpos][0] == "<lc>"):
            result += sign*modify((address),selector)
            expr = expr[:-pop]
        elif(expr[numpos][1] in symbols.labelDefs):
            result += sign*modify(int(symbols.labelDefs[expr[numpos][1]],base=16),selector)
            expr = expr[:-pop]
        elif(expr[numpos][1] in symbols.defs):
            result += sign*modify(int(symbols.defs[expr[numpos][1]],base=16),selector)
            expr = expr[:-pop]
        else:
            expr += [["<plus>", "+"],["<hex_num>",hex(result)]]
            return expr
        ##################################################
    return [result]
##############################################################################################################
def parse_lbl_def(tokens, symbols, code, line):
    er = ["<error>"]
    if not tokens:
        return 0
    ##################################################
    if(tokens[0][0] == "<lbl_def>"):
        lbl = tokens[0][1]
        if(not code.segment):
            error("Label cannot be defined outside memory segment!", line)
            return er
        if((code.segment == "code" and code.code_label) or (code.segment == "data" and code.data_label)):
            error("Label cannot come after another label, before the first one is bound!",line)
            return er
        elif lbl[:-1] in symbols.labelDefs:
            error("Label already in use!",line)
            return er
        elif lbl[:-1] in table.reserved:
            error("Label cannot be keyword!",line)
            return er
        elif re.match(r'^(0X)[0-9A-F]+$',lbl[:-1] or
             re.match(r'^[0-9]+$',lbl[:-1]) or
             re.match(r'^(0B)[0-1]+$')):
            error("Label cannot be number!",line)
            return er
        elif lbl[:-1] in (symbols.defs):
            error("Label conflicts with previous symbol definition",line)
            return er
        else:
            if(code.segment == "code"):
                symbols.labelDefs[lbl[:-1]] = '{0:0{1}X}'.format(code.code_address,4)
                code.code_label = lbl
            else:
                symbols.labelDefs[lbl[:-1]] = '{0:0{1}X}'.format(code.data_address,4)
                code.data_label = lbl
        return tokens.pop(0)
    else:
        return 0
##############################################################################################################
def setCodeSegment(arg, symbols, code, line):
    if(code.codeSegment or code.segment == "code"):
        error("Code segment already defined!",line)
        return 0
    else:
        code.codeSegment = True
        code.segment = "code"
        return 1
##############################################################################################################
def setDataSegment(arg, symbols, code, line):
    if(code.dataSegment or code.segment == "data"):
        error("Data segment already defined!",line)
        return 0
    else:
        code.dataSegment = True
        code.segment = "data"
        return 1
##############################################################################################################
def org(arg, symbols, code, line):
    address = 0
    if(not code.segment):
        error("Directive must be within code or data segment!",line)
        return 0
    elif(code.segment == "code"):
        address = code.code_address
    else:
        address = code.data_address

    if(arg < 0):
        error("Expression must be positive!",line)
        return 0
    elif(arg < address):
        error("Cannot move origin backwards!",line)
        return 0
    elif(arg > 65535):
        error("Cannot set origin past 0xFFFF",line)
        return 0
    else:
        if(code.segment == "code"):
            code.code_address = arg
            if(code.code_label):
                symbols.labelDefs[lbl[:-1]] = '{0:0{1}X}'.format(address,4)
        else:
            code.data_address = arg
            if(code.data_label):
                symbols.labelDefs[lbl[:-1]] = '{0:0{1}X}'.format(address,4)
    return 1
##############################################################################################################
def define(args, symbols, code, line):
    if(args[0] in symbols.labelDefs):
        error("Symbol definition conflicts with label def!",line)
        return 0
    if(args[0] in symbols.defs):
        error("Symbol definition conflicts with previous definition!",line)
        return 0
    symbols.defs[args[0]] = hex(args[1])
    return 1
##############################################################################################################
def db(args, symbols, code, line):
    if(code.segment != "data"):
        error("Directive must be within data segment!",line)
        return 0

    for arg in args:
        if(arg < -128 or arg > 255):
            error("Argument must be >= -128 and <= 255",line)
            return 0
        if(arg < 0):
            arg = 255 - abs(arg) + 1

        code.write_data(line, format(arg, '02X'))

    return 1

def store_string(arg, symbols, code, line):
    if(code.segment != "data"):
        error("Directive must be within data segment!",line)
        return 0

    for char in arg:
        if(int(ord(char)) > 128):
            error("Unsupported character in string!",line)
            return 0

    new_str = bytes(arg,"utf-8").decode("unicode_escape")

    for char in new_str:
        code.write_data(line,format(ord(char),'02X'))

    return 1
##############################################################################################################
directives = {
    # Format:
    # [function, min_args, max_args, name]
    # -1 means no bound

    ".CODE": setCodeSegment,
    ".DATA": setDataSegment,
    ".ORG":  org,
    ".DEFINE": define,
    ".DB":  db,
    ".STRING": store_string
}
##############################################################################################################
def parse_drct(tokens, symbols, code, line):
    args = [tokens, symbols, code, line]
    data = ["<drct>"]
    er = ["<error>"]
    if not tokens:
        return 0
    ##################################################
    # [drct_0]
    if(tokens[0][0] == "<drct_0>"):
        drct_0 = tokens[0][1]
        data.append(tokens.pop(0))
        status = directives[drct_0](0,symbols,code,line)
        if not status:
            return er
        return data
    ##################################################
    # [drct_1]
    if(tokens[0][0] == "<drct_1>"):
        drct_1 = tokens[0][1]
        data.append(tokens.pop(0))
        address = 0
        if(code.segment == "code"):
            address = code.code_address
        elif(code.segment == "data"):
            address = code.data_address
        if(not tokens):
            error("Directive missing argument!",line)
            return er
        expr = parse_expr(*args)
        if(not expr):
            error("Directive has bad argument!", line)
            return er
        if(expr == er):
            return er
        val = evaluate(expr[1:],symbols,address)
        data.append(expr)
        if(len(val) == 1):
            status = directives[drct_1](val[0],symbols,code,line)
            if(not status):
                return er
        else:
            error("Directive relies upon unresolved symbol!",line)
        return data
    ##################################################
    # [drct_2]
    if(tokens[0][0] == "<drct_2>"):
        drct_2 = tokens[0][1]
        data.append(tokens.pop(0))
        address = 0
        if(code.segment == "code"):
            address = code.code_address
        elif(code.segment == "data"):
            address = code.data_address
        if(not tokens):
            error("Directive missing argument!",line)
            return er
        if(tokens[0][0] != "<symbol>"):
            error("Directive has bad argument!",line)
            return er
        symbol = tokens[0][1]
        data.append(tokens.pop(0))
        if(not tokens):
            error("Directive missing comma and argument!",line)
            return er
        if(tokens[0][0] != "<comma>"):
            if(tokens[0][0] not in {"<hex_num>","<dec_num>","<bin_num>","<symbol>"}):
                error("Directive has bad argument!",line)
                return er
            error("Directive missing comma!",line)
            return er
        data.append(tokens.pop(0))
        if(not tokens):
            error("Directive missing argument!",line)
            return er
        expr = parse_expr(*args)
        if(not expr):
            error("Directive has bad argument!",line)
            return er
        elif(expr == er):
            return er
        data.append(expr)
        val = evaluate(expr[1:],symbols,address)
        if(len(val) == 1):
            status = directives[drct_2]([symbol,val[0]],symbols,code,line)
            if(not status):
                return er
        else:
            error("Directive relies upon unresolved symbol!",line)
            return er
        return data
    ##################################################
    # [drct_m]
    if(tokens[0][0] == "<drct_m>"):
        drct_m = tokens[0][1]
        d_args = []
        data.append(tokens.pop(0))

        address = 0
        if(code.segment == "code"):
            address = code.code_address
        elif(code.segment == "data"):
            address = code.data_address

        if(not tokens):
            error("Directive missing argument!",line)
            return er
        expr = parse_expr(*args)
        if(not expr):
            error("Directive has bad argumet!",line)
            return er
        elif(expr == er):
            return er
        data.append(expr)
        val = evaluate(expr[1:],symbols,address)
        if(len(val) == 1):
            d_args.append(val[0])
        else:
            error("Directive relies upon unresolved symbol!",line)
            return er

        while(tokens):
            if(tokens[0][0] != "<comma>"):
                error("Missing comma!",line)
                return er
            data.append(tokens.pop(0))
            if(not tokens):
                error("Directive missing last argument or has extra comma!",line)
                return er
            expr = parse_expr(*args)
            if(not expr):
                error("Directive has bad argument!",line)
                return er
            data.append(expr)
            if(expr == error):
                return er
            data.append(expr)
            val = evaluate(expr[1:],symbols,address)
            if(len(val) == 1):
                d_args.append(val[0])
            else:
                error("Directive relies upon unresolved symbol!",line)
                return er
        status = directives[drct_m](d_args,symbols,code,line)
        if not status:
            return er
        return data
    ##################################################
    # [drct_s]
    if(tokens[0][0] == "<drct_s>"):
        drct_s = tokens[0][1]
        data.append(tokens.pop(0))
        string = ""
        if(not tokens):
            error("Directive missing argument!",line)
            return er
        if(tokens[0][0] != "<quote>"):
            error("Directive missing start quote!",line)
            return er
        data.append(tokens.pop(0))

        while(len(tokens) and tokens[0][0] != "<quote>"):
            string += tokens[0][1]
            data.append(tokens.pop(0))

        if(not tokens or tokens[0][0] != "<quote>"):
            error("Directive missing end quote!",line)
            return er
        data.append(tokens.pop(0))

        status = directives[drct_s](string,symbols,code,line)
        if not status:
            return er
        return data
##############################################################################################################
def parse_code(tokens, symbols, code, line):
    args = [tokens, symbols, code, line]
    data = ["<code>"]
    er = ["<error>"]
    if not tokens:
        return 0
    ##################################################
    # Check if inside the code segment
    if(tokens[0][0] in {"<mnm_r_i>","<mnm_r_l>","<mnm_r_r>","<mnm_r>",
                        "<mnm_r_rp>","<mnm_rp>","<mnm_a>","<mnm_m>","<mnm_n>"}
                        and not (code.segment == "code")):
        error("Instructions must be inside the code segment!", line)
        return ["<error>"]
    ##################################################
    # [mnm_r_i] or [mnm_r_l]
    if(tokens[0][0] == "<mnm_r_i>" or tokens[0][0] == "<mnm_r_l>"):
        inst_str = tokens[0][1]
        inst_tkn = tokens[0][0]
        data.append(tokens.pop(0))
        if(not tokens):
            error("Instruction missing register!",line)
            return er
        if(tokens[0][0] != "<reg_even>" and tokens[0][0] != "<reg_odd>"):
            error("Instruction has a bad register!",line)
            return er
        reg1 = tokens[0][1]
        data.append(tokens.pop(0))
        if(not tokens):
            error("Instruction missing comma and argument!",line)
            return er
        if(tokens[0][0] != "<comma>"):
            if(tokens[0][0] not in {"<hex_num>","<dec_num>","<bin_num>","<symbol>"}):
                error("Instruction has bad argument!",line)
                return er
            error("Instruction missing comma!",line)
            return er
        data.append(tokens.pop(0))
        if(not tokens):
            error("Instruction missing argument!",line)
            return er
        expr = parse_expr(*args)
        if(not expr):
            error("Instruction has bad argument!",line)
            return er
        elif(expr == er):
            return er
        data.append(expr)
        ##################################################
        # Code Generation
        instruction = ""
        if(inst_tkn == "<mnm_r_i>"):
            instruction = table.mnm_r_i[inst_str]
        else:
            instruction = table.mnm_r_l[inst_str]
        instruction = format(int(reg1[1:]),'04b') + instruction[4:]
        code_string = inst_str + " " + reg1 + ", " + expr_to_str(expr[1:])
        val = evaluate(expr[1:],symbols,code.code_address)
        if(len(val) == 1):
            numb = val[0]
            if(numb < -128 or numb > 255):
                error("Argument must be >= -128 and <= 255",line)
                return er
            else:
                if(numb >= 0):
                    instruction = instruction[0:4] + format(numb,'08b') + instruction[12:]
                else:
                    numb = 255 - abs(numb) + 1
                    instruction = instruction[0:4] + format(numb,'08b') + instruction[12:]
                code.write_code(line,instruction,code_string,0)
        else:
            code.write_code(line,instruction,code_string,[inst_tkn,val])

        return data
    ##################################################
    # [mnm_r_r]
    if(tokens[0][0] == "<mnm_r_r>"):
        inst_str = tokens[0][1]
        data.append(tokens.pop(0))
        if(not tokens):
            error("Instruction missing register!",line)
            return er
        if(tokens[0][0] != "<reg_even>" and tokens[0][0] != "<reg_odd>"):
            error("Instruction has a bad register!",line)
            return er
        reg1 = tokens[0][1]
        data.append(tokens.pop(0))
        if(not tokens):
            error("Instruction missing comma and register!",line)
            return er
        if(tokens[0][0] != "<comma>"):
            if(tokens[0][0] != "<reg_even>" or tokens[0][0] != "<reg_odd>"):
                error("Instruction has a bad register!",line)
                return er
            error("Instruction missing comma!",line)
            return er
        data.append(tokens.pop(0))
        if(not tokens):
            error("Instruction missing register!",line)
            return er
        if(tokens[0][0] != "<reg_even>" and tokens[0][0] != "<reg_odd>"):
            error("Instruction has a bad register!",line)
            return er
        reg2 = tokens[0][1]
        data.append(tokens.pop(0))
        ##################################################
        # Code Generation
        instruction = table.mnm_r_r[inst_str]
        instruction = format(int(reg1[1:]),'04b') + format(int(reg2[1:]),'04b') + instruction[8:]
        code_string = inst_str + " " + reg1 + ", " + reg2
        code.write_code(line,instruction,code_string,0)
        return data
    ##################################################
    # [mnm_r]
    if(tokens[0][0] == "<mnm_r>"):
        inst_str = tokens[0][1]
        data.append(tokens.pop(0))
        if(not tokens):
            error("Instruction missing register!",line)
            return er
        if(tokens[0][0] != "<reg_even>" and tokens[0][0] != "<reg_odd>"):
            error("Instruction has a bad register!",line)
            return er
        reg1 = tokens[0][1]
        data.append(tokens.pop(0))
        ##################################################
        # Code Generation
        instruction = table.mnm_r[inst_str]
        instruction = format(int(reg1[1:]),'04b') + instruction[4:]
        code_string = inst_str + " " + reg1
        code.write_code(line,instruction,code_string,0)
        return data
    ##################################################
    # [mnm_r_rp]
    if(tokens[0][0] == "<mnm_r_rp>"):
        inst_str = tokens[0][1]
        data.append(tokens.pop(0))
        if(not tokens):
            error("Instruction missing register!",line)
            return er
        if(tokens[0][0] != "<reg_even>" and tokens[0][0] != "<reg_odd>"):
            error("Instruction has a bad register!",line)
            return er
        reg1 = tokens[0][1]
        data.append(tokens.pop(0))
        if(not tokens):
            error("Instruction missing comma and register!",line)
            return er
        if(tokens[0][0] != "<comma>"):
            if(tokens[0][0] != "<reg_even>"):
                error("Instruction has a bad rp register!",line)
                return er
            error("Instruction missing comma!",line)
            return er
        data.append(tokens.pop(0))
        if(not tokens):
            error("Instruction missing rp register!",line)
            return er
        if(tokens[0][0] != "<reg_even>"):
            error("Instruction has a bad rp register!",line)
            return er
        reg2 = tokens[0][1]
        data.append(tokens.pop(0))
        ##################################################
        # Code Generation
        instruction = table.mnm_r_rp[inst_str]
        instruction = format(int(reg1[1:]),'04b') + format(int(reg2[1:]),'04b') + instruction[8:]
        code_string = inst_str + " " + reg1 + ", " + reg2
        code.write_code(line,instruction,code_string,0)
        return data
    ##################################################
    # [mnm_rp]
    if(tokens[0][0] == "<mnm_rp>"):
        inst_str = tokens[0][1]
        data.append(tokens.pop(0))
        if(not tokens):
            error("Instruction missing rp register!",line)
            return er
        if(tokens[0][0] != "<reg_even>"):
            error("Instruction has a bad rp register!",line)
            return er
        reg1 = tokens[0][1]
        data.append(tokens.pop(0))
        ##################################################
        # Code Generation
        instruction = table.mnm_rp[inst_str]
        instruction = format(int(reg1[1:]),'04b') + instruction[4:]
        code_string = inst_str + " " + reg1
        code.write_code(line,instruction,code_string,0)
        return data
    ##################################################
    # [mnm_a] or [mnm_m]
    if(tokens[0][0] == "<mnm_a>" or tokens[0][0] == "<mnm_m>"):
        inst_str = tokens[0][1]
        inst_tkn = tokens[0][0]
        data.append(tokens.pop(0))
        if(not tokens):
            error("Instruction missing argument!",line)
            return er
        expr = parse_expr(*args)
        if(not expr):
            error("Instruction has bad argument!",line)
            return er
        elif(expr == er):
            return er
        data.append(expr)
        ##################################################
        # Code Generation
        instruction = ""
        code_string = inst_str + " " + expr_to_str(expr[1:])
        if(inst_tkn == "<mnm_a>"):
            instruction = table.mnm_a[inst_str]
            address = ""
            code.write_code(line,instruction,code_string,0)
            val = evaluate(expr[1:],symbols,code.code_address)
            if(len(val) == 1):
                numb = val[0]
                if(numb < 0 or numb > 65535):
                    error("Address must be >= 0 and <= 65535",line)
                    return er
                else:
                    address = format(numb,'016b')
                code.write_code(line,address,"",0)
            else:
                code.write_code(line,"AAAAAAAAAAAAAAAA","",[inst_tkn,val])
        else:
            instruction = table.mnm_m[inst_str]
            val = evaluate(expr[1:],symbols,code.code_address)
            if(len(val) == 1):
                numb = val[0]
                if(numb < 0 or numb > 16):
                    error("Mask must be >= 0 and <= 16",line)
                    return er
                else:
                    instruction = instruction[0:4] + format(numb,'04b') + instruction[8:]
                code.write_code(line,instruction,code_string,0)
            else:
                code.write_code(line,instruction,code_string,[inst_tkn,val])

        return data
    ##################################################
    # [mnm_n]
    if(tokens[0][0] == "<mnm_n>"):
        inst_str = tokens[0][1]
        data.append(tokens.pop(0))
        ##################################################
        # Code Generation
        instruction = table.mnm_n[inst_str]
        code.write_code(line,instruction,inst_str,0)
        return data

    return 0
##############################################################################################################
# Grammar:
#
# <line> ::= <lbl_def> [<drct>] [<code>]
#          | <drct> [<code>]
#          | <code>
#
# <code> ::= <mnm_r_i> <reg> <comma> <expr>
#          | <mnm_r_l> <reg> <comma> <expr>
#          | <mnm_r_r> <reg> <comma> <reg>
#          | <mnm_r> <reg>
#          | <mnm_r_rp> <reg> <comma> <reg_even>
#          | <mnm_rp> <reg_even>
#          | <mnm_a> <expr>
#          | <mnm_n>
#          | <mnm_m> <expr>
#
# <reg>  ::= <reg_even>
#          | <reg_odd>
#
# <expr> ::= [ (<plus> | <minus>) ] <numb> [ <selector> ] { (<plus> | <minus>) <numb> [ <selector> ]}
#
# <drct> ::= <drct_0> 
#          | <drct_1> <expr>
#          | <drct_2> <expr> <comma> <expr>
#          | <drct_m> <expr> { <comma>  <expr> }
#          | <drct_s> <quote> { <string_seg> } <quote>
#
# <numb> ::= <hex_num> | <dec_num> | <bin_num> | <symbol> | <lc>
#
##############################################################################################################
def parse_line(tokens, symbols, code, line):
    data = ["<line>"]
    er = ["<error>"]
    if(len(tokens) == 0):
        return 0
    ################################
    # [lbl_def]
    lbl_def = parse_lbl_def(tokens, symbols, code, line)
    if(lbl_def):
        if(lbl_def == er):
            return er
        data.append(lbl_def)
    ################################
    # [drct]
    drct = parse_drct(tokens, symbols, code, line)
    if(drct):
        if(drct == er):
            return er
        data.append(drct)
    ################################
    # [code]
    code = parse_code(tokens, symbols, code, line)
    if(code):
        if(code == er):
            return er
        data.append(code)
    ###############################
    # check to see that we have at
    # least one of lbl_def, drct,
    # or code
    if(len(data) < 2):
        tokens.pop(0)
        error("Bad Initial Identifier!",line)
        return er
    ###############################
    # check to see if we have any
    # tokens left
    if(len(tokens)):   
        error("Bad Final Identifier(s)! " + str(tokens),line)
        return er
    ###############################
    # everything's good
    return data
##############################################################################################################
# Second pass
def second_pass(symbols, code):
    i = 0
    while i < len(code.code_data):
        code_line = code.code_data[i]
        line = code_line[0]
        if(code_line[-1]):
            val = evaluate(code_line[-1][1],symbols,code_line[2])
            if(len(val) == 1):
                numb = val[0]
                ##################################################
                # [mnm_r_i] or [mnm_r_l]
                if(code_line[-1][0] == "<mnm_r_i>" or code_line[-1][0] == "<mnm_r_l>"):
                    instruction = code_line[4]
                    if(numb < -128 or numb > 255):
                        error("Argument must be >= -128 and <= 255",line)
                        return 0
                    else:
                        if(numb >= 0):
                            instruction = instruction[0:4] + format(numb,'08b') + instruction[12:]
                        else:
                            numb = 255 - abs(numb) + 1
                            instruction = instruction[0:4] + format(numb,'08b') + instruction[12:]
                        code_line[4] = instruction
                        code_line[-1] = 0
                ##################################################
                # [mnm_a]
                elif(code_line[-1][0] == "<mnm_a>"):
                    if(numb < 0 or numb > 65535):
                        error("Address must be >= 0 and <= 65535",line)
                        return 0
                    else:
                        code_line[4] = format(numb,'016b')
                        code_line[-1] = 0
                ##################################################
                # [mnm_m]
                elif(code_line[-1][0] == "<mnm_m>"):
                    instruction = code_line[4]
                    if(numb < 0 or numb > 16):
                        error("Mask must be >= 0 and <= 16",line)
                        return 0
                    else:
                        instruction = instruction[0:4] + format(numb,'04b') + instruction[8:]
            else:
                error("Expression relies on unresolved symbol!",line)
                return 0
        i += 1
    return 1
##############################################################################################################
def parse(lines, symbols, code):

    codeLines, tokenLines = lexer(lines)

    if(codeLines == 0):
        sys.exit(1)

    tree = []

    for tokens, line in zip(tokenLines, codeLines):
        parsedLine = parse_line(tokens, symbols, code, line)
        tree.append(parsedLine)
        if(parsedLine[0] == "<error>"):
            sys.exit(1)

    result = second_pass(symbols, code)
    if(not result):
        sys.exit(1)
##############################################################################################################
def output(code, file_name, args):
    code_file = open(file_name + "_code",'w') if file_name else sys.stdout
    data_file = open(file_name + "_data",'w') if file_name else sys.stdout
    if(args.debug == True):
        print("Line Number\tAddress\t\tLabel\t\tCode\t\t\tSource",file=code_file)
        print("----------------------------------------------------------------------------------------------------",file=code_file)
        for x in code.code_data:
            print(x[1] + "\t\t" + "0x"+x[2] + "\t\t" + x[3] + "\t\t" + "0b"+x[4] + "\t" + x[5],file=code_file)
        if(not file_name):
            print()
        print("Line Number\tAddress\t\tLabel\t\tData",file=data_file)
        print("----------------------------------------------------------------------------------------------------",file=data_file)
        for x in code.data_data:
            print(x[1] + "\t\t" + "0x"+x[2] + "\t\t" + x[3] + "\t\t" + "0x"+x[4],file=data_file)
    else:
        for x in code.code_data:
            print("0x"+x[2] + "," + "0b"+x[4],file=code_file)
        if(not file_name):
            print()
        for x in code.data_data:
            print("0x"+x[2] + "," + "0x"+x[4],file=data_file)
##############################################################################################################
# Main
code = Code()
symbols = Symbol()

discription = 'A simple 8085 assembler.'
p = argparse.ArgumentParser(description = discription)
p.add_argument("source", help="source file")
p.add_argument("-o", "--out", help="output file name (stdout, if not specified)")
p.add_argument("-d", "--debug", help="outputs debugging information", action="store_true")
args = p.parse_args();

if(args.source):
    outFile = args.source

parse(read(args.source),symbols,code)
output(code, (args.out if args.out else ""), args)