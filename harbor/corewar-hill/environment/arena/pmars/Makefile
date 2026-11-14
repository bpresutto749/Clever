# pMARS 0.9.4 (GPL v2, see COPYING), built in KotH-server mode: no debugger,
# no graphics. Same simulator semantics as the CodeClash build.
CC ?= gcc
CFLAGS = -O2 -DEXT94 -DSERVER -DPERMUTATE -DRWLIMIT
OBJ = pmars.o asm.o eval.o disasm.o cdb.o sim.o pos.o clparse.o global.o token.o str_eng.o
pmars: $(OBJ)
	$(CC) -o pmars $(OBJ)
%.o: %.c
	$(CC) $(CFLAGS) -c $<
clean:
	rm -f *.o pmars
