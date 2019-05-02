DEFAULT REL
extern printf
extern scanf
extern fflush
extern usleep
global main
section .data
_fmin db "%ld", 0
x db 0
y db 0
a db 0
i db 0
section .text
_input:
push rbp
mov rbp, rsp
sub rsp, 32
lea rax, [rbp - 8]
mov rcx, _fmin
mov rdx, rax
call scanf
mov rax, [rbp - 8]
leave
ret
main:
push rbp
mov rax, [x]
mov [y], rax
mov rax, [x]
mov rbx, [y]
cmp rax, rbx
je _L1
mov rax, 20
mov [a], rax
_L1:
mov rax, [x]
mov rbx, [y]
cmp rax, rbx
je _L2
mov rax, 20
mov [a], rax
_L2:
mov rax, 0
mov [i], rax
mov rax, [i]
mov rbx, 2
_L3:
cmp rax, rbx
jge _L4
add rax, -4
push rax
mov rax, 0
mov [i], rax
mov rax, [i]
mov rbx, 2
_L5:
cmp rax, rbx
jge _L6
add rax, -2
push rax
mov rax, 1
mov [y], rax
pop rax
jmp _L5
_L6:
mov rax, 1
mov [x], rax
pop rax
jmp _L3
_L4:
xor rax, rax
pop rbp
ret
