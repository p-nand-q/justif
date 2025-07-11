package main

type Node interface {
	node()
}

type Program struct {
	Instructions []Instruction
}

func (p *Program) node() {}

type Instruction interface {
	Node
	instruction()
}

type IfInstruction struct {
	Condition    Node
	TrueInstructions  []Instruction
	FalseInstructions []Instruction
}

func (i *IfInstruction) node()        {}
func (i *IfInstruction) instruction() {}

type RecursionInstruction struct {
	Index Node
}

func (r *RecursionInstruction) node()        {}
func (r *RecursionInstruction) instruction() {}

type MemsetInstruction struct {
	Memory    *MemoryAccess
	Operation string
	Value     Node
}

func (m *MemsetInstruction) node()        {}
func (m *MemsetInstruction) instruction() {}

type OutputInstruction struct {
	Mode   string // ">" or "!"
	Memory *MemoryAccess
}

func (o *OutputInstruction) node()        {}
func (o *OutputInstruction) instruction() {}

type MemoryAccess struct {
	Direct   bool
	Index    Node
	CharIndex Node // for string character access
}

func (m *MemoryAccess) node() {}

type CompareNode struct {
	Operation string // "+", "-", "*", "/"
	Left      *MemoryAccess
	Right     Node
}

func (c *CompareNode) node() {}

type IsIndexNode struct {
	Index Node
}

func (i *IsIndexNode) node() {}

type NumberNode struct {
	Value    int
	IsLast   bool // for _
	IsBefore bool // for $
}

func (n *NumberNode) node() {}

type StringNode struct {
	Value string
}

func (s *StringNode) node() {}

// NoOpInstruction represents a no-op (like 0)
type NoOpInstruction struct{}

func (n *NoOpInstruction) node()        {}
func (n *NoOpInstruction) instruction() {}

// Add new instruction type for constant
type ConstantInstruction struct {
	Value Node
}

func (c *ConstantInstruction) node()        {}
func (c *ConstantInstruction) instruction() {}