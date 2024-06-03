.class Main:Obj
.method $constructor
.local a,t

const 42
new tester
call tester:$constructor
store a
load a
call tester:print
pop
const "\n"
call String:print
pop
load a
load_field tester:x
store t
load t
call Int:print
pop
const "\n"
call String:print
pop
const "\n"
call String:print
pop

return 0

