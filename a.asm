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
y db 0
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
xor rdx, rdx
mov rax, 10
xor rdx, rdx
mov rcx, 2
idiv rcx
add rax, [a]
mov [x], rax
mov rax, 4
mov [x], rax
mov rax, -6
mov [a], rax
mov rax, [x]
mov [y], rax
mov rax, 20
mov [a], rax
_L1:
xor rax, rax
pop rbp
ret
