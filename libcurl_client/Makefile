CC = gcc
TARGET = cemon
OBJECT = cemon.o
SOURCE = cemon.c
CFLAGS = -Wall `curl-config --cflags` `pkg-config --cflags jansson`
LDLIBS = `curl-config --libs` `pkg-config --libs jansson`

.PHONY: all
all: CFLAGS += -O3 -DNDEBUG
all: $(TARGET)

.PHONY: debug
debug: CFLAGS += -g
debug: $(TARGET)

$(TARGET): $(OBJECT)

$(OBJECT): $(SOURCE)

.PHONY: clean
clean:
	$(RM) $(TARGET) $(OBJECT)
