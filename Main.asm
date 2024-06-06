.class Main:Obj
.method $constructor
    .local t,a
    enter

    const "hello"
    new tester
    call tester:$constructor
    store a
    load a
    call tester:test
    store t
    load t
    call String:print
    pop
    const "\n"
    call String:print
    pop

    return 0

