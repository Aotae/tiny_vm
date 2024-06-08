.class tester:Obj
.field x
.field y
.field c
.method test forward
.method $constructor
.args x,y
    enter
    load x
    load $
    store_field $:x
    load y
    load $
    store_field $:y
    load $
    load_field $:y
    call String:print
    pop
    load $
    load_field $:y
    load $
    load_field $:x
    call Obj:minus
    load $
    store_field $:c
    load $
    load_field $:c
    call Obj:print
    pop
    const "tester constructor is being called\n"
    call String:print
    pop
    load $
return 2

.method test
    enter
    const "test is being called\n"
    call String:print
    pop
    load $
    load_field $:x
    return 0
