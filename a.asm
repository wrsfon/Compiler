DEFAULT REL
extern printf
extern scanf
extern fflush
extern usleep
global main
section .data
_fmin db "%ld", 0
a db 0
x db 0
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
mov rax, 2
add rax, 1
imul rax, 3
mov [a], rax
mov rax, 3
add rax, 3
xor rdx, rdx
mov rcx, 3
idiv rcx
xor rdx, rdx
mov rcx, 5
idiv rcx
mov [x], rax
xor rax, rax
pop rbp
ret
