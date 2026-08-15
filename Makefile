.PHONY: run smoke ci hardware

PYTHON ?= python3
PROFILE_TESTS = $(PYTHON) -m unittest -v test_app.py

define RUN_PROFILE
	command='$(PROFILE_TESTS)'; \
	echo 'profile=$(1) command='$$command; \
	setsid timeout --kill-after=5s 120s sh -c "$$command" & \
	pid=$$!; \
	wait $$pid; rc=$$?; \
	kill -- -$$pid 2>/dev/null || true; \
	echo 'profile=$(1) rc='$$rc; \
	exit $$rc
endef

run:
	python3 app.py

smoke:
	$(call RUN_PROFILE,smoke)

ci: smoke

hardware:
	$(call RUN_PROFILE,hardware)
