CC = gcc
TARGET = cemon
OBJECT = cemon.o
SOURCE = cemon.c
CFLAGS = -Wall -O3 `curl-config --cflags` `pkg-config --cflags jansson`
LDLIBS = `curl-config --libs` `pkg-config --libs jansson`

.PHONY: all
all: CFLAGS += -DNDEBUG
all: $(TARGET)

.PHONY: debug
debug: $(TARGET)

$(TARGET): $(OBJECT)

$(OBJECT): $(SOURCE)

.PHONY: clean
clean:
	$(RM) $(TARGET) $(OBJECT)
