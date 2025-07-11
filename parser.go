package main

import (
	"fmt"
)

type Parser struct {
	expression string
	pos        int
	nums       [2]int // for _ and $
}

func NewParser(expression string) *Parser {
	return &Parser{
		expression: expression,
		pos:        0,
		nums:       [2]int{-1, -1},
	}
}

func (p *Parser) Parse() (*Program, error) {
	instructions := p.INSTRUCTIONS()
	if instructions == nil {
		return nil, fmt.Errorf("failed to parse instructions")
	}
	return &Program{Instructions: instructions}, nil
}

func (p *Parser) SkipWhitespaces() {
	for p.pos < len(p.expression) {
		ch := p.expression[p.pos]
		if (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') || 
		   ch == ' ' || ch == '\r' || ch == '\n' || ch == '\t' {
			p.pos++
		} else {
			break
		}
	}
}

func (p *Parser) PushPos() (int, [2]int) {
	return p.pos, p.nums
}

func (p *Parser) PopPos(pos int, nums [2]int) {
	p.pos = pos
	p.nums = nums
}

func (p *Parser) GetChar(offset int) byte {
	p.SkipWhitespaces()
	if p.pos+offset < len(p.expression) {
		return p.expression[p.pos+offset]
	}
	return 0
}

func (p *Parser) SkipChar(s string) bool {
	p.SkipWhitespaces()
	if p.pos+len(s) <= len(p.expression) && p.expression[p.pos:p.pos+len(s)] == s {
		p.pos += len(s)
		return true
	}
	return false
}

func (p *Parser) INSTRUCTIONS() []Instruction {
	pos, nums := p.PushPos()
	instruction := p.INSTRUCTION()
	if instruction != nil {
		result := []Instruction{}
		for instruction != nil {
			result = append(result, instruction)
			if p.SkipChar(",") {
				instruction = p.INSTRUCTION()
			} else {
				break
			}
		}
		return result
	}
	p.PopPos(pos, nums)
	return nil
}

func (p *Parser) INSTRUCTION() Instruction {
	pos, nums := p.PushPos()
	
	// Try each instruction type in order
	// IF handles COMPARE and other conditions internally
	instructionParsers := []func()Instruction{
		p.IF,
		p.RECURSION,
		p.MEMSET,
		p.OUTPUT,
		p.INPUT,
		p.CONSTANT,
	}
	
	for _, parser := range instructionParsers {
		if instruction := parser(); instruction != nil {
			return instruction
		}
	}
	
	p.PopPos(pos, nums)
	return nil
}

func (p *Parser) IF() Instruction {
	pos, nums := p.PushPos()
	
	// Try different condition types
	var condition Node
	if mem := p.MEMORY(); mem != nil {
		condition = mem
	} else if cmp := p.COMPARE(); cmp != nil {
		condition = cmp
	} else if rec := p.RECURSION(); rec != nil {
		condition = rec
	} else if idx := p.ISINDEX(); idx != nil {
		condition = idx
	}
	
	if condition != nil && p.SkipChar("?") {
		trueInst := p.INSTRUCTIONS()
		// Allow empty true branch
		if trueInst == nil {
			trueInst = []Instruction{}
		}
		if p.SkipChar(":") {
			falseInst := p.INSTRUCTIONS()
			// Allow empty false branch
			if falseInst == nil {
				falseInst = []Instruction{}
			}
			return &IfInstruction{
				Condition:         condition,
				TrueInstructions:  trueInst,
				FalseInstructions: falseInst,
			}
		}
	}
	
	p.PopPos(pos, nums)
	return nil
}

func (p *Parser) ISINDEX() Node {
	pos, nums := p.PushPos()
	if p.SkipChar("~") {
		var value Node
		if num := p.DECINT(); num != nil {
			value = num
		} else if mem := p.MEMORY(); mem != nil {
			value = mem
		}
		if value != nil {
			return &IsIndexNode{Index: value}
		}
	}
	p.PopPos(pos, nums)
	return nil
}

func (p *Parser) COMPARE() Node {
	pos, nums := p.PushPos()
	c := p.GetChar(0)
	if c == '+' || c == '-' || c == '*' || c == '/' {
		p.pos++
		if mem := p.MEMORY(); mem != nil && p.SkipChar("=") {
			var value Node
			if num := p.DECINT(); num != nil {
				value = num
			} else if mem2 := p.MEMORY(); mem2 != nil {
				value = mem2
			} else if rec := p.RECURSION(); rec != nil {
				value = rec
			}
			if value != nil {
				return &CompareNode{
					Operation: string(c),
					Left:      mem,
					Right:     value,
				}
			}
		}
	}
	p.PopPos(pos, nums)
	return nil
}

func (p *Parser) RECURSION() Instruction {
	pos, nums := p.PushPos()
	if p.SkipChar("=") {
		// Try parsing as DECINT first (includes _ and $)
		if index := p.DECINT(); index != nil {
			return &RecursionInstruction{Index: index}
		}
		// Also try memory access
		if mem := p.MEMORY(); mem != nil {
			return &RecursionInstruction{Index: mem}
		}
	}
	p.PopPos(pos, nums)
	return nil
}

func (p *Parser) MEMSET() Instruction {
	pos, nums := p.PushPos()
	if mem := p.MEMORY(); mem != nil {
		c := p.GetChar(0)
		if c == '=' || c == '+' || c == '-' || c == '*' || c == '/' {
			p.pos++
			var value Node
			if num := p.DECINT(); num != nil {
				value = num
			} else if str := p.STRING(); str != nil {
				value = str
			} else if mem2 := p.MEMORY(); mem2 != nil {
				value = mem2
			}
			if value != nil {
				return &MemsetInstruction{
					Memory:    mem,
					Operation: string(c),
					Value:     value,
				}
			}
		}
	}
	p.PopPos(pos, nums)
	return nil
}

func (p *Parser) OUTPUT() Instruction {
	pos, nums := p.PushPos()
	if p.SkipChar(">") {
		if mem := p.MEMORY(); mem != nil {
			return &OutputInstruction{Mode: ">", Memory: mem}
		}
	} else if p.SkipChar("!") {
		if mem := p.MEMORY(); mem != nil {
			return &OutputInstruction{Mode: "!", Memory: mem}
		}
	}
	p.PopPos(pos, nums)
	return nil
}

func (p *Parser) INPUT() Instruction {
	pos, nums := p.PushPos()
	if p.SkipChar("<") {
		if mem := p.MEMORY(); mem != nil {
			// Input not implemented yet
			return nil
		}
	}
	p.PopPos(pos, nums)
	return nil
}

func (p *Parser) CONSTANT() Instruction {
	if num := p.DECINT(); num != nil {
		return &ConstantInstruction{Value: num}
	}
	return nil
}

func (p *Parser) MEMORY() *MemoryAccess {
	pos, nums := p.PushPos()
	if p.SkipChar(".") {
		var index Node
		if num := p.DECINT(); num != nil {
			index = num
		} else if mem := p.MEMORY(); mem != nil {
			// Indirect memory access
			index = mem
		}
		
		if index != nil {
			result := &MemoryAccess{Index: index, Direct: true}
			
			// Check for indirect access (when index is a memory access)
			if _, isMemory := index.(*MemoryAccess); isMemory {
				result.Direct = false
			}
			
			// Check for string character access
			if p.SkipChar("!") {
				var charIndex Node
				if num := p.DECINT(); num != nil {
					charIndex = num
				} else if mem := p.MEMORY(); mem != nil {
					charIndex = mem
				}
				if charIndex != nil {
					result.CharIndex = charIndex
				}
			}
			
			return result
		}
	}
	p.PopPos(pos, nums)
	return nil
}

func (p *Parser) STRING() Node {
	if p.SkipChar("\"") {
		startPos := p.pos
		for p.pos < len(p.expression) {
			if p.expression[p.pos] == '"' {
				value := p.expression[startPos:p.pos]
				p.pos++
				return &StringNode{Value: value}
			}
			p.pos++
		}
	}
	return nil
}

func (p *Parser) DECINT() Node {
	p.SkipWhitespaces()
	
	// Check for special tokens
	if p.SkipChar("_") {
		return &NumberNode{Value: p.nums[0], IsLast: true}
	}
	if p.SkipChar("$") {
		return &NumberNode{Value: p.nums[1], IsBefore: true}
	}
	
	// Parse regular number
	number := 0
	foundDigit := false
	
	for p.pos < len(p.expression) {
		ch := p.expression[p.pos]
		if ch >= '0' && ch <= '9' {
			number = number*10 + int(ch-'0')
			p.pos++
			foundDigit = true
		} else {
			break
		}
	}
	
	if foundDigit {
		// Update number tracking
		p.nums[1] = p.nums[0]
		p.nums[0] = number
		return &NumberNode{Value: number}
	}
	
	return nil
}