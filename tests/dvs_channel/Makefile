input:	clean preprocess

preprocess:
	gmsh -2 src/channel.geo -o src/channel.msh

run:
	python ../../firedrake_fluids/shallow_water.py dvs_channel.swml

clean:
	rm -f *.pvd *.pvtu *.vtu *.stat *_A* *_B* *_C* *.log matrix* *~ *.pyc nohup.out *.node *.ele *.edge
