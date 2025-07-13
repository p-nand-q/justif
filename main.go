package main

import (
	"flag"
	"fmt"
	"os"
	"strings"
)

type DefineFlags []string

func (d *DefineFlags) String() string {
	return strings.Join(*d, ",")
}

func (d *DefineFlags) Set(value string) error {
	*d = append(*d, value)
	return nil
}

func main() {
	var (
		useOPP  = flag.Bool("opp", false, "Enable OPP preprocessing")
		defines DefineFlags
	)
	
	flag.Var(&defines, "D", "Define a variable (can be used multiple times)")
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: %s [options] <file.justif>\n", os.Args[0])
		fmt.Fprintf(os.Stderr, "\nOptions:\n")
		flag.PrintDefaults()
		fmt.Fprintf(os.Stderr, "\nFiles with .opp.justif extension automatically enable OPP preprocessing.\n")
	}
	
	flag.Parse()
	
	if flag.NArg() < 1 {
		flag.Usage()
		os.Exit(1)
	}
	
	filename := flag.Arg(0)
	
	// Auto-detect OPP from filename or use flag
	if *useOPP || strings.HasSuffix(filename, ".opp.justif") {
		// Build defines map
		definesMap := make(map[string]string)
		for _, def := range defines {
			parts := strings.SplitN(def, "=", 2)
			if len(parts) == 2 {
				definesMap[parts[0]] = parts[1]
			} else {
				definesMap[parts[0]] = "1"
			}
		}
		
		runWithOPP(filename, definesMap)
		return
	}
	
	// Simple mode without OPP
	source, err := os.ReadFile(filename)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading file: %v\n", err)
		os.Exit(1)
	}

	parser := NewParser(string(source))
	ast, err := parser.Parse()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Parse error: %v\n", err)
		os.Exit(1)
	}
	

	interpreter := NewInterpreter()
	err = interpreter.Execute(ast)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Runtime error: %v\n", err)
		os.Exit(1)
	}
}