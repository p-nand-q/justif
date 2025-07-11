package main

import (
	"fmt"
)

// Memory stores values as either integers or integer arrays (for strings)
type Memory struct {
	cells map[int]interface{} // int or []int
}

func NewMemory() *Memory {
	return &Memory{
		cells: make(map[int]interface{}),
	}
}

func (m *Memory) Get(index int) interface{} {
	if val, ok := m.cells[index]; ok {
		return val
	}
	return 0 // default to 0
}

func (m *Memory) Set(index int, value interface{}) {
	m.cells[index] = value
}

func (m *Memory) GetAsInt(index int) (int, error) {
	val := m.Get(index)
	switch v := val.(type) {
	case int:
		return v, nil
	case []int:
		return 0, fmt.Errorf("cannot convert string to int")
	default:
		return 0, nil
	}
}

func (m *Memory) GetChar(cellIndex int, charIndex int) (int, error) {
	val := m.Get(cellIndex)
	switch v := val.(type) {
	case []int:
		if charIndex >= 0 && charIndex < len(v) {
			return v[charIndex], nil
		}
		return 0, nil // out of bounds returns 0
	case int:
		return 0, fmt.Errorf("cell %d is not a string", cellIndex)
	default:
		return 0, fmt.Errorf("cell %d is empty", cellIndex)
	}
}

func (m *Memory) ApplyOperation(index int, op string, value int) error {
	current := m.Get(index)
	
	currentInt, ok := current.(int)
	if !ok {
		return fmt.Errorf("cannot perform arithmetic on non-integer")
	}
	
	var result int
	switch op {
	case "=":
		result = value
	case "+":
		result = currentInt + value
	case "-":
		result = currentInt - value
	case "*":
		result = currentInt * value
	case "/":
		if value == 0 {
			return fmt.Errorf("division by zero")
		}
		result = currentInt / value
	default:
		return fmt.Errorf("unknown operation: %s", op)
	}
	
	m.Set(index, result)
	return nil
}

// Convert string to integer array with null terminator
func StringToIntArray(s string) []int {
	result := make([]int, len(s)+1)
	for i, ch := range s {
		result[i] = int(ch)
	}
	result[len(s)] = 0 // null terminator
	return result
}