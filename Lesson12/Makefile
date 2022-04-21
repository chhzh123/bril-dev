all:
	# tracing-based JIT
	python3 bvm.py -f test/demo.json 42
	# optimize the trace
	python3 ../Lesson3/lvn.py -f trace.json | python3 ../Lesson3/dce.py | python3 ../Lesson3/lvn.py | python3 ../Lesson3/dce.py > trace.opt.json
	# insert traced optimized path
	python3 transform.py test/demo.json trace.opt.json
	# reexecute optimized program
	python3 bvm.py -f test/demo.opt.json 42

bubblesort:
	# tracing-based JIT
	python3 bvm.py -f test/bubblesort.json 5 10 7 5 1 3
	# optimize the trace
	python3 ../Lesson3/lvn.py -f trace.json | python3 ../Lesson3/dce.py | python3 ../Lesson3/lvn.py | python3 ../Lesson3/dce.py > bubblesort.opt.json
	# insert traced optimized path
	python3 transform.py test/bubblesort.json bubblesort.opt.json
	# reexecute optimized program
	python3 bvm.py -f test/bubblesort.opt.json 5 10 7 5 1 3

loop:
	# tracing-based JIT
	python3 bvm.py -f test/loopcond.json
	# optimize the trace
	python3 ../Lesson3/lvn.py -f trace.json | python3 ../Lesson3/dce.py | python3 ../Lesson3/lvn.py | python3 ../Lesson3/dce.py > loopcond.opt.json
	# insert traced optimized path
	python3 transform.py test/loopcond.json loopcond.opt.json
	# reexecute optimized program
	python3 bvm.py -f test/loopcond.opt.json