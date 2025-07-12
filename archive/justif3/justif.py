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

    def __getitem__(self, index: list[int]) -> int:
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
        logger.debug("GET memory[{}]={}", offset, result)
        return result

    def __setitem__(self, index: int, value: int):
        offset = index[0]
        if type(offset) == type([]):
            offset = self.__memory[offset[0]]
        self.__memory[offset] = value
        logger.debug("SET memory[{}]={}", offset, value)
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

    def LessThan(self, index: int) -> int:
        """_summary_

        Args:
            index (_type_): _description_

        Returns:
            _type_: _description_
        """
        a = self.Value(self.a, index)
        b = self.Value(self.b, index)
        logger.debug("Test if {} is less than {}", a, b)
        return a < b

    def Equal(self, index: int) -> int:
        """_summary_

        Args:
            index (_type_): _description_

        Returns:
            _type_: _description_
        """
        return self.Value(self.a, index) == self.Value(self.b, index)

    def GreaterThan(self, index: int) -> int:
        """_summary_

        Args:
            index (_type_): _description_

        Returns:
            _type_: _description_
        """
        return self.Value(self.a, index) > self.Value(self.b, index)

    def NotEqual(self, index: int) -> int:
        return not (self.Value(self.a, index) == self.Value(self.b, index))

    def Recurse(self, index: int) -> int:
        """_summary_

        Args:
            index (_type_): _description_

        Returns:
            _type_: _description_
        """
        global root_sequence
        logger.debug("Call self recursively with index {}", self.index)
        return ExecuteInstructionSequence(root_sequence, self.index)

    def Output(self, index: int) -> int:
        """_summary_

        Args:
            index (_type_): _description_

        Returns:
            _type_: _description_
        """
        return 1, sys.stdout.write(chr(memory[self.address]))

    def OutputInteger(self, *args) -> None:
        """_summary_

        Args:
            index (_type_): _description_
        """
        logger.debug("Output integer at address {} using args {}", self.address, repr(args))
        print(str(memory[self.address]))

    def Constant(self, index: int) -> int:
        """_summary_

        Args:
            index (_type_): _description_

        Returns:
            _type_: _description_
        """
        return self.value

    def Input(self, index: int) -> int:
        """_summary_

        Args:
            index (_type_): _description_
        """
        raise "ERROR, not implemented yet"

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
        return self.INSTRUCTIONS()

    def SkipWhitespaces(self):
        """_summary_"""
        try:
            while (
                self.expression[self.pos]
                in " \r\nABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
            ):
                self.pos += 1
        except:
            pass

    def PushPos(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return self.pos, self.__nums[:]

    def PopPos(self, s):
        """_summary_

        Args:
            s (_type_): _description_
        """
        self.pos = s[0]
        self.__nums = s[1]

    def GetChar(self, pos: int=0) -> str:
        """_summary_

        Args:
            pos (int, optional): _description_. Defaults to 0.

        Returns:
            _type_: _description_
        """
        self.SkipWhitespaces()
        try:
            result = self.expression[self.pos + pos]
            assert isinstance(result, str), "Expected a string character"
            logger.debug("GetChar: {!r}", result)
            return result
        except IndexError:
            pass
        except:
            logger.exception("GetChar failed at position {}", self.pos + pos)
        return '\0'

    def parser_skip_char(self, expression: str) -> bool:
        """_summary_

        Args:
            expression (_type_): _description_

        Returns:
            _type_: _description_
        """
        self.SkipWhitespaces()
        try:
            if self.expression[self.pos : self.pos + len(expression)] == expression:
                self.pos += len(expression)
                return True
        except IndexError:
            pass
        return False

    def ISINDEX(self):
        pos = self.PushPos()
        if self.parser_skip_char("~"):
            value = self.parse_dec_int()
            if value is None:
                value = self.parse_memory_access()
            if value is not None:
                result = Instruction()
                result.value = value
                result.Execute = result.IsIndex
                return result
        self.PopPos(pos)

    def COMPARE(self):
        pos = self.PushPos()
        c = self.GetChar()
        if c in "+-*/":
            self.pos += 1
            m = self.parse_memory_access()
            if m is not None and self.parser_skip_char("="):
                v = self.parse_dec_int()
                if v is None:
                    v = self.parse_memory_access()
                if v is not None:
                    result = Instruction()
                    result.a = m
                    result.b = v
                    result.Execute = [
                        result.LessThan,
                        result.Equal,
                        result.GreaterThan,
                        result.NotEqual,
                    ]["+-*/".index(c)]
                    return result
        self.PopPos(pos)

    def IF(self):
        pos = self.PushPos()
        m = self.parse_memory_access()
        if m is None:
            m = self.COMPARE()
        if m is None:
            m = self.RECURSION()
        if m is None:
            m = self.ISINDEX()
        if m is not None and self.parser_skip_char("?"):
            if_true = self.INSTRUCTIONS()
            if if_true and self.parser_skip_char(":"):
                if_false = self.INSTRUCTIONS()
                if if_false:
                    result = Instruction()
                    result.address = m
                    result.if_true = if_true
                    result.if_false = if_false
                    result.Execute = result.If
                    return result
        self.PopPos(pos)

    def INPUT(self):
        pos = self.PushPos()
        if self.parser_skip_char("<"):
            address = self.parse_memory_access()
            if address:
                result = Instruction()
                result.address = address
                result.Execute = result.Input
                return result
        self.PopPos(pos)

    def OUTPUT(self):
        pos = self.PushPos()
        if self.parser_skip_char(">"):
            address = self.parse_memory_access()
            if address:
                result = Instruction()
                result.address = address
                result.Execute = result.Output
                return result
        elif self.parser_skip_char("!"):
            address = self.parse_memory_access()
            if address:
                result = Instruction()
                result.address = address
                result.Execute = result.OutputInteger
                return result
        self.PopPos(pos)

    def INSTRUCTIONS(self):
        pos = self.PushPos()
        instruction = self.INSTRUCTION()
        if instruction:
            result = []
            while 1:
                result.append(instruction)
                if self.parser_skip_char(","):
                    instruction = self.INSTRUCTION()
                    if instruction:
                        continue
                break
            return result
        self.PopPos(pos)

    def INSTRUCTION(self):
        pos = self.PushPos()
        for function in (
            self.IF,
            self.COMPARE,
            self.RECURSION,
            self.MEMSET,
            self.OUTPUT,
            self.INPUT,
            self.CONSTANT,
        ):
            instruction = function()
            if instruction is not None:
                return instruction
        self.PopPos(pos)

    def CONSTANT(self):
        decint = self.parse_dec_int()
        if decint is not None:
            result = Instruction()
            result.value = decint
            result.Execute = result.Constant
            return result

    def STRING(self):
        if self.parser_skip_char('"'):
            startpos = self.pos
            while 1:
                c = self.GetChar()
                if c == 0:
                    raise "ERROR, expected end-of-string"
                self.pos += 1
                if c == '"':
                    return self.expression[startpos : self.pos - 1]

    def RECURSION(self):
        pos = self.PushPos()
        if self.parser_skip_char("="):
            index = self.parse_dec_int()
            if index is not None:
                result = Instruction()
                result.index = index
                result.Execute = result.Recurse
                return result
        self.PopPos(pos)

    def MEMSET(self):
        pos = self.PushPos()
        m = self.parse_memory_access()
        if m:
            c = self.GetChar()
            if c in "=+-*/":
                self.pos += 1
                d = self.parse_dec_int()
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
        self.PopPos(pos)

    def parse_memory_access(self):
        """_summary_

        Raises:
            SyntaxError: _description_

        Returns:
            list[int] | None: _description_
        """
        pos = self.PushPos()
        if self.parser_skip_char("."):
            d = self.parse_dec_int()
            if d is None:
                d = self.parse_memory_access()
            if d is not None:
                result = [d]
                while self.parser_skip_char("!"):
                    number = self.parse_dec_int()
                    if number is None:
                        number = self.parse_memory_access()
                        if number is None:
                            raise SyntaxError("Expected decint after '!'")
                    result.append(number)
                return result
        self.PopPos(pos)

    def parse_dec_int(self) -> int | None:
        """Parse a decimal integer from the current position in the expression.
        If it is an integer, the scan position is advanced and the integer is returned.

        Returns:
            int | None: Either the parsed integer or None if parsing fails. 
        """
        number: int = 0
        if self.parser_skip_char("_"):
            return self.__nums[0]
        if self.parser_skip_char("$"):
            return self.__nums[1]
        success, digit = self.parse_dec_digit()
        if not success:
            return None

        while success:
            number *= 10
            number += digit
            success, digit = self.parse_dec_digit()
        self.__nums[1] = self.__nums[0]
        self.__nums[0] = number
        return number

    def parse_dec_digit(self) -> tuple[bool, int]:
        """Check if the current character is a decimal digit and if so, return its value.

        Returns:
            tuple[bool, int]: (success, digit_value)
        """
        c = self.GetChar()
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
