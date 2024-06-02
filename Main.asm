.class Main:Obj
.method $constructor
.local y,z,a,x,b
const false
store y
const true
store x
const false
store z
const 4
store a
const 2
store b
load y
jump_if val_true_0
const true
jump end_not_0
val_true_0:
const false
end_not_0:

jump_ifnot and_false_0
load x
jump_ifnot and_false_0
const true
jump and_end_0
and_false_0:
const false
and_end_0:

jump_ifnot else_0
jump then_0
then_0:
const "(not y) is true and x is true -> x=true, y = false\n"
call String:print
pop

jump endif_0
else_0:
const "hooray x is true therefore not x works\n"
call String:print
pop

endif_0:

load x
jump_ifnot and_false_1
load y
jump_ifnot and_false_1
const true
jump and_end_1
and_false_1:
const false
and_end_1:

jump_ifnot else_1
jump then_1
then_1:
const "while x is true y is not this shouldn't print\n"
call String:print
pop

jump endif_1
else_1:
const "expected\n"
call String:print
pop

endif_1:

const 0
const 2
load b
call Int:minus
call Int:equals

jump_ifnot else_2
jump then_2
then_2:
const "b is equal to 2\n"
call String:print
pop

jump endif_2
else_2:
endif_2:

load a
load b
call Int:less

jump_ifnot else_3
jump then_3
then_3:
const "b is less than 4\n"
call String:print
pop

jump endif_3
else_3:
endif_3:

load b
load a
call Int:less

jump_ifnot else_4
jump then_4
then_4:
const "b is greater than a\n"
call String:print
pop

jump endif_4
else_4:
const "b is not greater than a\n"
call String:print
pop

endif_4:

load a
load b
call Int:less
jump_if val_true_1
const true
jump end_not_1
val_true_1:
const false
end_not_1:

jump_ifnot and_false_2
load x
jump_ifnot and_false_2
const true
jump and_end_2
and_false_2:
const false
and_end_2:

jump_ifnot else_5
jump then_5
then_5:
const "b is not less than a, and x is true\n"
call String:print
pop

jump endif_5
else_5:
const "b<a is true therefore (not b < a) is true and x is true\n"
call String:print
pop

endif_5:

load x
jump_if or_true_0
load y
jump_if or_true_0
const false
jump or_end_0
or_true_0:
const true
or_end_0:


jump_ifnot else_6
jump then_6
then_6:
const "either x or y is true\n"
call String:print
pop

jump endif_6
else_6:
endif_6:

load z
jump_if or_true_1
load y
jump_if or_true_1
const false
jump or_end_1
or_true_1:
const true
or_end_1:


jump_ifnot else_7
jump then_7
then_7:
const "either z or y is true\n"
call String:print
pop

jump endif_7
else_7:
endif_7:

load x
jump_if or_true_2
load y
jump_if val_true_2
const true
jump end_not_2
val_true_2:
const false
end_not_2:

jump_if or_true_2
const false
jump or_end_2
or_true_2:
const true
or_end_2:


jump_ifnot else_8
jump then_8
then_8:
const "either x or not y is true\n"
call String:print
pop

jump endif_8
else_8:
endif_8:


return 0

