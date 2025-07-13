package main

// CompareInstruction wraps a CompareNode to make it usable as an instruction
// This allows comparisons like +.3=58 to be used in IF branches
type CompareInstruction struct {
	Compare *CompareNode
}

func (c *CompareInstruction) node()        {}
func (c *CompareInstruction) instruction() {}