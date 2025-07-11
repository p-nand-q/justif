# Justif & Recursion

Justif & Recursion, or, short, JUSTIF, is a small programming language with the following features:

There is just IF and recursion for implementing program logic. There are no explicit loop constructs. The code is not self-modifying, you must use recursion to implement loops.

The interpretation of syntax characters is context-sensitive. For example, "=2" means recurse self with argument 2, while ".1==2" means assign the result of recursing with argument 2 to the address 1.

Comments can be placed anywhere in the code: all uppercase or lowercase letters plus space and newline are considered whitespaces.

Here is a Hello, World-type program in JUSTIF:

```
~1?.0=_,.$="Hello, World",=2:~2?.1!.0?>.1!.0,._+1,=2:0:0
```

And here is an example that will print the first 10 fibonacci numbers.

```
~1?.2=$,.0=1,.3=$,=2:~_?+._=10?!.0,.1=.$,._+.3,.0=.$,.$=.1,.2+$,=_:0:_
```

Finally, here is atoi in good JUSTIF style:

```
~1?.2="1182",.0=_,.1=$,=3,!.$:~2?.3=.$!.0,*.$=47?+.3=58:0:~3?=2?.$-48,.1*10,.$+.3,.0+1,=3:0:I AM JUSTIF_
```

## Go Implementation

This is a Go implementation of the JUSTIF interpreter.

### Installation

```bash
go install github.com/p-nand-q/justif@latest
```

Or build from source:

```bash
git clone https://github.com/p-nand-q/justif
cd justif
go build -o justif
```

### Basic Usage

```bash
justif <filename.justif>
```

### OPP Integration

JUSTIF includes built-in support for OPP (Obfuscated Pre-Processor), allowing you to use macros, conditional compilation, and other preprocessor features:

```bash
# Automatically detect OPP from .opp.justif extension
justif examples/hello_opp.opp.justif

# Explicitly enable OPP preprocessing
justif -opp myfile.justif

# Define preprocessor variables
justif -D DEBUG examples/hello_opp.opp.justif

# Multiple defines
justif -D DEBUG -D VERSION=2 myfile.justif
```

When OPP is enabled, your source is preprocessed first, then the resulting pure JUSTIF code is interpreted. This two-pass approach ensures complete compatibility between OPP's syntax and JUSTIF's unique comment rules (where all letters are whitespace).

## The JUSTIF tutorial

The following sections describe how to use JUSTIF for programming.

### Numbers, Whitespaces and Comments

Numbers are just plain decimal numbers. A future version of JUSTIF might feature ENHADINUMs support, but right now it doesn't. Whitespaces are SPACE, TAB, NEWLINE plus all uppercase and lowercase letters. This means there are no explicit comment specifiers needed. For example, you can modify the HELLO-WORLD example from above like this:

```
IF CALLED BY INDEX ONE ~1 ? 
DO 
    ASSIGN ZERO TO MEMORY CELL ZERO .0=_,
    ASSIGN STRING TO MEMORY CELL ONE .$="Hello, World",
    CALL SELF RECURSIVELY WITH INDEX TWO =2:
IF CALLED BY INDEX TWO ~2 ? 
    IF CELL ONE INDEXED BY CELL ZERO IS NOT NULL .1!.0 ? 
    DO  
        PRINT CHARACTER IN CELL ONE INDEXED BY CELL ZERO >.1!.0,
        INCREMENT CELL ZERO BY ONE ._+1,
        CALL SELF RECURSIVELY WITH INDEX TWO =2:0
ELSE DO NOTHING :0
```

which just might make the program more understandable. Furthermore, for perl programmers deciding to switch to JUSTIF, there are two helper tokens

- `_` - use the last number
- `$` - use the number used before the last number

For example, the expression

```
!.0,.1=.0,.1+.3
```

can be written as

```
!.0,.1=.$,._+.3
```

where the `$` is replaced by 0 because it is the number used before the last number, and `_` is replaced by 1 because it is the last number used. (Note that `$` and `_` do not change the last number used).

**Implementation note**: The `_` and `$` tokens track numbers globally throughout both parsing and execution. They are initialized to -1 and update whenever a literal number is encountered.

### Accessing Memory

JUSTIF has no variables, just a large memory array. Memory cells can contain either numbers or strings, nothing else. Memory cells are directly addressed with an index:

- `.0` - cell 0
- `.1` - cell 1
- ...
- `.n` - cell n

You can access memory indirect by using the syntax

- `..0` - cell indexed by cell 0
- `..1` - cell indexed by cell 1
- ...
- `..n` - cell indexed by cell n

**Implementation note**: Indirect memory access is implemented by using another memory cell reference as the index. For example, if cell 5 contains the value 10, then `..5` accesses cell 10.

If the cell contains a string, you can access the characters of the string (as integer values) with the syntax

- `.0!0` - character 0 of string at cell 0
- `.0!1` - character 1 of string at cell 0
- ...
- `.0!n` - character n of string at cell 0
- `.1!0` - character 0 of string at cell 1
- ...
- `.n!0` - character 0 of string at cell n

You can access the characters in a string cell indirectly by using the syntax

- `.0!.1` - character indexed by cell 1 of string at cell 0
- `.0!.2` - character indexed by cell 2 of string at cell 0
- ...
- `.0!.n` - character indexed by cell n of string at cell 0

**Implementation note**: Strings are stored internally as arrays of integers with a null terminator (0). When accessing characters beyond the string length, the result is 0.

You can do the following operations on cells

- `CELL '=' VALUE` - assign value to cell
- `CELL '+' VALUE` - increment cell by value
- `CELL '-' VALUE` - subtract value from cell
- `CELL '*' VALUE` - multiply cell by value
- `CELL '/' VALUE` - divide cell by value

Values can be either integers, or strings, or other memory cells. Here are some example expressions:

- `.0=42` - assign the number 42 to the cell 0
- `.0="Test"` - assign the string "Test" to the cell 0. 
- `.1=..0` - assign the cell indexed by the cell 0 to the cell 1

### Doing I/O

There are two output commands

- `>cell` - output cell as character
- `!cell` - output cell as digit

Here are some examples

- `!42` - print 42
- `!.0` - print the cell 0 as integer
- `>.0` - print the cell 0 as character
- `!..0` - print the cell indexed by the cell 0 as integer
- `>.0!.1` - print the cell 0 indexed by the cell 1 as character

**Implementation note**: The `!` command outputs integers with a newline, while `>` outputs characters without a newline.

There is an input command, "<", that is currently not supported.

### Comparison

You can compare a memory cell to another memory cell or to an integer constant by using the syntax

- `+cell=value` - check if the cell is less than the value
- `-cell=value` - check if the cell is equal to the value
- `*cell=value` - check if the cell is larger than the value
- `/cell=value` - check if the cell is not equal to the value

Here are some examples

- `+.1=10` - check if the cell 1 is less than 10
- `+.1=.2` - check if the cell 1 is less than the cell 2
- `+.1==2` - check if the cell 1 is less than the result of calling self recursively with index 2
- `-.1=10` - check if the cell 1 is equal to 10
- `*.1=10` - check if the cell 1 is greater than 10
- `/.1=10` - check if the cell 1 is not equal to 10

**Implementation note**: The comparison value can be a recursion expression (=n), which executes the recursion and uses its return value for comparison.

You can check if the current index is a specified value by using the syntax

- `~1` - check if the index is 1
- `~2` - check if the index is 2
- ...
- `~n` - check if the index is n
- `~.0` - check if the index is the cell 0
- `~.1` - check if the index is the cell 1
- ...
- `~.n` - check if the index is the cell n

**Implementation note**: `~_` checks if the current recursion index equals the last number used, which is useful for dynamic recursion patterns.

### The IF command

The IF-command is the only traditional logic construct in JUSTIF. It works exactly like the ?: operator in C. Example:

```
.0?.1=1:.1=2 - if .0 is true, assign 1 to .1, otherwise assign 2 to .1
```

You can use the comparison operators described above. Instructions can be grouped by using commas. Example:

```
.0?.1=1,.2=1:0 - if .0 is true, assign 1 to .1, assign 1 to .2, otherwise do nothing.
```

**Implementation note**: 
- A bare number (like 0) is a valid instruction that evaluates to that number but performs no action
- Empty instruction lists are allowed in both true and false branches
- Conditions can be memory cells (true if non-zero), comparisons, index checks, or even recursion calls

### Calling self recursively

Each JUSTIF program is called initially with an index 1. It can call itself recursively with a new index. The syntax is

- `=1` - call self with index 1
- `=2` - call self with index 2
- ...
- `=n` - call self with index n

**Implementation note**: 
- Recursion can be used both as an instruction and as an expression that returns a value
- The index can be a memory reference or special token (`_` or `$`)
- Recursion expressions can appear in comparisons, assignments, and other contexts

### Syntax

The complete syntax for JUSTIF reads:

```
CODE = INSTRUCTIONS.
IF = MEMORY|ISINDEX|COMPARE '?' INSTRUCTIONS ':' INSTRUCTIONS.
COMPARE = ('+'|'-'|'*'|'/') MEMORY '=' (DECINT|MEMORY).
ISINDEX = '~' (DECINT|MEMORY).
INSTRUCTIONS = INSTRUCTION { ',' INSTRUCTION }.
INSTRUCTION = RECURSION|MEMSET|INPUT|OUTPUT|IF.
OUTPUT = ('>'|'!') MEMORY.
INPUT = '<' MEMORY.
RECURSION = '=' DECINT.
MEMSET = MEMORY ('='|'+'|'*'|'/'|'-') DECINT|STRING|MEMORY.
STRING = '"' ascii '"'.
MEMORY = '.' (DECINT|MEMORY) ['!' (DECINT|MEMORY)]
DECINT = '_' | '$' | DECDIGIT {DECDIGIT}.
DECDIGIT = '0' .. '9'.
```

**Implementation notes**:
- The parser uses recursive descent parsing
- Instructions can be empty (resulting in empty instruction lists)
- Constants (bare numbers) are valid instructions
- The grammar is designed to be unambiguous despite the context-sensitive nature of some operators

## Example Files

The `examples/` directory contains several JUSTIF programs:

### hello.justif
The classic Hello World program. Uses two recursion indices:
- Index 1: Initialize counter to 0 and string to "Hello, World"
- Index 2: Loop through string, printing each character until null terminator

### hello_verbose.justif
Same as hello.justif but with extensive comments showing how uppercase letters and spaces serve as whitespace, making the code self-documenting.

### hello_opp.opp.justif
Demonstrates OPP integration with JUSTIF. Uses conditional compilation to print different messages based on whether DEBUG is defined:
- Without DEBUG: prints "Hello, World"
- With DEBUG: prints "Hello from OPP+Justif!"
Run with `justif -D DEBUG examples/hello_opp.opp.justif` to see the debug version.

### fibonacci.justif
Prints the first 10 Fibonacci numbers. Uses advanced features with `_` for dynamic recursion and memory cells to track the sequence. Note: The original example uses complex `_` semantics that may behave differently in edge cases.

### fib_fixed.justif
A simplified version of the Fibonacci sequence that avoids the complex `_` usage, making it more straightforward to understand and debug.

### atoi.justif
Converts the string "1182" to an integer and prints it. Demonstrates:
- String character access with `.n!m`
- Character comparison (ASCII values)
- Arithmetic operations to build the integer result
Note: Uses complex nested conditions and may need adjustment for full compatibility.

### counter.justif
A simple counter program that prints numbers 1 through 5 with newlines. Good for understanding basic recursion and comparison operations.

### Various test files
- `test_fib.justif`, `fib_test2.justif` - Fibonacci variations for testing
- `atoi_simple.justif`, `atoi_test2.justif` - Simplified atoi versions
- `const_test.justif` - Tests constant number handling
- `nested_if.justif` - Tests nested IF statements