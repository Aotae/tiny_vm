.class tester:Obj
.field x
.method test forward
.method $constructor
.args x
    enter
    load x
    load $
    store_field $:x
    return 1

.method test
    enter
    load $
    load_field $:x
    return 0
