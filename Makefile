LIBIMPULSE=-limpulse -Wl,-rpath,.
LIBS=-lpulse -lfftw3
PY_INCLUDE=$(shell python-config --cflags)

all: python-impulse

test-libimpulse: libimpulse
	gcc impulse-src/test-libimpulse.c -L. $(LIBIMPULSE) $(LIBS) -o test-libimpulse
	chmod u+x test-libimpulse

libimpulse:
	gcc -pthread -Wall -shared -Wl,-soname,libimpulse.so -fPIC\
		impulse-src/Impulse.c $(LIBS) -o libimpulse.so

python-impulse: libimpulse
	gcc -pthread -fno-strict-aliasing -DNDEBUG -g -fwrapv -O2 -Wall -Wstrict-prototypes -fPIC\
		-shared -Wl,-O1 -Wl,-Bsymbolic-functions $(PY_INCLUDE) impulse-src/impulsemodule.c\
		-L. $(LIBIMPULSE) $(LIBS) -o ./impulse.so

clean:
	rm -rf test-libimpulse
	rm -rf libimpulse.so
	rm -rf impulse.so
