LIBIMPULSE=-limpulse -Wl,-rpath,.
LIBS=-lpulse -lfftw3
BUILD_DIR=build
COPY_DEFAULTS=COPYING README
PY_INCLUDE=/usr/include/python2.7

impulse: python-impulse
	cp src/impulse-cli.py $(BUILD_DIR)

test-libimpulse: libimpulse
	gcc src/test-libimpulse.c -L$(BUILD_DIR) $(LIBIMPULSE)\
		$(LIBS) -o $(BUILD_DIR)/test-libimpulse
	chmod u+x $(BUILD_DIR)/test-libimpulse

libimpulse:
	gcc -pthread -Wall -shared -Wl,-soname,libimpulse.so -fPIC\
		src/Impulse.c $(LIBS) -o $(BUILD_DIR)/libimpulse.so

python-impulse: libimpulse
	gcc -pthread -fno-strict-aliasing -DNDEBUG -g -fwrapv -O2 -Wall -Wstrict-prototypes -fPIC\
		-shared -Wl,-O1 -Wl,-Bsymbolic-functions -I$(PY_INCLUDE) src/impulsemodule.c\
		-L$(BUILD_DIR) $(LIBIMPULSE) $(LIBS) \
		-o $(BUILD_DIR)/impulse.so

clean:
	rm -rf $(BUILD_DIR)/test-libimpulse
	rm -rf $(BUILD_DIR)/libimpulse.so
	rm -rf $(BUILD_DIR)/impulse.so
	rm -rf $(BUILD_DIR)/impulse-cli.py
