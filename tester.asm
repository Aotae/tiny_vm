.class tester:Obj
.field x
.field y
.method test forward

.method $constructor
.args x
load x
load $
store_field $:x
const 42
load $
store_field $:y
.method test
enter
load $
load_field $:x
return 0

