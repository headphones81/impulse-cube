LIBIMPULSE=-limpulse -Wl,-rpath,.
BUILD_DIR=build
COPY_DEFAULTS=COPYING README

impulse: libimpulse python-impulse
	mkdir -p $(BUILD_DIR)/impulse
	cp $(COPY_DEFAULTS) $(BUILD_DIR)/impulse
	cp Impulse.py $(BUILD_DIR)/impulse
	cp $(BUILD_DIR)/libimpulse/libimpulse.so $(BUILD_DIR)/impulse/
	cp $(BUILD_DIR)/python-impulse/impulse.so $(BUILD_DIR)/impulse/

test-libimpulse: libimpulse
	mkdir -p $(BUILD_DIR)/test-libimpulse
	cp $(COPY_DEFAULTS) $(BUILD_DIR)/test-libimpulse
	cp $(BUILD_DIR)/libimpulse/libimpulse.so $(BUILD_DIR)/test-libimpulse/
	gcc -c src/test-libimpulse.c -o $(BUILD_DIR)/test-libimpulse/test-libimpulse.o
	gcc $(BUILD_DIR)/test-libimpulse/test-libimpulse.o -L$(BUILD_DIR)/test-libimpulse/ $(LIBIMPULSE)\
		-lpulse -lfftw3 -o $(BUILD_DIR)/test-libimpulse/test-libimpulse
	rm $(BUILD_DIR)/test-libimpulse/test-libimpulse.o

libimpulse:
	mkdir -p $(BUILD_DIR)/libimpulse
	cp $(COPY_DEFAULTS) $(BUILD_DIR)/libimpulse
	gcc -pthread -Wall -fPIC -c\
		src/Impulse.c -o $(BUILD_DIR)/libimpulse/Impulse.o
	gcc -pthread -lpulse -lfftw3 -shared -Wl,-soname,libimpulse.so -fPIC\
		$(BUILD_DIR)/libimpulse/Impulse.o -o $(BUILD_DIR)/libimpulse/libimpulse.so
	rm $(BUILD_DIR)/libimpulse/Impulse.o

python-impulse: libimpulse
	mkdir -p $(BUILD_DIR)/python-impulse
	cp $(COPY_DEFAULTS) $(BUILD_DIR)/python-impulse
	cp $(BUILD_DIR)/libimpulse/libimpulse.so $(BUILD_DIR)/python-impulse/
	gcc -pthread -fno-strict-aliasing -DNDEBUG -g -fwrapv -O2 -Wall -Wstrict-prototypes -fPIC\
		-I/usr/include/python2.7 -c src/impulsemodule.c -o $(BUILD_DIR)/python-impulse/impulsemodule.o
	gcc -pthread -shared -Wl,-O1 -Wl,-Bsymbolic-functions -L$(BUILD_DIR)/python-impulse/ \
		$(BUILD_DIR)/python-impulse/impulsemodule.o $(LIBIMPULSE) -lpulse -lfftw3 \
        -o $(BUILD_DIR)/python-impulse/impulse.so
	rm $(BUILD_DIR)/python-impulse/impulsemodule.o

clean:
	rm -rf $(BUILD_DIR)
