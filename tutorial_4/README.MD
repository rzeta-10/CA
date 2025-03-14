# VLIW Processor Simulator

This repository contains a Python implementation of a simple VLIW (Very Long Instruction Word) processor simulator.  The simulator demonstrates basic VLIW concepts, including instruction-level parallelism, hazard detection (RAW, WAW, WAR), and functional unit allocation.

## Features

* **Instruction Set:**  Supports a limited instruction set including:
    * `LD`: Load from memory.
    * `SD`: Store to memory.
    * `ADD`: Integer addition.
    * `FADD`: Floating-point addition.
    * `MUL`: Integer multiplication.
    * `FMUL`: Floating-point multiplication.
    * `AND`: Bitwise AND.
    * `OR`: Bitwise OR.
    * `NOP`: No operation.

* **VLIW Execution:**  Simulates the parallel execution of instructions in VLIW packets.

* **Hazard Detection:** Detects and handles data hazards (RAW, WAW, WAR) to ensure correct program execution.

* **Functional Unit Allocation:**  Allocates instructions to available functional units (INT_ALU, INT_MUL, FP_ALU, FP_MUL, MEM, LOGIC) based on instruction type and availability.

* **Cycle-by-Cycle Simulation:** Provides a detailed, cycle-by-cycle breakdown of instruction execution, showing instruction issuing, execution start, completion, and commitment.

* **Register File and Memory:**  Manages a register file and a small memory space.

## Usage

1.  **Run the simulator:** Execute `main.py`.  The simulator will load instructions from `instructions.txt` (you'll need to create this file; see the example below).
2.  **Create an instruction file:** The `instructions.txt` file should contain one instruction per line.  Each instruction follows the format:
    *   `LD R1, M0` (Load from memory location M0 into register R1)
    *   `ADD R1, R2, R3` (Add R2 and R3, store result in R1)
    *   and so on...

**Example `instructions.txt`:**
* `LD R1, M0 `
* `ADD R2, R1, R3` 
* `MUL R4, R5, R6`


##  Output

The simulator outputs a detailed trace of the execution, including:

*   Instruction parsing.
*   Cycle-by-cycle execution details (instructions issued, completed, functional units used).
*   Final execution summary (instruction timing, functional units).


