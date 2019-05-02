import sys
import platform
from inspect import getframeinfo, stack
from copy import deepcopy

system_platform = platform.system()

asmheader = "DEFAULT REL\nextern printf\nextern scanf\nextern fflush\nextern usleep\nglobal main\n"
main_entry = 'main:'
scanf_label = 'scanf'
printf_label = 'printf'
fflush_label = 'fflush'
sleep_label = 'usleep'
reg_order = ["rdi", "rsi", "rdx", "rcx"]
if system_platform == 'Darwin':
    asmheader = "DEFAULT REL\nextern _printf\nextern _scanf\nextern _fflush\nextern _usleep\nglobal _main\n"
    main_entry = '_main:'
    scanf_label = '_scanf'
    printf_label = '_printf'
    fflush_label = '_fflush'
    sleep_label = '_usleep'
    reg_order = ["rdi", "rsi", "rdx", "rcx"]
if system_platform == 'Windows':
    reg_order = ["rcx", "rdx", "r8", "r9"]

asmtext = "section .text\n"
asmdata = 'section .data\n'
asmleave = 'xor rax, rax\npop rbp\nret\n'


global_var = []
const_var = []

global_str_counter = 0
global_str = {}
global_if_counter = 0
str_prefix = '_LC'

lexer = None

def add_data(var_name, value):
    global asmdata
    asmdata += "%s db %s\n" % (var_name, value)


def add_text(cmd):
    global asmtext
    asmtext += cmd + '\n'


# init
# sys_input
add_data("_fmin", "\"%ld\", 0")
add_text("_input:")
add_text("push rbp")
add_text("mov rbp, rsp")
add_text("sub rsp, 32")
add_text("lea rax, [rbp - 8]")
add_text("mov %s, _fmin" % reg_order[0])
add_text("mov %s, rax" % reg_order[1])
add_text("call " + scanf_label)
add_text("mov rax, [rbp - 8]")
add_text("leave")
add_text("ret")

# add main label
add_text(main_entry)
add_text("push rbp")

cmp_symbol = ['=', '!=', '>', '<']

def multiple_stm_routine(stm1, stm2):
    statement_main(stm1)
    statement_main(stm2)

def statement_main(stm):
    try:
        if stm[0] == 'assign':
            assign_routine(stm[1],stm[2])
        elif stm[0] == 'const_assign':
            const_assign_routine(stm[1],stm[2])
        elif stm[0] == 'array':
            declare_arr(stm[1],stm[2])
        elif stm[0] == 'loop':
            loop_routine(stm[1],stm[2])
        elif stm[0] == 'cmp':
            cmp_routine(stm[1],stm[2])
        elif stm[0] == 'show':
            show_routine(stm[1])
        elif stm[0] == 'stmt_multi':
            multiple_stm_routine(stm[1],stm[2])
    except SystemExit:
        sys.exit(1)
    except:
        pass

def get_type(symbol):
    if type(symbol) is tuple:
        if symbol[0] == 'array':
            return 'ARRAY'
        return 'expression'
    # if symbol == 'array':
    #     return 'ARRAY'
    if symbol[0]=='\"':
        return 'STRING'
    try:
        int(symbol)
        return 'CONSTANT'
    except ValueError:
        return 'ID'


def get_var(symbol):
    if symbol not in global_var:
        global_var.append(symbol)
        add_data(symbol,0)
        # asmdata += "%s dq 0\n" % symbol
    # print_error("Use of undeclare variable %s" % symbol)
    return symbol


def get_str(text):
    # add_text("%s" %text)
    if text not in global_str:
        declare_string(text)
    return global_str[text]


def get_array_id(arr):
    get_var(arr[2])
    add_text('mov rbx, %s' % arr[1])
    add_text('mov rcx, [%s]' % arr[2])
    add_text('imul rcx, 8')
    add_text('add rbx, rcx')

def declare_var(var_name, value=0):
    global asmdata
    if var_name in global_var:
        print_error("Duplicate variable")
    else:
        global_var.append(var_name)
        val_type = get_type(value)
        if val_type == 'INPUT':
            asmdata += "%s dq 0\n" % var_name
            # input_routine()
            # add_text("mov [%s], rax" % var_name)
        elif val_type == 'CONSTANT':
            asmdata += "%s dq %s\n" % (var_name, value)
        elif val_type == 'ARRAY':
            asmdata += "%s dq 0\n" % var_name
            assign_routine(var_name, value)
        else:
            print_error('Declare variable with unsupport type.',
                        show_line=False)


def declare_string(text):
    global global_str_counter
    if text not in global_str:
        asm_symbol = str_prefix + str(global_str_counter)
        global_str[text] = asm_symbol
        _text = ''
        if '\\n' in text:
            texts = text.replace('"', '').split('\\n')
            for t in texts:
                if t:
                    _text += '"' + t + '", 10,'
            _text += ' 0'
        else:
            _text = text + ', 0'
        add_data(asm_symbol, _text)
        global_str_counter += 1


def declare_arr(var_name, args):
    global asmdata
    if var_name in global_var:
        print_error("Duplicate variable")
    else:
        global_var.append(var_name)
        if args[0] == 'argument':
            asmdata += "%s dq " % var_name
            while args[1] != None:
                asmdata += "%s ," % args[1]
                args = args[2]
        else:
            # var array with size
            asmdata += "%s times %s dq 0" % (var_name, args)
        asmdata += '\n'

def const_assign_routine(dest,source):
    d_type = get_type(dest)
    s_type = get_type(source)

    if s_type == 'CONSTANT':
        add_text('mov rax, ' + source)
    elif s_type == 'ID':
        get_var(source)
        add_text('mov rax, [%s]' % source)
    elif s_type == 'expression':
        expression_main(source)
    elif s_type == 'ARRAY':
        index_type = get_type(source[2]) #check structure
        get_var(source[1]) #check structure
        if index_type == 'ID':
            get_array_id(source)
            add_text('mov rax, [rbx]')
        elif index_type == 'CONSTANT':
            add_text('mov rax, [%s + %s * 8]' % (source[1], source[2]))

    if d_type == 'ARRAY':
        index_type = get_type(dest[2])
        if index_type == 'ID':
            get_array_id(dest)
            add_text('mov [rbx], rax')
        elif index_type == 'CONSTANT':
            add_text('mov [%s + %s * 8], rax' % (dest[1], dest[2]))
    else:
        get_var(dest)
        add_text('mov [%s], rax' % dest)

    const_var.append(dest)

def assign_routine(dest, source):
    d_type = get_type(dest)
    s_type = get_type(source)
    # check dest!=const_var
    if dest in const_var:
        print_error("Constant Variable Assigned")
        return

    if s_type == 'CONSTANT':
        add_text('mov rax, ' + source)
    elif s_type == 'ID':
        get_var(source)
        add_text('mov rax, [%s]' % source)
    elif s_type == 'expression':
        expression_main(source)
    elif s_type == 'ARRAY':
        index_type = get_type(source[2]) #check structure
        get_var(source[1]) #check structure
        if index_type == 'ID':
            get_array_id(source)
            add_text('mov rax, [rbx]')
        elif index_type == 'CONSTANT':
            add_text('mov rax, [%s + %s * 8]' % (source[1], source[2]))

    if d_type == 'ARRAY':
        index_type = get_type(dest[2])
        if index_type == 'ID':
            get_array_id(dest)
            add_text('mov [rbx], rax')
        elif index_type == 'CONSTANT':
            add_text('mov [%s + %s * 8], rax' % (dest[1], dest[2]))
    else:
        get_var(dest)
        add_text('mov [%s], rax' % dest)


def cmp_routine(exp, stm):
    global global_if_counter
    global_if_counter += 1
    exit_c = global_if_counter
    expression_main(exp)
    statement_main(stm)
    # if else_stm:
    #     offset = 1
    #     s = str(else_stm)
    #     offset += s.count("'else'")
    #     add_text("jmp _L%d" % (global_if_counter + offset))
    add_text("_L%d:" % exit_c)


# def else_routine(stm):
#     global global_if_counter
#     statement_main(stm[1])
#     global_if_counter += 1
#     add_text("_L%d:" % global_if_counter)


def while_routine(exp, stm):
    global global_if_counter
    loop_c = global_if_counter
    exit_c = loop_c + 1
    add_text("_L%d:" % loop_c)
    global_if_counter += 1
    expression_main(exp)
    global_if_counter += 1
    statement_main(stm)
    add_text("jmp _L%d" % loop_c)
    add_text("_L%d:" % exit_c)
    global_if_counter += 1

def expression_main(exp, count=0):
    t = exp[0]
    if t == '+':
        plus_routine(exp[1],exp[2],count)
    elif t == '-':
        minus_routine(exp[1],exp[2],count)
    elif t == '*':
        multiply_routine(exp[1],exp[2],count)
    elif t == '/':
        divide_routine(exp[1],exp[2],count)
    elif t == '%':
        mod_routine(exp[1],exp[2],count)

    # if t in cmp_symbol:
    #     cmp_main(exp) #error
    # else:
    #     switcher = {
    #         '+': plus_routine,
    #         '-': minus_routine,
    #         '*': multiply_routine,
    #         '/': divide_routine,
    #         '%': mod_routine
    #     }

    #     func = switcher[t]
    #     func(exp[1], exp[2], count)

def show_routine(arg):
    # reg_c = 1
    a = arg
    a_type = get_type(a)
    if a_type == 'CONSTANT':
        add_text("mov %s, %s" % (reg_order[1], a))
    elif a_type == 'ID':
        get_var(a)
        add_text("mov %s, [%s]" % (reg_order[1], a))
    elif a_type == 'STRING':
        get_var(a)
        add_text("mov %s, %s" % (reg_order[0], get_str(a[1:-1])))
    add_text("mov eax, 0")
    add_text("call " + printf_label)
    add_text("xor %s, %s" % (reg_order[0], reg_order[0]))
    add_text("call " + fflush_label)
    # reg_c = 1
    # while arg[1] != None:
    #     if arg[0] == 'argument':
    #         a = arg[1]
    #         a_type = get_type(a)
    #         if a_type == 'CONSTANT':
    #             add_text("mov %s, %s" % (reg_order[reg_c], a))
    #         elif a_type == 'ID':
    #             get_var(a)
    #             add_text("mov %s, [%s]" % (reg_order[reg_c], a))
    #         elif a_type == 'ARRAY':
    #             index_type = get_type(a[2])
    #             if index_type == 'ID':
    #                 get_array_id(a)
    #                 add_text('mov %s, [rbx]' % reg_order[reg_c])
    #             elif index_type == 'CONSTANT':
    #                 add_text('mov %s, [%s + %s * 8]' %
    #                          (reg_order[reg_c], a[1], a[2]))
    #         else:
    #             expression_main(arg[1])
    #             add_text("mov %s, rax" % reg_order[reg_c])
    #     reg_c += 1
    #     arg = arg[2]
    # add_text("mov %s, %s" % (reg_order[0], get_str(fmt)))
    # add_text("call " + printf_label)
    # add_text("xor %s, %s" % (reg_order[0], reg_order[0]))
    # add_text("call " + fflush_label)

def plus_routine(a, b, count=0):
    a_type = get_type(a)
    b_type = get_type(b)
    if a_type == 'CONSTANT':
        if count == 0:
            add_text("mov rax, %s" % a)
        else:
            add_text("add rax, " + a)
    elif a_type == 'ID':
        get_var(a)
        if count == 0:
            add_text("mov rax, [%s]" % a)
        else:
            add_text("add rax, [%s]" % a)
    elif a_type == 'expression':
        expression_main(a, count)
    elif a_type == 'ARRAY':
        index_type = get_type(a[2])
        if index_type == 'ID':
            get_array_id(a)
            if count == 0:
                add_text('mov rax, [rbx]')
            else:
                add_text('add rax, [rbx]')
        elif index_type == 'CONSTANT':
            if count == 0:
                add_text('mov rax, [%s + %s * 8]' % (a[1], a[2]))
            else:
                add_text('add rax, [%s + %s * 8]' % (a[1], a[2]))
    else:
        error_token()
    count += 1

    if b_type == 'CONSTANT':
        add_text("add rax, " + b)
    elif b_type == 'ID':
        get_var(b)
        add_text("add rax, [%s]" % b)
    elif b_type == 'expression':
        expression_main(b, count)
    elif b_type == 'ARRAY':
        index_type = get_type(b[2])
        if index_type == 'ID':
            get_array_id(b)
            add_text('add rax, [rbx]')
        elif index_type == 'CONSTANT':
            add_text('add rax, [%s + %s * 8]' % (b[1], b[2]))

    else:
        error_token()


def minus_routine(a, b, count=0):
    a_type = get_type(a)
    b_type = get_type(b)
    if a_type == 'CONSTANT':
        if count == 0:
            add_text("mov rax," + a)
        else:
            add_text("sub rax, " + a)
    elif a_type == 'ID':
        get_var(a)
        if count == 0:
            add_text("mov rax, [%s]" % a)
        else:
            add_text("sub rax, [%s]" % a)
    elif a_type == 'expression':
        expression_main(a, count)
    elif a_type == 'ARRAY':
        index_type = get_type(a[2])
        if index_type == 'ID':
            get_array_id(a)
            if count == 0:
                add_text('mov rax, [rbx]')
            else:
                add_text('sub rax, [rbx]')
        elif index_type == 'CONSTANT':
            if count == 0:
                add_text('mov rax, [%s + %s * 8]' % (a[1], a[2]))
            else:
                add_text('sub rax, [%s + %s * 8]' % (a[1], a[2]))
    else:
        error_token()

    count += 1

    if b_type == 'CONSTANT':
        add_text("sub rax, " + b)
    elif b_type == 'ID':
        get_var(b)
        add_text("sub rax, [%s]" % b)
    elif b_type == 'expression':
        expression_main(b, count)
    elif b_type == 'ARRAY':
        index_type = get_type(b[2])
        if index_type == 'ID':
            get_array_id(b)
            add_text('sub rax, [rbx]')
        elif index_type == 'CONSTANT':
            add_text('sub rax, [%s + %s * 8]' % (b[1], b[2]))
    else:
        error_token()


def multiply_routine(a, b, count=0):
    a_type = get_type(a)
    b_type = get_type(b)
    if a_type == 'CONSTANT':
        if count == 0:
            add_text("mov rax," + a)
        else:
            add_text("imul rax, " + a)
    elif a_type == 'ID':
        get_var(a)
        if count == 0:
            add_text("mov rax, [%s]" % a)
        else:
            add_text("imul rax, [%s]" % a)
    elif a_type == 'expression':
        expression_main(a, count)
    elif a_type == 'ARRAY':
        index_type = get_type(a[2])
        if index_type == 'ID':
            get_array_id(a)
            if count == 0:
                add_text('mov rax, [rbx]')
            else:
                add_text('imul rax, [rbx]')
        elif index_type == 'CONSTANT':
            if count == 0:
                add_text('mov rax, [%s + %s * 8]' % (a[1], a[2]))
            else:
                add_text('imul rax, [%s + %s * 8]' % (a[1], a[2]))
    else:
        error_token()
    count += 1

    if b_type == 'CONSTANT':
        add_text("imul rax, %s" % b)
    elif b_type == 'ID':
        get_var(b)
        add_text("imul rax, [%s]" % b)
    elif b_type == 'expression':
        expression_main(b, count)
    elif b_type == 'ARRAY':
        index_type = get_type(b[2])
        if index_type == 'ID':
            get_array_id(b)
            add_text('imul rax, [rbx]')
        elif index_type == 'CONSTANT':
            add_text('imul rax, [%s + %s * 8]' % (b[1], b[2]))
    else:
        error_token()


def divide_routine(a, b, count=0):
    a_type = get_type(a)
    b_type = get_type(b)
    add_text('xor rdx, rdx')
    if a_type == 'CONSTANT':
        if count == 0:
            add_text('mov rax, ' + a)
        else:
            add_text('mov rcx, ' + a)
            add_text('idiv rcx')
    elif a_type == 'ID':
        get_var(a)
        if count == 0:
            add_text('mov rax, [%s]' % a)
        else:
            add_text('mov rcx, [%s]' % a)
            add_text('idiv rcx')
    elif a_type == 'expression':
        expression_main(a, count)
    elif a_type == 'ARRAY':
        index_type = get_type(a[2])
        if index_type == 'ID':
            get_array_id(a)
            if count == 0:
                add_text('mov rax, [rbx]')
            else:
                add_text('mov rcx, [rbx]')
                add_text('idiv rcx')
        elif index_type == 'CONSTANT':
            if count == 0:
                add_text('mov rax, [%s + %s * 8]' % (a[1], a[2]))
            else:
                add_text('mov rcx, [%s + %s * 8]' % (a[1], a[2]))
                add_text('idiv rcx')
    else:
        error_token()
    count += 1

    add_text('xor rdx, rdx')
    if b_type == 'CONSTANT':
        add_text('mov rcx, ' + b)
        add_text('idiv rcx')
    elif b_type == 'ID':
        get_var(b)
        add_text('mov rcx, [%s]' % b)
        add_text('idiv rcx')
    elif b_type == 'expression':
        expression_main(b, count)
    elif b_type == 'ARRAY':
        index_type = get_type(b[2])
        if index_type == 'ID':
            get_array_id(b)
            add_text('idiv rcx')
        elif index_type == 'CONSTANT':
            add_text('mov rcx, [%s + %s * 8]' % (b[1], b[2]))
            add_text('idiv rcx')
    else:
        error_token()


def mod_routine(a, b, count=0):
    a_type = get_type(a)
    b_type = get_type(b)
    add_text('xor rdx, rdx')
    if a_type == 'CONSTANT':
        if count == 0:
            add_text('mov rax, ' + a)
        else:
            add_text('mov rcx, ' + a)
            add_text('idiv rcx')
            add_text('mov rax, rdx')
    elif a_type == 'ID':
        get_var(a)
        if count == 0:
            add_text('mov rax, [%s]' % a)
        else:
            add_text('mov rcx, [%s]' % a)
            add_text('idiv rcx')
            add_text('mov rax, rdx')
    elif a_type == 'expression':
        expression_main(a, count)
    elif a_type == 'ARRAY':
        index_type = get_type(a[2])
        if index_type == 'ID':
            get_array_id(a)
            if count == 0:
                add_text('mov rax, [rbx]')
            else:
                add_text('mov rcx, [rbx]')
                add_text('idiv rcx')
                add_text('mov rax, rdx')
        elif index_type == 'CONSTANT':
            if count == 0:
                add_text('mov rax, [%s + %s * 8]' % (a[1], a[2]))
            else:
                add_text('mov rcx, [%s + %s * 8]' % (a[1], a[2]))
                add_text('idiv rcx')
                add_text('mov rax, rdx')
    else:
        error_token()

    count += 1

    add_text('xor rdx, rdx')
    if b_type == 'CONSTANT':
        add_text('mov rcx, ' + b)
        add_text('idiv rcx')
        add_text('mov rax, rdx')
    elif b_type == 'ID':
        get_var(b)
        add_text('mov rcx, [%s]' % b)
        add_text('idiv rcx')
        add_text('mov rax, rdx')
    elif b_type == 'expression':
        expression_main(b, count)
    elif b_type == 'ARRAY':
        index_type = get_type(b[2])
        if index_type == 'ID':
            get_array_id(b)
            add_data('mov rcx, [rbx]')
            add_text('idiv rcx')
            add_text('mov rax, rdx')
        elif index_type == 'CONSTANT':
            add_text('mov rcx, [%s + %s * 8]' % (b[1], b[2]))
            add_text('idiv rcx')
            add_text('mov rax, rdx')
    else:
        error_token()

def cmp_main(cmp_e):
    global global_if_counter
    t = cmp_e[0]
    a = cmp_e[1]
    b = cmp_e[2]
    type_a = get_type(a)
    type_b = get_type(b)
    if type_a == 'expression':
        expression_main(a)
    elif type_a == 'IDENTIFIER':
        get_var(a)
        add_text("mov rax, [%s]" % a)
    elif type_a == 'CONSTANT':
        add_text("mov rax, %s" % a)
    elif type_a == 'ARRAY':
        index_type = get_type(a[2])
        get_var(a[1])
        if index_type == 'ID':
            get_array_id(a)
            add_text('mov rax, [rbx]')
        elif index_type == 'CONSTANT':
            add_text('mov rax, [%s + %s * 8]' % (a[1], a[2]))
        else:
            error_token()

    if type_b == 'expression':
        expression_main(b)
    elif type_b == 'ID':
        get_var(b)
        add_text("mov rbx, [%s]" % b)
    elif type_b == 'CONSTANT':
        add_text("mov rbx, %s" % b)
    elif type_b == 'ARRAY':
        index_type = get_type(b[2])
        if index_type == 'ID':
            get_array_id(b)
            add_text('mov rbx, [rbx]')
        elif index_type == 'CONSTANT':
            add_text('mov rbx, [%s + %s * 8]' % (b[1], b[2]))
        else:
            error_token()

    if t != '&&':
        add_text("cmp rax, rbx")
    switcher = {
        '=': equal_routine,
        '>': greater_routine,
        '<': less_routine,
        '!=': not_equal_routine
    }
    func = switcher[t]
    func()

def less_routine():
    add_text("jge _L%d" % global_if_counter)


def greater_routine():
    add_text("jle _L%d" % global_if_counter)


def not_equal_routine():
    add_text("je _L%d" % global_if_counter)

def equal_routine():
    add_text("jne _L%d" % global_if_counter)

def error_token():
    print_error("Unexpected token")

def print_error(error_str, show_line=True):
    if show_line:
        print("ERROR : %s At line %d" % (error_str, lexer.lineno)) #line number incorrect
    else:
        print("ERROR : %s" % error_str)
    sys.exit(1)