.class tester:Obj
.field x
.method test forward

.method $constructor
.args x,y
load x
load $
store_field $:x
.method test
enter
load $
load_field $:x
return 0


