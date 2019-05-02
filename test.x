x -> 4.
a -> 0x6.
y -> x.
cmp x != y {
    a->20.
}.
cmp x != y {
    a->20.
}.
loop i->(0,2,-4)
    loop i->(0,2,-2)
        y->1.
    fin.
    x->1.
fin.