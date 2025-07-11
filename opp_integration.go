package main

import (
	"fmt"
	"os"

	"github.com/p-nand-q/opp"
)

func runWithOPP(filename string, defines map[string]string) {
	source, err := os.ReadFile(filename)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading file: %v\n", err)
		os.Exit(1)
	}

	sourceStr := string(source)
	
	// Apply OPP preprocessing
	preprocessor := opp.WithDefines(defines)
	sourceStr, err = preprocessor.Process(sourceStr)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Preprocessing error: %v\n", err)
		os.Exit(1)
	}

	parser := NewParser(sourceStr)
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