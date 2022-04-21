all:
	# tracing-based JIT
	python3 bvm.py -f test/demo.json 42
	# optimize the trace
	python3 ../Lesson3/lvn.py -f trace.json | python3 ../Lesson3/dce.py | python3 ../Lesson3/lvn.py | python3 ../Lesson3/dce.py > trace.opt.json
	# insert traced optimized path
	python3 transform.py test/demo.json trace.opt.json
	# reexecute optimized program
	python3 bvm.py -f test/demo.opt.json 42