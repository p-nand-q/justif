#! /usr/bin/python
"""_summary_"""
from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from pprint import pformat
from typing import Final

import typer
from loguru import logger

# pylint: disable=line-too-long

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


class Address:
    """An address in memory, which can be either direct or indirect."""

    def __init__(self, address: int, direct: bool = True):
        self.address: Final[int] = address
        self.direct: Final[bool] = direct

    @property
    def indirect(self) -> bool:
        """Check if the address is indirect."""
        return not self.direct

    def __repr__(self):
        if self.direct:
            return f"DirectAddress({self.address})"
        else:
            return f"IndirectAddress({self.address})"


class EffectiveAddress:
    """An effective address in memory, which consists of a base address and an optional offset."""

    def __init__(self, address: Address, offset: Address | None = None):
        self.address: Final[Address] = address
        """The base address in memory."""
        self.offset: Final[Address | None] = offset
        """An optional offset to the base address, which can be another EffectiveAddress."""

    def __repr__(self):
        if self.offset is None:
            return f"EffectiveAddress({self.address})"
        else:
            return f"EffectiveAddress({self.address}, offset={self.offset})"

class Memory:
    """A simple memory class to store and retrieve values."""

    def __init__(self):
        self.__ram: dict[int, int | list[int]] = {}
        """Our very strange multi-dimensional memory."""

    def read_ea(self, ea: EffectiveAddress) -> int:
        """_summary_

        Args:
            index (list): _description_

        Returns:
            int: _description_
        """
        logger.debug("MEMORY: GET {!r}", ea)
        first_address: int = 0

        if ea.address.indirect:
            temp_value = self.__ram[ea.address.address]
            assert isinstance(temp_value, int)
            first_address = temp_value
        else:
            first_address = ea.address.address
        assert isinstance(first_address, int), "Offset must be an int"

        if first_address not in self.__ram:
            self.__ram[first_address] = 0

        temp_result = self.__ram[first_address]
        actual_result: int = 0

        if isinstance(temp_result, list):
            assert ea.offset is not None, "Effective address must have an offset"

            if ea.offset.direct:
                actual_result = temp_result[ea.offset.address]

            else:
                # one more level of indirection
                temp_ea = EffectiveAddress(Address(ea.offset.address, direct=True))
                actual_result = temp_result[self.read_ea(temp_ea)]

        else:
            assert ea.offset is None, "Effective address must not have an offset"
            assert isinstance(
                temp_result, int
            ), "Expected an int for the first part of the index"
            actual_result = temp_result

        assert isinstance(actual_result, int), "Expected an int as the result"
        logger.debug("MEMORY: GET {!r} RETURNS {}", ea, actual_result)
        return actual_result

    def write_ea(self, ea: EffectiveAddress, value: int | list[int]) -> int:
        """_summary_

        Args:
            index (list): _description_
            value (int | list[int]): _description_

        Returns:
            int: _description_
        """
        logger.debug("MEMORY: SET {!r}={!r}", ea, value)

        assert isinstance(
            ea, EffectiveAddress
        ), "Effective address must be an instance of EffectiveAddress"

        # target type is either an int
        assert isinstance(value, int) or isinstance(
            value, list
        ), "Value must be an int or a list of ints"

        if not ea.address.direct:
            offset = self.__ram[ea.address.address]
        else:
            offset = ea.address.address

        assert isinstance(value, int) or isinstance(value, list)
        assert isinstance(offset, int), "Offset must be an int"

        self.__ram[offset] = value
        logger.debug("MEMORY: ACTUALLY, SET self.__ram[{!r}]={!r}", offset, value)
        return 0


class ExecutionContext(Memory):
    """_summary_"""

    def __init__(self):
        super().__init__()
        self.current_index: int = 0
        self.root_sequence: list[Instruction] = []


class Instruction(ABC):
    """A class to represent an instruction in the Justif language."""

    @abstractmethod
    def execute(self, context: ExecutionContext, index: int) -> int:
        """execute the instruction.

        Args:
            index (int): Optional index

        Returns:
            int: An integer that *MAY* have meaning in the context of the instruction.
        """

    def get_value(self, data, context: ExecutionContext, index: int) -> int | list[int]:
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
            case EffectiveAddress():
                return context.read_ea(data)
            case _ if isinstance(data, Instruction):
                return data.execute(context, index)
            case _:
                raise RuntimeError(f"Bad type {type(data)} for assignment")


class IfInstruction(Instruction):
    """A class to represent a constant instruction in the Justif language"""

    def __init__(
        self,
        instructions_if_true: list[Instruction],
        instructions_if_false: list[Instruction],
        address: EffectiveAddress | Instruction,
    ):
        self.__address = address
        self.__instructions_if_true = instructions_if_true
        self.__instructions_if_false = instructions_if_false

    def __repr__(self):
        return f"IfInstruction(addres={self.__address!r}, if_true:\n{pformat(self.__instructions_if_true)},\nif_false:\n{pformat(self.__instructions_if_false)})"

    def execute(self, context: ExecutionContext, index: int) -> int:
        if isinstance(self.__address, Instruction):
            result = self.__address.execute(context, index)
        else:
            ea = self.__address
            assert ea is not None
            # logger.critical("would be using ea: {}", ea)
            # logger.critical("but actually is using address: {}", self.__address)
            result = context.read_ea(ea)
        logger.debug("IF-Expression is {}", result)
        if result:
            return execute_instructions(self.__instructions_if_true, context, index)
        else:
            return execute_instructions(self.__instructions_if_false, context, index)


class CheckIndexInstruction(Instruction):
    """A class to represent a constant instruction in the Justif language"""

    def __init__(self, value: int | EffectiveAddress):
        self.__value = value

    def __repr__(self):
        return f"CheckIndexInstruction(value={self.__value!r})"

    def execute(self, context: ExecutionContext, index: int) -> int:
        """execute the constant instruction.

        Args:
            index (int): *ignored*

        Returns:
            int: returns the constant value.
        """
        return index == self.get_value(self.__value, context, index)


class ConstantInstruction(Instruction):
    """A class to represent a constant instruction in the Justif language"""

    def __init__(self, decint: int):
        self.__value = decint

    def __repr__(self):
        return f"ConstantInstruction(value={self.__value!r})"

    def execute(self, context: ExecutionContext, index: int) -> int:
        """execute the constant instruction.

        Args:
            index (int): *ignored*

        Returns:
            int: returns the constant value.
        """
        return self.__value


class InputInstruction(Instruction):
    """A class to represent an input instruction in the Justif language."""

    def __init__(self, address: EffectiveAddress):
        self.__address = address
        """Address at which to store the input value."""

    def __repr__(self):
        return f"InputInstruction(index={self.__address!r})"

    def execute(self, context: ExecutionContext, index: int) -> int:
        """execute the input instruction.

        Args:
            index (int): *ignored*
        """
        raise RuntimeError("Not implemented yet")


class RecurseInstruction(Instruction):
    """A class to represent a recursion instruction in the Justif language."""

    def __init__(self, index: int):
        assert isinstance(index, int), "Index must be an integer"
        self.__index = index

    def __repr__(self):
        return f"RecurseInstruction(index={self.__index!r})"

    def execute(self, context: ExecutionContext, index: int) -> int:
        """_summary_

        Args:
            index (_type_): _description_

        Returns:
            _type_: _description_
        """
        logger.debug("Call self recursively with index {}", self.__index)
        return execute_instructions(context.root_sequence, context, self.__index)


class OutputCharInstruction(Instruction):
    """A class to represent a char output instruction in the Justif language."""

    def __init__(self, address: EffectiveAddress):
        self.__address = address

    def __repr__(self):
        return f"OutputCharInstruction(value={self.__address!r})"

    def execute(self, context: ExecutionContext, index: int) -> int:
        """_summary_

        Args:
            index (int): *ignored*

        Returns:
            int: returns 1 always, indicating successful execution.
        """
        sys.stdout.write(chr(context.read_ea(self.__address)))
        return 1


class OutputIntegerInstruction(Instruction):
    """A class to represent a char output instruction in the Justif language."""

    def __init__(self, address: EffectiveAddress):
        self.__address = address

    def __repr__(self):
        return f"OutputIntegerInstruction(value={self.__address!r})"

    def execute(self, context: ExecutionContext, index: int) -> int:
        """_summary_

        Args:
            index (int): *ignored*

        Returns:
            int: returns 1 always, indicating successful execution.
        """
        print(str(context.read_ea(self.__address)))
        return 1


class ComparisonInstruction(Instruction):
    """A class to represent a char output instruction in the Justif language."""

    def __init__(
        self,
        first: EffectiveAddress,
        second: int | EffectiveAddress,
        method_to_execute: str,
    ):
        self.__first = first
        self.__second = second
        self.__method_to_execute: Final[str] = method_to_execute

    def __repr__(self) -> str:
        return f"ComparisonInstruction(first={self.__first}, second={self.__second}, method_to_execute={self.__method_to_execute})"

    def execute(self, context: ExecutionContext, index: int) -> int:
        a = self.get_value(self.__first, context, index)
        assert isinstance(a, int)
        b = self.get_value(self.__second, context, index)
        assert isinstance(b, int)
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

    def __init__(
        self,
        source: int | str | EffectiveAddress,
        target: EffectiveAddress,
        method_to_execute: str,
    ):
        self.__source = source
        self.__target = target
        self.__method_to_execute: Final[str] = method_to_execute

    def __repr__(self) -> str:
        return f"MemsetInstruction(source={self.__source}, target={self.__target}, method_to_execute={self.__method_to_execute!r})"

    def execute(self, context: ExecutionContext, index: int) -> int:

        second_value = self.get_value(self.__source, context, index)

        match self.__method_to_execute:
            case "=":
                return context.write_ea(
                    self.__target, self.get_value(self.__source, context, index)
                )
            case "+":
                assert isinstance(second_value, int)
                first_value = self.get_value(self.__target, context, index)
                assert isinstance(first_value, int)
                return context.write_ea(
                    self.__target,
                    first_value + second_value,
                )
            case "-":
                assert isinstance(second_value, int)
                first_value = self.get_value(self.__target, context, index)
                assert isinstance(first_value, int)
                return context.write_ea(
                    self.__target,
                    first_value - second_value,
                )
            case "*":
                assert isinstance(second_value, int)
                first_value = self.get_value(self.__target, context, index)
                assert isinstance(first_value, int)
                return context.write_ea(
                    self.__target,
                    first_value * second_value,
                )
            case "/":
                assert isinstance(second_value, int)
                first_value = self.get_value(self.__target, context, index)
                assert isinstance(first_value, int)
                return context.write_ea(
                    self.__target,
                    first_value // second_value,
                )
            case _:
                logger.error("Unknown memset method: {}", self.__method_to_execute)
                raise RuntimeError(f"Unknown memset method: {self.__method_to_execute}")


def execute_instructions(
    instructions: list[Instruction], context: ExecutionContext, index: int
) -> int:
    """execute a sequence of instructions.

    Args:
        instructions (list[Instruction]): _description_
        index (int): _description_

    Returns:
        int: _description_
    """
    # logger.critical("Executing instructions with index: {}", index)
    result = 0
    for instruction in instructions:
        logger.debug(">>: {}", instruction)
        result = instruction.execute(context, index)
    return result


class JustifParser:
    """A parser for the Justif language."""

    def __init__(self):
        self.expression: str = ""
        self.__pos: int = 0
        self.__nums: list[int] = [-1, -1]

    def parse_expression(self, expression: str) -> list[Instruction] | None:
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

    def __is_index(self):
        state = self.__save_state()
        if self.__skip_char("~"):
            v: int | EffectiveAddress | None = self.__dec_int()
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
            m: EffectiveAddress | None = self.__indirect_memory_access()
            if m is not None and self.__skip_char("="):
                v: EffectiveAddress | int | None = self.__dec_int()
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
        m: EffectiveAddress | Instruction | None = self.__indirect_memory_access()
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
            address = self.__indirect_memory_access()
            if address is not None:
                return OutputCharInstruction(address)

        elif self.__skip_char("!"):
            address = self.__indirect_memory_access()
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
                    logger.debug("Parsed string: {!r}", result)
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
                d: int | str | EffectiveAddress | None = self.__dec_int()
                if d is None:
                    d = self.__string()
                if d is None:
                    d = self.__indirect_memory_access()
                if d is not None:
                    return MemsetInstruction(d, m, c)
        self.__restore_state(state)
        return None

    def __get_address(self) -> int | list | None:
        decval = self.__dec_int()
        if decval is not None:
            return decval
        d = self.__internal_indirect_memory_access()
        if d is None:
            return None
        assert isinstance(d, list)
        assert len(d) == 1, "Expected a single element list"
        assert isinstance(d[0], int), "Expected an int in the list"
        return d

    def __internal_indirect_memory_access(self) -> list | None:
        """Indirect memory access parsing. Can be as deeply nested as you want.

        Raises:
            SyntaxError: Raised if the syntax is incorrect.

        Returns:
            list | None: Nested list. Can be a list of ints, or lists of ints, or lists of lis
        """
        state = self.__save_state()
        if self.__skip_char("."):
            d: int | list | None = self.__get_address()
            if d is not None:
                result: list = [d]
                # maybe one level of indirection
                if self.__skip_char("!"):
                    offset = self.__get_address()
                    if offset is not None:
                        result.append(offset)
                    else:
                        raise SyntaxError("Expected an offset after '!'")
                return result
        self.__restore_state(state)
        return None

    def __indirect_memory_access(self) -> EffectiveAddress | None:
        """Indirect memory access parsing. Can be as deeply nested as you want.

        Raises:
            SyntaxError: Raised if the syntax is incorrect.

        Returns:
            list | None: Nested list. Can be a list of ints, or lists of ints, or lists of lis
        """
        something = self.__internal_indirect_memory_access()
        if something is not None:
            assert isinstance(something, list)
            assert len(something) >= 1, "Effective address must have at least one element"
            assert len(something) <= 2, "Effective address must have at most two elements"

            if isinstance(something[0], int):
                address = Address(something[0], direct=True)
            else:
                assert isinstance(something[0], list), "First element must be an int or a list"
                assert len(something[0]) == 1, "First element must be a single-element list"
                assert isinstance(something[0][0], int), "First element must be an int"
                # ok, good, indirect address
                address = Address(something[0][0], direct=False)

            offset: Address | None = None
            if len(something) == 2:
                assert something[1] is not None, "Second element must not be None"
                assert isinstance(something[1], list)
                assert len(something[1]) == 1, "Second element must be a single-element list"
                assert isinstance(
                    something[1][0], int
                ), "First element of second item must be an int"
                offset = Address(something[1][0], direct=False)

            return EffectiveAddress(address, offset)

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


def main(filenames: list[str], debug: bool = False):
    """_summary_

    Args:
        filename (str): _description_
        debug (bool, optional): _description_. Defaults to False.
    """
    # Configure logger: colors yes, no timestamp, no function/line info
    logger.remove()  # Remove default handler
    level = "DEBUG" if debug else "INFO"
    logger.add(
        sys.stderr,
        level=level,
        format="<level>{level: <8}</level> | <level>{message}</level>",
        colorize=True,
    )

    j = JustifParser()
    for filename in filenames:
        logger.info(
            "---------------------------- {} ----------------------------", filename
        )
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()

        rs = j.parse_expression(content)
        if rs is not None:
            context = ExecutionContext()
            context.root_sequence = rs
            execute_instructions(rs, context, 1)
            print()
        else:
            logger.error("Unable to parse {}", filename)


if __name__ == "__main__":
    typer.run(main)
