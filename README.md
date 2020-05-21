# gpptoxunit
small personal project reading output of g++ compilation and translate it to xunit

## Usage

for now, I just have a special rule in makefiles:

```Makefile
%.o: %.cpp
	@$(CC) $(CFLAGS) $(INCLUDES) -c -o /dev/null $<

# static analysis
lint: $(OBJS)
```

and run:
```bash
make -k lint 2> error.log
gpptoxunit.py -o cpptojunit.xml error.log
```
to make the report
