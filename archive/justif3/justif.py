#! /usr/bin/python
import sys
from typing import Final
from abc import ABC, abstractmethod

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
        self.__ram: dict[int, int] = {}

    def get_memory_value(self, index: list) -> int:
        logger.critical("MEMORY: GET [{!r}]", index)
        offset = index[0]
        if type(offset) == type([]):
            offset = self.__ram[offset[0]]
        if offset not in self.__ram:
            self.__ram[offset] = 0
        result = self.__ram[offset]
        if len(index) == 2:
            offset = index[1]
            if type(offset) == type(0):
                result = result[offset]
            else:
                result = result[self.get_memory_value(offset)]
        logger.debug("MEMORY: GOT [{!r}]={!r}", index, result)
        return result

    def set_memory_value(self, index: list, value: int) -> int:
        #logger.critical("MEMORY: SET [{!r}]={!r}", index, value)
        offset = index[0]
        if type(offset) == type([]):
            offset = self.__ram[offset[0]]
        self.__ram[offset] = value
        logger.debug("MEMORY: SET [{!r}]={!r}", offset, value)
        return 0


memory: Final[Memory] = Memory()
root_sequence: list = []  # This will hold the root sequence of instructions.


class ExecutionContext:
    """A class to represent the execution context of the Justif language."""

    def __init__(self, root_sequence):
        self.memory: Memory = Memory()
        self.index: int = 0
        self.root_sequence: list[Instruction] = root_sequence



class Instruction(ABC):
    """A class to represent an instruction in the Justif language."""

    @abstractmethod
    def Execute(self, index: int) -> int:
        """Execute the instruction.

        Args:
            index (int): Optional index

        Returns:
            int: An integer that *MAY* have meaning in the context of the instruction.
        """

    def get_value(self, data: list | "Instruction", index: int) -> int | list[int]:
        """_summary_

        Args:
            data (_type_): _description_
            index (_type_): _description_

        Returns:
            int | list[int]: returns either the raw "byte" (int), or a list of raw "bytes" (int).
        """
        match data:
            case int():
                return data
            case str():
                return list([ord(c) for c in data]) + [0]
            case list():
                # aha! list is somewhat our marker for "begin an effective address"
                return memory.get_memory_value(data)
            case _ if isinstance(data, Instruction):
                return data.Execute(index)
            case _:
                raise RuntimeError(f"Bad type {type(data)} for assignment")

class IfInstruction(Instruction):
    """A class to represent a constant instruction in the Justif language"""

    def __init__(self, instructions_if_true: list[Instruction], instructions_if_false: list[Instruction], address: list | Instruction):
        self.__address: Final[list | Instruction] = address
        self.__instructions_if_true: list[Instruction] = instructions_if_true
        self.__instructions_if_false: list[Instruction] = instructions_if_false

    def Execute(self, index: int) -> int:
        if isinstance(self.__address, Instruction):
            logger.debug("Executing IF-Expression  {!r}=> INSTRUCTION", self.__address)
            result = self.__address.Execute(index)
        else:
            logger.debug("Executing IF-Expression  {!r}=> NOT INSTRUCTION", self.__address)
            result = memory.get_memory_value(self.__address)
        logger.debug("IF-Expression is {}, execute {}", result, self.__instructions_if_true if result else self.__instructions_if_false)
        if result:
            return ExecuteInstructionSequence(self.__instructions_if_true, index)
        else:
            return ExecuteInstructionSequence(self.__instructions_if_false, index)
    
class CheckIndexInstruction(Instruction):
    """A class to represent a constant instruction in the Justif language"""

    def __init__(self, value: list):
        self.__value: Final[list] = value

    def Execute(self, index: int) -> int:
        """Execute the constant instruction.

        Args:
            index (int): *ignored*

        Returns:
            int: returns the constant value.
        """
        return index == self.get_value(self.__value, index)
    
class ConstantInstruction(Instruction):
    """A class to represent a constant instruction in the Justif language"""

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
    """A class to represent an input instruction in the Justif language."""

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
    """A class to represent a recursion instruction in the Justif language."""

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
    """A class to represent a char output instruction in the Justif language."""

    def __init__(self, address: list):
        self.__value: Final[list] = address

    def Execute(self, _: int) -> int:
        """_summary_

        Args:
            index (int): *ignored*

        Returns:
            int: returns 1 always, indicating successful execution.
        """
        sys.stdout.write(chr(memory.get_memory_value(self.__value)))
        return 1


class OutputIntegerInstruction(Instruction):
    """A class to represent a char output instruction in the Justif language."""

    def __init__(self, address: list):
        self.__value: Final[list] = address

    def Execute(self, _: int) -> int:
        """_summary_

        Args:
            index (int): *ignored*

        Returns:
            int: returns 1 always, indicating successful execution.
        """
        print(str(memory.get_memory_value(self.__value)))
        return 1


class ComparisonInstruction(Instruction):
    """A class to represent a char output instruction in the Justif language."""

    def __init__(
        self, first: list, second: list, method_to_execute: str
    ):
        self.__first: Final[list] = first
        self.__second: Final[list] = second
        self.__method_to_execute: Final[str] = method_to_execute

    def Execute(self, index: int) -> int:
        a = self.get_value(self.__first, index)
        b = self.get_value(self.__second, index)
        match self.__method_to_execute:
            case "+":
                logger.debug("Executing less than comparison: {} < {}", a, b)
                return a < b
            case "-":
                logger.debug("Executing equal to comparison: {} == {}", a, b)
                return a == b
            case "*":
                logger.debug("Executing greater than comparison: {} > {}", a, b)
                return a > b
            case "/":
                logger.debug("Executing not equal to comparison: {} != {}", a, b)
                return a != b
            case _:
                logger.error("Unknown comparison method: {}", self.__method_to_execute)
                raise RuntimeError(
                    f"Unknown comparison method: {self.__method_to_execute}"
                )


class MemsetInstruction(Instruction):
    """A class to represent a char output instruction in the Justif language."""

    def __init__(self, source: list, target: list, method_to_execute: str):
        self.__source: Final[list] = source
        self.__target: Final[list] = target
        self.__method_to_execute: Final[str] = method_to_execute

    def Execute(self, index: int) -> int:
        match self.__method_to_execute:
            case "=":
                return memory.set_memory_value(
                    self.__target,
                    self.get_value(self.__source, index))
            case "+":
                return memory.set_memory_value(
                    self.__target,
                    memory.get_memory_value(self.__target) + self.get_value(self.__source, index))
            case "-":
                return memory.set_memory_value(
                    self.__target,
                    memory.get_memory_value(self.__target) - self.get_value(self.__source, index))
            case "*":
                return memory.set_memory_value(
                    self.__target,
                    memory.get_memory_value(self.__target) * self.get_value(self.__source, index))
            case "/":
                return memory.set_memory_value(
                    self.__target,
                    memory.get_memory_value(self.__target) // self.get_value(self.__source, index))
            case _:
                logger.error("Unknown memset method: {}", self.__method_to_execute)
                raise RuntimeError(f"Unknown memset method: {self.__method_to_execute}")


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
    """A parser for the Justif language."""

    def __init__(self):
        self.expression: str = ""
        self.__pos: int = 0
        self.__nums: list[int] = [-1, -1]

    def Parse(self, expression: str) -> list[Instruction] | None:
        """Parse the Justif expression into a sequence of instructions.

        Args:
            expression (str): A valid justif expression / program.

        Returns:
            list[Instruction]: The instructions parsed from the expression.
        """
        self.expression = expression
        self.__pos = 0
        self.__nums = [-1, -1]
        return self.__parse_instructions()

    def __skip_whitespaces(self) -> None:
        """Skip whitespace characters in the expression.
        This method advances the position in the expression until a non-whitespace character is found.
        """
        try:
            while (
                self.expression[self.__pos]
                in " \r\nABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
            ):
                self.__pos += 1
        except IndexError:
            pass

    def __save_state(self) -> tuple[int, list[int]]:
        """Push the current parser position and intermediate numbers onto a stack.

        Returns:
            tuple[int, list[int]]: (current position, copy of __nums)
        """
        return self.__pos, self.__nums[:]

    def __restore_state(self, previously_saved_pos: tuple[int, list[int]]) -> None:
        """Restore the previously saved position and numbers from a local variable

        Args:
            s (_tytuple[int, list[int]]pe_):(previous position, copy of previous __nums)
        """
        self.__pos = previously_saved_pos[0]
        self.__nums = previously_saved_pos[1]

    def __get_char(self) -> str:
        """Get the character at the current position

        Returns:
            str: character at the current position or '\0' if out of bounds.
        """
        self.__skip_whitespaces()
        try:
            result = self.expression[self.__pos]
            assert isinstance(result, str), "Expected a string character"
            logger.debug("__get_char[{}]: {!r}", self.__pos, result)
            return result
        except IndexError:
            pass
        return "\0"

    def __skip_char(self, expression: str) -> bool:
        """_summary_

        Args:
            expression (_type_): _description_

        Returns:
            _type_: _description_
        """
        self.__skip_whitespaces()
        try:
            if self.expression[self.__pos : self.__pos + len(expression)] == expression:
                self.__pos += len(expression)
                return True
        except IndexError:
            pass
        return False

    def __is_index(self) :
        state = self.__save_state()
        if self.__skip_char("~"):
            v: list | None  = self.__dec_int()
            if v is None:
                v = self.__indirect_memory_access()
            if v is not None:
                return CheckIndexInstruction(v)
        self.__restore_state(state)

    def __cmp_instruction(self) -> Instruction | None:
        state = self.__save_state()
        c = self.__get_char()
        if c in "+-*/":
            self.__pos += 1
            m = self.__indirect_memory_access()
            if m is not None and self.__skip_char("="):
                v: list | None = self.__dec_int()
                if v is None:
                    v = self.__indirect_memory_access()
                if v is not None:
                    return ComparisonInstruction(m, v, c)
        self.__restore_state(state)
        return None

    def __if(self) -> Instruction | None:
        """Parse an if instruction from the expression.

        Returns:
            Instruction | None: An IfInstruction if a valid if condition is found, otherwise None.
        """
        state = self.__save_state()
        m: list | Instruction | None = self.__indirect_memory_access()
        if m is None:
            m = self.__cmp_instruction()
        if m is None:
            m = self.__recursion()
        if m is None:
            m = self.__is_index()
        if m is not None and self.__skip_char("?"):
            if_true = self.__parse_instructions()
            if if_true and self.__skip_char(":"):
                if_false = self.__parse_instructions()
                if if_false:
                    return IfInstruction(if_true, if_false, m)
        self.__restore_state(state)
        return None

    def __io_input(self) -> InputInstruction | None:
        """Parse an input instruction from the expression.

        Returns:
            InputInstruction | None: An InputInstruction if a valid input is found, otherwise None.
        """
        state = self.__save_state()
        if self.__skip_char("<"):
            address = self.__indirect_memory_access()
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
            address: list = self.__indirect_memory_access()
            if address is not None:
                return OutputCharInstruction(address)

        elif self.__skip_char("!"):
            address: list = self.__indirect_memory_access()
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
            self.__if,
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
        return None

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

    def __string(self) -> str | None:
        """Get a string from the current expression.

        Raises:
            SyntaxError: Raised if the string is not properly terminated.

        Returns:
            str | None: The string parsed from the expression, or None if no string is found.
        """
        if self.__skip_char('"'):
            startpos = self.__pos
            while 1:
                c = self.__get_char()
                if c == "\0":
                    raise SyntaxError("Expected end-of-string")
                self.__pos += 1
                if c == '"':
                    result = self.expression[startpos : self.__pos - 1]
                    logger.critical("Parsed string: {!r}", result)
                    return result
        return None

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
        m = self.__indirect_memory_access()
        if m:
            c = self.__get_char()
            if c in "=+-*/":
                self.__pos += 1
                d: list | None = self.__dec_int()
                if d is None:
                    d = self.__string()
                if d is None:
                    d = self.__indirect_memory_access()
                if d is not None:
                    return MemsetInstruction(d, m, c)
        self.__restore_state(state)
        return None

    def __indirect_memory_access(self) -> list | None:
        """Indirect memory access parsing. Can be as deeply nested as you want.

        Raises:
            SyntaxError: Raised if the syntax is incorrect.

        Returns:
            list | None: Nested list. Can be a list of ints, or lists of ints, or lists of lis
        """
        state = self.__save_state()
        if self.__skip_char("."):
            d: int | list | None = self.__dec_int()
            if d is None:
                d = self.__indirect_memory_access()
            if d is not None:
                result: list = [d]
                while self.__skip_char("!"):
                    number: int | list | None = self.__dec_int()
                    if number is None:
                        number = self.__indirect_memory_access()
                        if number is None:
                            raise SyntaxError("Expected decint after '!'")
                    result.append(number)
                return result
        self.__restore_state(state)
        return None

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
            self.__pos += 1
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
