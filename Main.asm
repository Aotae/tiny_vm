.class Main:Obj
.method $constructor
    .local t,a
    enter

    const "hello\n"
    const "i'm pretty sure this should error since not an int, but I haven't gotten to it yet\n"
    new tester
    call tester:$constructor
    store a
    load a
    call tester:test
    store t
    const "\ndoing something along the lines of a.x.print() won't work right now\n"
    call String:print
    pop
    load t
    call Nothing:print
    pop
    const "\n"
    call String:print
    pop

    return 0

