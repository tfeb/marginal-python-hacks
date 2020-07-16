# The only purpose of this is to support testing everything at once:
# for any other operation you need to look in subdirectories.
#

SUBDIRS		= safer-shell-commands
TARGET		= test

.PHONY: test $(SUBDIRS)

test: TARGET=test
test: $(SUBDIRS)

$(SUBDIRS):
	@echo "* $(TARGET) in $@"
	@$(MAKE) -C $@ $(TARGET)
