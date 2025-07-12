#! /usr/bin/python
import sys
from typing import Final

import typer
from loguru import logger

## CODE = INSTRUCTIONS.
## IF = MEMORY|ISINDEX|COMPARE '?' INSTRUCTIONS ':' INSTRUCTIONS.
## COMPARE = ('+'|'-'|'*'|'/') MEMORY '=' (DECINT|MEMORY).
## ISINDEX = '~' (DECINT|MEMORY).
## INSTRUCTIONS = INSTRUCTION { ',' INSTRUCTION }.
## INSTRUCTION = RECURSION|MEMSET|INPUT|OUTPUT|IF.
## OUTPUT = ('>'|'!') MEMORY.
## INPUT = '<' MEMORY.
## RECURSION = '=' DECINT.
## MEMSET = MEMORY ('='|'+'|'*'|'/'|'-') DECINT|STRING|MEMORY.
## STRING = '"' ascii '"'.
## MEMORY = '.' DECINT ['!' (DECINT|MEMORY)]
## DECINT = '_' | '$' | DECDIGIT {DECDIGIT}.
## DECDIGIT = '0' .. '9'.


class Memory:
    """A simple memory class to store and retrieve values."""

    def __init__(self):
        self.__memory: dict[int, int] = {}

    def __getitem__(self, index: int | list[int]) -> int:
        
        offset = index[0]
        if type(offset) == type([]):
            offset = self.__memory[offset[0]]
        if offset not in self.__memory:
            self.__memory[offset] = 0
        result = self.__memory[offset]
        if len(index) == 2:
            offset = index[1]
            if type(offset) == type(0):
                result = result[offset]
            else:
                result = result[memory[offset]]
        logger.warning("MEMORY: GOT [{!r}]={!r}", index, result)
        return result

    def __setitem__(self, index: int, value: int):
        offset = index[0]
        if type(offset) == type([]):
            offset = self.__memory[offset[0]]
        self.__memory[offset] = value
        logger.warning("MEMORY: SET [{!r}]={!r}", offset, value)
        return 0


memory: Final[Memory] = Memory()
root_sequence: list = []  # This will hold the root sequence of instructions.

class Instruction:
    """A class to represent an instruction in the Justif language."""

    def Value(self, data, index: int):
        """_summary_

        Args:
            data (_type_): _description_
            index (_type_): _description_

        Returns:
            _type_: _description_
        """
        logger.info(
            "Value called with data={} of type {} and index={}", data, type(data), index
        )
        if type(data) == type(0):
            return data
        elif type(data) == type(""):
            return list([ord(c) for c in data]) + [0]
        elif type(data) == type([]):
            return memory[data]
        elif type(data) == type(self):
            return data.Execute(index)
        else:
            raise "ERROR, expected type int, string or Instruction for assignment but got %s instead" % str(
                type(self.source)
            )

    def Assign(self, index: int) -> int:
        """This method assigns a value to the current target memory location.

        Args:
            index (int): The index to retrieve the value from the source.

        Returns:
            int: The value assigned to the target memory location.
        """
        memory[self.target] = self.Value(self.source, index)
        return memory[self.target]

    def Add(self, index: int) -> int:
        """_summary_

        Args:
            index (_type_): _description_

        Returns:
            _type_: _description_
        """
        value = self.Value(self.source, index)
        logger.debug("Add {} to {}", value, memory[self.target])
        memory[self.target] += value
        return memory[self.target]

    def Subtract(self, index: int) -> int:
        """_summary_

        Args:
            index (_type_): _description_

        Returns:
            _type_: _description_
        """
        memory[self.target] -= self.Value(self.source, index)
        return memory[self.target]

    def Multiply(self, index: int) -> int:
        """_summary_

        Args:
            index (_type_): _description_

        Returns:
            _type_: _description_
        """
        memory[self.target] *= self.Value(self.source, index)
        return memory[self.target]

    def Divide(self, index: int) -> int:
        """_summary_

        Args:
            index (_type_): _description_

        Returns:
            _type_: _description_
        """
        memory[self.target] /= self.Value(self.source, index)
        return memory[self.target]


    def If(self, index: int) -> bool:
        if type(self.address) == type(self):
            result = self.address.Execute(index)
        else:
            result = memory[self.address]
        logger.debug("IF-Expression is {}", result)
        if result:
            return ExecuteInstructionSequence(self.if_true, index)
        else:
            return ExecuteInstructionSequence(self.if_false, index)

    def IsIndex(self, index: int) -> bool:
        """_summary_

        Args:
            index (_type_): _description_

        Returns:
            _type_: _description_
        """
        return index == self.Value(self.value, index)


class ConstantInstruction(Instruction):
    """A class to represent a constant instruction in the Justif language
    """
    def __init__(self, decint: int):
        self.__value: Final[int] = decint

    def Execute(self, _: int) -> int:
        """Execute the constant instruction.

        Args:
            index (int): *ignored*

        Returns:
            int: returns the constant value.
        """
        return self.__value

class InputInstruction(Instruction):
    """A class to represent an input instruction in the Justif language.
    """
    def __init__(self, address: int):
        self.__address: Final[int] = address
        """Address at which to store the input value."""
        
    def Execute(self, _: int) -> int:
        """Execute the input instruction.

        Args:
            index (int): *ignored*
        """
        raise RuntimeError("Not implemented yet")

class RecurseInstruction(Instruction):
    """A class to represent a recursion instruction in the Justif language.
    """
    def __init__(self, index: int):
        self.__index: Final[int] = index

    def Execute(self, index: int) -> int:
        """_summary_

        Args:
            index (_type_): _description_

        Returns:
            _type_: _description_
        """
        global root_sequence
        logger.debug("Call self recursively with index {}", self.__index)
        return ExecuteInstructionSequence(root_sequence, self.__index)

class OutputCharInstruction(Instruction):
    """A class to represent a char output instruction in the Justif language.
    """
    def __init__(self, address: int):
        self.__value: Final[int] = address

    def Execute(self, _: int) -> int:
        """_summary_

        Args:
            index (int): *ignored*

        Returns:
            int: returns 1 always, indicating successful execution.
        """
        sys.stdout.write(chr(memory[self.__value]))
        return 1

class OutputIntegerInstruction(Instruction):
    """A class to represent a char output instruction in the Justif language.
    """
    def __init__(self, address: int):
        self.__value: Final[int] = address

    def Execute(self, _: int) -> int:
        """_summary_

        Args:
            index (int): *ignored*

        Returns:
            int: returns 1 always, indicating successful execution.
        """
        sys.stdout.write(str(memory[self.__value]))
        return 1

class ComparisonInstruction(Instruction):
    """A class to represent a char output instruction in the Justif language.
    """
    def __init__(self, first: int, second: int, method_to_execute: str):
        self.__first: Final[int] = first
        self.__second: Final[int] = second
        self.__method_to_execute: Final[str] = method_to_execute

    def Execute(self, index: int) -> int:
        a = self.Value(self.__first, index)
        b = self.Value(self.__second, index)
        match self.__method_to_execute:
            case '+':
                logger.debug("Executing less than comparison: {} < {}", a, b)
                return a < b
            case '-':
                logger.debug("Executing equal to comparison: {} == {}", a, b)
                return a == b
            case '*':
                logger.debug("Executing greater than comparison: {} > {}", a, b)
                return a > b
            case '/':
                logger.debug("Executing not equal to comparison: {} != {}", a, b)
                return a != b
            case _:
                logger.error("Unknown comparison method: {}", self.__method_to_execute)
                raise RuntimeError(f"Unknown comparison method: {self.__method_to_execute}")

def ExecuteInstructionSequence(instructions: list[Instruction], index: int) -> int:
    """Execute a sequence of instructions.

    Args:
        instructions (list[Instruction]): _description_
        index (int): _description_

    Returns:
        int: _description_
    """
    result = 0
    for instruction in instructions:
        result = instruction.Execute(index)
    return result


class JustifParser:
    """A parser for the Justif language.
    """
    
    def __init__(self):
        self.expression: str = ""
        self.pos: int = 0
        self.__nums: list[int] = [-1, -1]

    def Parse(self, expression: str) -> list[Instruction] | None:
        """Parse the Justif expression into a sequence of instructions.

        Args:
            expression (str): A valid justif expression / program.

        Returns:
            list[Instruction]: The instructions parsed from the expression.
        """
        self.expression = expression
        self.pos = 0
        self.__nums = [-1, -1]
        return self.__parse_instructions()

    def __skip_whitespaces(self) -> None:
        """Skip whitespace characters in the expression.
        This method advances the position in the expression until a non-whitespace character is found."""
        try:
            while (
                self.expression[self.pos]
                in " \r\nABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
            ):
                self.pos += 1
        except IndexError:
            pass

    def __save_state(self) -> tuple[int, list[int]]:
        """Push the current parser position and intermediate numbers onto a stack.

        Returns:
            tuple[int, list[int]]: (current position, copy of __nums)
        """
        return self.pos, self.__nums[:]

    def __restore_state(self, previously_saved_pos: tuple[int, list[int]]) -> None:
        """Restore the previously saved position and numbers from a local variable

        Args:
            s (_tytuple[int, list[int]]pe_):(previous position, copy of previous __nums)
        """
        self.pos = previously_saved_pos[0]
        self.__nums = previously_saved_pos[1]

    def __get_char(self) -> str:
        """Get the character at the current position

        Returns:
            str: character at the current position or '\0' if out of bounds.
        """
        self.__skip_whitespaces()
        try:
            result = self.expression[self.pos]
            assert isinstance(result, str), "Expected a string character"
            logger.debug("GetChar: {!r}", result)
            return result
        except IndexError:
            pass
        return '\0'

    def __skip_char(self, expression: str) -> bool:
        """_summary_

        Args:
            expression (_type_): _description_

        Returns:
            _type_: _description_
        """
        self.__skip_whitespaces()
        try:
            if self.expression[self.pos : self.pos + len(expression)] == expression:
                self.pos += len(expression)
                return True
        except IndexError:
            pass
        return False

    def ISINDEX(self):
        state = self.__save_state()
        if self.__skip_char("~"):
            value = self.__dec_int()
            if value is None:
                value = self.parse_memory_access()
            if value is not None:
                result = Instruction()
                result.value = value
                result.Execute = result.IsIndex
                return result
        self.__restore_state(state)

    def __cmp_instruction(self) -> Instruction | None:
        state = self.__save_state()
        c = self.__get_char()
        if c in "+-*/":
            self.pos += 1
            m = self.parse_memory_access()
            if m is not None and self.__skip_char("="):
                v = self.__dec_int()
                if v is None:
                    v = self.parse_memory_access()
                if v is not None:
                    return ComparisonInstruction(m, v, c)
        self.__restore_state(state)
        return None

    def IF(self):
        state = self.__save_state()
        m = self.parse_memory_access()
        if m is None:
            m = self.__cmp_instruction()
        if m is None:
            m = self.__recursion()
        if m is None:
            m = self.ISINDEX()
        if m is not None and self.__skip_char("?"):
            if_true = self.__parse_instructions()
            if if_true and self.__skip_char(":"):
                if_false = self.__parse_instructions()
                if if_false:
                    result = Instruction()
                    result.address = m
                    result.if_true = if_true
                    result.if_false = if_false
                    result.Execute = result.If
                    return result
        self.__restore_state(state)

    def __io_input(self) -> InputInstruction | None:
        """Parse an input instruction from the expression.

        Returns:
            InputInstruction | None: An InputInstruction if a valid input is found, otherwise None.
        """
        state = self.__save_state()
        if self.__skip_char("<"):
            address = self.parse_memory_access()
            if address:
                return InputInstruction(address)
        self.__restore_state(state)
        return None

    def __io_output(self) -> Instruction | None:
        """Parse an output instruction from the expression.

        Returns:
            Instruction | None: An OutputCharInstruction or OutputIntegerInstruction if a valid output is found, otherwise None.
        """
        state = self.__save_state()
        if self.__skip_char(">"):
            address = self.parse_memory_access()
            if address is not None:
                return OutputCharInstruction(address)

        elif self.__skip_char("!"):
            address = self.parse_memory_access()
            if address is not None:
                return OutputIntegerInstruction(address)

        self.__restore_state(state)
        return None

    def __parse_instructions(self) -> list[Instruction] | None:
        """Return a list of instructions parsed from the expression.

        Returns:
            list[Instruction] | None: A list of instructions if valid instructions are found, otherwise None.
        """
        state = self.__save_state()
        instruction = self.__parse_single_instruction()
        if instruction:
            result = []
            while 1:
                result.append(instruction)
                if self.__skip_char(","):
                    instruction = self.__parse_single_instruction()
                    if instruction:
                        continue
                break
            return result
        self.__restore_state(state)
        return None

    def __parse_single_instruction(self) -> Instruction | None:
        """Parse a single instruction from the expression.

        Returns:
            Instruction | None: An Instruction if a valid instruction is found, otherwise None.
        """
        state = self.__save_state()
        for function in (
            self.IF,
            self.__cmp_instruction,
            self.__recursion,
            self.__memset,
            self.__io_output,
            self.__io_input,
            self.__parse_constant,
        ):
            instruction = function()
            if instruction is not None:
                return instruction
        self.__restore_state(state)

    def __parse_constant(self) -> Instruction | None:
        """Parse a constant value from the expression.

        Returns:
            Instruction | None: A ConstantInstruction if a valid constant is found, otherwise None.
        """
        decint = self.__dec_int()
        if decint is not None:
            logger.debug("Parsed constant value: {}", decint)
            return ConstantInstruction(decint)
        return None

    def STRING(self):
        if self.__skip_char('"'):
            startpos = self.pos
            while 1:
                c = self.__get_char()
                if c == 0:
                    raise SyntaxError("Expected end-of-string")
                self.pos += 1
                if c == '"':
                    return self.expression[startpos : self.pos - 1]

    def __recursion(self) -> Instruction | None:
        """_summary_

        Returns:
            Instruction | None: 
        """
        state = self.__save_state()
        if self.__skip_char("="):
            index = self.__dec_int()
            if index is not None:
                return RecurseInstruction(index)
        self.__restore_state(state)
        return None

    def __memset(self) -> Instruction | None:
        """_summary_

        Returns:
            Instruction | None: _description_
        """
        state = self.__save_state()
        m = self.parse_memory_access()
        if m:
            c = self.__get_char()
            if c in "=+-*/":
                self.pos += 1
                d = self.__dec_int()
                if d is None:
                    d = self.STRING()
                if d is None:
                    d = self.parse_memory_access()
                if d is not None:
                    result = Instruction()
                    result.source = d
                    result.operation = c
                    result.target = m
                    result.Execute = [
                        result.Assign,
                        result.Add,
                        result.Subtract,
                        result.Multiply,
                        result.Divide,
                    ]["=+-*/".index(c)]
                    return result
        self.__restore_state(state)
        return None

    def parse_memory_access(self):
        """_summary_

        Raises:
            SyntaxError: _description_

        Returns:
            list[int] | None: _description_
        """
        state = self.__save_state()
        if self.__skip_char("."):
            d = self.__dec_int()
            if d is None:
                d = self.parse_memory_access()
            if d is not None:
                result = [d]
                while self.__skip_char("!"):
                    number = self.__dec_int()
                    if number is None:
                        number = self.parse_memory_access()
                        if number is None:
                            raise SyntaxError("Expected decint after '!'")
                    result.append(number)
                return result
        self.__restore_state(state)

    def __dec_int(self) -> int | None:
        """Parse a decimal integer from the current position in the expression.
        If it is an integer, the scan position is advanced and the integer is returned.

        Returns:
            int | None: Either the parsed integer or None if parsing fails. 
        """
        number: int = 0
        if self.__skip_char("_"):
            return self.__nums[0]
        if self.__skip_char("$"):
            return self.__nums[1]
        success, digit = self.__dec_digit()
        if not success:
            return None

        while success:
            number *= 10
            number += digit
            success, digit = self.__dec_digit()
        self.__nums[1] = self.__nums[0]
        self.__nums[0] = number
        return number

    def __dec_digit(self) -> tuple[bool, int]:
        """Check if the current character is a decimal digit and if so, return its value.

        Returns:
            tuple[bool, int]: (success, digit_value)
        """
        c = self.__get_char()
        if ord(c) >= ord("0") and ord(c) <= ord("9"):
            self.pos += 1
            return True, ord(c) - ord("0")
        return False, 0


def main(
    filename: str = typer.Argument(..., help="The filename to parse and execute.")
):
    j = JustifParser()
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    global root_sequence
    root_sequence = j.Parse(content)
    if root_sequence is not None:
        ExecuteInstructionSequence(root_sequence, 1)
    else:
        logger.error("Unable to parse {}", filename)


if __name__ == "__main__":
    typer.run(main)
