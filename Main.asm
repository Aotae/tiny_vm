.class Main:Obj
.method $constructor
.local z,x,a,c,y,b
const 2
store x
const 10
store z
const true
store y
load y

jump_ifnot else_0
jump then_0
then_0:
const "hello x is less than z\n"
call String:print
pop

jump endif_0
else_0:
const "hello x is not less than z\n"
call String:print
pop
load z
load x
call Int:less

jump_ifnot else_1
jump then_1
then_1:
const "x is greater than z\n"
call String:print
pop

jump endif_1
else_1:
endif_1:


endif_0:

load z
store a
load x
store b
load b
call Int:print
pop
.class tester
.field y
.field x

.method $constructor
.args x
load x
load $
store_field $:x
const 42
load $
store_field $:42







store c
const 12
load c
store_field $:12
load c
call Int:print
pop

return 0

