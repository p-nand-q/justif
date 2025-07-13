package main

import (
	"fmt"
)

type Interpreter struct {
	memory      *Memory
	program     *Program
	nums        [2]int // track last/before-last numbers globally
}

func NewInterpreter() *Interpreter {
	return &Interpreter{
		memory: NewMemory(),
		nums:   [2]int{-1, -1},
	}
}

func (i *Interpreter) Execute(program *Program) error {
	i.program = program
	_, err := i.ExecuteInstructionSequence(i.program.Instructions, 1)
	return err
}

func (i *Interpreter) ExecuteInstructionSequence(instructions []Instruction, index int) (int, error) {
	result := 0
	// fmt.Printf("DEBUG: Executing %d instructions at index %d\n", len(instructions), index)
	for _, inst := range instructions {
		val, err := i.ExecuteInstruction(inst, index)
		if err != nil {
			return 0, err
		}
		result = val
	}
	return result, nil
}

func (i *Interpreter) ExecuteInstruction(inst Instruction, index int) (int, error) {
	switch instr := inst.(type) {
	case *IfInstruction:
		return i.ExecuteIf(instr, index)
	case *RecursionInstruction:
		idx, err := i.Value(instr.Index, index)
		if err != nil {
			return 0, err
		}
		result, err := i.ExecuteInstructionSequence(i.program.Instructions, idx)
		return result, err
	case *MemsetInstruction:
		return i.ExecuteMemset(instr, index)
	case *OutputInstruction:
		return i.ExecuteOutput(instr, index)
	case *ConstantInstruction:
		return i.Value(instr.Value, index)
	case *CompareInstruction:
		// Execute comparison and return boolean result (0 or 1)
		result, err := i.EvaluateCondition(instr.Compare, index)
		if err != nil {
			return 0, err
		}
		if result {
			return 1, nil
		}
		return 0, nil
	case *NoOpInstruction:
		return 0, nil
	default:
		return 0, fmt.Errorf("unknown instruction type: %T", inst)
	}
}

func (i *Interpreter) ExecuteIf(instr *IfInstruction, index int) (int, error) {
	condition, err := i.EvaluateCondition(instr.Condition, index)
	if err != nil {
		return 0, err
	}

	if condition {
		return i.ExecuteInstructionSequence(instr.TrueInstructions, index)
	}
	return i.ExecuteInstructionSequence(instr.FalseInstructions, index)
}

func (i *Interpreter) ExecuteMemset(instr *MemsetInstruction, index int) (int, error) {
	targetIndex, err := i.GetMemoryIndex(instr.Memory, index)
	if err != nil {
		return 0, err
	}
	// fmt.Printf("DEBUG: Memset cell %d with operation %s\n", targetIndex, instr.Operation)

	// Handle different value types
	switch val := instr.Value.(type) {
	case *StringNode:
		if instr.Operation == "=" {
			i.memory.Set(targetIndex, StringToIntArray(val.Value))
			return 0, nil
		}
		return 0, fmt.Errorf("cannot perform %s operation on string", instr.Operation)
		
	case *MemoryAccess:
		// Check if this is character access
		if val.CharIndex != nil {
			cellIndex, err := i.GetMemoryIndex(val, index)
			if err != nil {
				return 0, err
			}
			charIndex, err := i.Value(val.CharIndex, index)
			if err != nil {
				return 0, err
			}
			charValue, err := i.memory.GetChar(cellIndex, charIndex)
			if err != nil {
				return 0, err
			}
			// For character access, we always get an int value
			if instr.Operation == "=" {
				i.memory.Set(targetIndex, charValue)
				return 0, nil
			}
			return 0, i.memory.ApplyOperation(targetIndex, instr.Operation, charValue)
		}
		
		// Regular memory access without character index
		sourceIndex, err := i.GetMemoryIndex(val, index)
		if err != nil {
			return 0, err
		}
		sourceValue := i.memory.Get(sourceIndex)
		if instr.Operation == "=" {
			i.memory.Set(targetIndex, sourceValue)
			return 0, nil
		}
		// For arithmetic operations, convert to int
		intVal, err := i.memory.GetAsInt(sourceIndex)
		if err != nil {
			return 0, err
		}
		return 0, i.memory.ApplyOperation(targetIndex, instr.Operation, intVal)
		
	default:
		// Regular integer value
		intVal, err := i.Value(instr.Value, index)
		if err != nil {
			return 0, err
		}
		if instr.Operation == "=" {
			i.memory.Set(targetIndex, intVal)
			return intVal, nil
		}
		return 0, i.memory.ApplyOperation(targetIndex, instr.Operation, intVal)
	}
}

func (i *Interpreter) ExecuteOutput(instr *OutputInstruction, index int) (int, error) {
	if instr.Memory.CharIndex != nil {
		// Character access in string
		cellIndex, err := i.GetMemoryIndex(instr.Memory, index)
		if err != nil {
			return 0, err
		}
		charIndex, err := i.Value(instr.Memory.CharIndex, index)
		if err != nil {
			return 0, err
		}
		charValue, err := i.memory.GetChar(cellIndex, charIndex)
		if err != nil {
			return 0, err
		}
		if instr.Mode == ">" {
			fmt.Printf("%c", rune(charValue))
		} else {
			fmt.Printf("%d", charValue)
		}
	} else {
		// Regular memory access
		memIndex, err := i.GetMemoryIndex(instr.Memory, index)
		if err != nil {
			return 0, err
		}
		// Debug: what are we outputting?
		if false { // Enable for debugging
			fmt.Printf("[DEBUG: outputting memory[%d] = %v]\n", memIndex, i.memory.Get(memIndex))
		}
		val := i.memory.Get(memIndex)
		switch v := val.(type) {
		case int:
			if instr.Mode == ">" {
				fmt.Printf("%c", rune(v))
			} else {
				fmt.Println(v)
			}
		case []int:
			if instr.Mode == ">" {
				for _, ch := range v {
					if ch == 0 {
						break
					}
					fmt.Printf("%c", rune(ch))
				}
			} else {
				return 0, fmt.Errorf("cannot output string as number")
			}
		}
	}
	return 0, nil
}

func (i *Interpreter) EvaluateCondition(node Node, index int) (bool, error) {
	switch n := node.(type) {
	case *CompareNode:
		leftIndex, err := i.GetMemoryIndex(n.Left, index)
		if err != nil {
			return false, err
		}
		leftVal, err := i.memory.GetAsInt(leftIndex)
		if err != nil {
			return false, err
		}
		
		rightVal, err := i.Value(n.Right, index)
		if err != nil {
			return false, err
		}

		switch n.Operation {
		case "+":
			return leftVal < rightVal, nil
		case "-":
			return leftVal == rightVal, nil
		case "*":
			return leftVal > rightVal, nil
		case "/":
			return leftVal != rightVal, nil
		}
		
	case *IsIndexNode:
		idx, err := i.Value(n.Index, index)
		if err != nil {
			return false, err
		}
		return index == idx, nil
		
	case *MemoryAccess:
		// Handle character access specially
		if n.CharIndex != nil {
			cellIndex, err := i.GetMemoryIndex(n, index)
			if err != nil {
				return false, err
			}
			charIndex, err := i.Value(n.CharIndex, index)
			if err != nil {
				return false, err
			}
			charValue, err := i.memory.GetChar(cellIndex, charIndex)
			if err == nil {
				return charValue != 0, nil
			}
			// If error, character doesn't exist
			return false, nil
		}
		
		// Regular memory access
		memIndex, err := i.GetMemoryIndex(n, index)
		if err != nil {
			return false, err
		}
		val, err := i.memory.GetAsInt(memIndex)
		if err != nil {
			return false, err
		}
		return val != 0, nil
		
	case Instruction:
		// Execute instruction and check result
		result, err := i.ExecuteInstruction(n, index)
		if err != nil {
			return false, err
		}
		return result != 0, nil
	}
	
	return false, fmt.Errorf("invalid condition type: %T", node)
}

func (i *Interpreter) Value(node Node, index int) (int, error) {
	switch n := node.(type) {
	case *NumberNode:
		// For _ and $, the value was resolved at parse time
		// and stored in n.Value. We should use that, not the
		// runtime nums array.
		if n.IsLast || n.IsBefore {
			return n.Value, nil
		}
		// Update tracking for regular numbers
		i.nums[1] = i.nums[0]
		i.nums[0] = n.Value
		return n.Value, nil
		
	case *MemoryAccess:
		idx, err := i.GetMemoryIndex(n, index)
		if err != nil {
			return 0, err
		}
		return i.memory.GetAsInt(idx)
		
	case Instruction:
		return i.ExecuteInstruction(n, index)
		
	default:
		return 0, fmt.Errorf("cannot get value from %T", node)
	}
}

func (i *Interpreter) GetMemoryIndex(mem *MemoryAccess, index int) (int, error) {
	idx, err := i.Value(mem.Index, index)
	if err != nil {
		return 0, err
	}
	
	// Handle indirect access
	if !mem.Direct {
		return i.memory.GetAsInt(idx)
	}
	
	return idx, nil
}