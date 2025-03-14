class Instruction:
    def __init__(self, op, dst=None, src1=None, src2=None, mem_addr=None):
        self.op = op
        self.dst = dst
        self.src1 = src1
        self.src2 = src2
        self.mem_addr = mem_addr
        self.issue_cycle = -1
        self.execute_start_cycle = -1
        self.execute_complete_cycle = -1
        self.write_result_cycle = -1
        self.status = "Not issued"

    def __str__(self):
        if self.op == "LD":
            return f"{self.op} R{self.dst}, {self.mem_addr}"
        elif self.op == "ST":
            return f"{self.op} {self.mem_addr}, R{self.src1}"
        elif self.op == "NOP":
            return f"{self.op}"
        else:
            return f"{self.op} R{self.dst}, R{self.src1}, R{self.src2}"

    def get_latency(self):
        latencies = {
            "IADD": 6,
            "ISUB": 6,
            "IMUL": 12,
            "FADD": 18,
            "FSUB": 18,
            "FMUL": 30,
            "LD": 1,
            "ST": 1,
            "AND": 1,
            "OR": 1,
            "XOR": 1,
            "NOP": 1
        }
        return latencies.get(self.op, 1)


class ReservationStation:
    def __init__(self, name, op_type):
        self.name = name
        self.op_type = op_type
        self.busy = False
        self.op = None
        self.vj = None
        self.vk = None
        self.qj = None
        self.qk = None
        self.dest = None
        self.a = None
        self.instruction_index = None
        self.remaining_cycles = 0

    def __str__(self):
        if not self.busy:
            return f"{self.name}: idle"
        return f"{self.name}: busy, op={self.op}, Vj={self.vj}, Vk={self.vk}, Qj={self.qj}, Qk={self.qk}, dest={self.dest}, A={self.a}, cycles left={self.remaining_cycles}"


class LoadStoreBuffer:
    def __init__(self, name):
        self.name = name
        self.busy = False
        self.op = None
        self.address = None
        self.vj = None  # Register value to store (for ST)
        self.qj = None  # Reservation station producing value (for ST)
        self.dest = None  # Register to load into (for LD)
        self.instruction_index = None
        self.remaining_cycles = 0

    def __str__(self):
        if not self.busy:
            return f"{self.name}: idle"
        return f"{self.name}: busy, op={self.op}, addr={self.address}, Vj={self.vj}, Qj={self.qj}, dest={self.dest}, cycles left={self.remaining_cycles}"


class RegisterStatus:
    def __init__(self, num_registers=32):
        self.regs = [None] * num_registers 

    def __str__(self):
        result = "Register Status:\n"
        for i, reg in enumerate(self.regs):
            if reg is not None:
                result += f"R{i}: {reg}\n"
        return result


class RegisterFile:
    def __init__(self, num_registers=32):
        self.values = [0] * num_registers

    def __str__(self):
        result = "Register File:\n"
        for i, val in enumerate(self.values):
            result += f"R{i}: {val}\n"
        return result


class Memory:
    def __init__(self, size=1024):
        self.data = [0] * size

    def read(self, address):
        return self.data[address]

    def write(self, address, value):
        self.data[address] = value


class ReorderBuffer:
    def __init__(self, size=16):
        self.entries = [{"valid": False, "instruction": None, "state": None, "destination": None, "value": None} for _ in range(size)]
        self.head = 0  # Points to oldest instruction
        self.tail = 0  # Points to next free entry
        self.size = size
        self.count = 0

    def is_full(self):
        return self.count == self.size

    def is_empty(self):
        return self.count == 0

    def add_instruction(self, instruction):
        if self.is_full():
            return False

        self.entries[self.tail]["valid"] = True
        self.entries[self.tail]["instruction"] = instruction
        self.entries[self.tail]["state"] = "issued"
        self.entries[self.tail]["destination"] = instruction.dst
        self.entries[self.tail]["value"] = None

        entry_index = self.tail
        self.tail = (self.tail + 1) % self.size
        self.count += 1
        return entry_index

    def update_state(self, entry_index, state, value=None):
        if self.entries[entry_index]["valid"]:
            self.entries[entry_index]["state"] = state
            if value is not None:
                self.entries[entry_index]["value"] = value

    def commit(self, reg_file, memory):
        if self.is_empty() or self.entries[self.head]["state"] != "completed":
            return None

        entry = self.entries[self.head]
        instruction = entry["instruction"]
        
        # Update architectural state
        if instruction.op != "ST" and instruction.op != "NOP":
            if instruction.dst is not None:
                reg_file.values[instruction.dst] = entry["value"]
        elif instruction.op == "ST":
            memory.write(instruction.mem_addr, entry["value"])
        
        # Mark entry as invalid
        self.entries[self.head]["valid"] = False
        committed_instr = instruction
        
        # Update head pointer
        self.head = (self.head + 1) % self.size
        self.count -= 1
        
        return committed_instr

    def __str__(self):
        result = "Reorder Buffer:\n"
        current = self.head
        for i in range(self.count):
            entry = self.entries[current]
            result += f"Entry {current}: {entry['instruction']} - {entry['state']}"
            if entry['value'] is not None:
                result += f", value={entry['value']}"
            result += "\n"
            current = (current + 1) % self.size
        return result

class TomasuloProcessor:
    def __init__(self):
        # Initialize components
        self.memory = Memory()
        self.reg_file = RegisterFile()
        self.reg_status = RegisterStatus()
        
        self.reservation_stations = {
            "IADD1": ReservationStation("IADD1", ["IADD", "ISUB"]),
            "IADD2": ReservationStation("IADD2", ["IADD", "ISUB"]),
            "IMUL1": ReservationStation("IMUL1", ["IMUL"]),
            "FADD1": ReservationStation("FADD1", ["FADD", "FSUB"]),
            "FMUL1": ReservationStation("FMUL1", ["FMUL"]),
            "LOGIC1": ReservationStation("LOGIC1", ["AND", "OR", "XOR"]),
        }
        
        self.load_buffers = {
            "LD1": LoadStoreBuffer("LD1"),
            "LD2": LoadStoreBuffer("LD2"),
        }
        
        self.store_buffers = {
            "ST1": LoadStoreBuffer("ST1"),
            "ST2": LoadStoreBuffer("ST2"),
        }
        
        # Create reorder buffer
        self.rob = ReorderBuffer()
        
        self.completed_instructions = []
        
        self.cycle = 0
        self.pc = 0
        self.program = []
        self.history = {}  # To store the state of the processor at each cycle

    def load_program(self, program):
        self.program = program
        self.pc = 0

    def issue_instruction(self):
        if self.pc >= len(self.program):
            return False
        
        instruction = self.program[self.pc]
        
        # Check if ROB is full
        if self.rob.is_full():
            return False
        
        station = None
        rob_entry = None
        
        if instruction.op == "LD":
            for buf_name, buf in self.load_buffers.items():
                if not buf.busy:
                    station = buf
                    break
        elif instruction.op == "ST":
            for buf_name, buf in self.store_buffers.items():
                if not buf.busy:
                    station = buf
                    break
        elif instruction.op == "NOP":
            rob_entry = self.rob.add_instruction(instruction)
            instruction.issue_cycle = self.cycle
            instruction.status = "Issued"
            self.pc += 1
            return True
        else:
            for rs_name, rs in self.reservation_stations.items():
                if not rs.busy and instruction.op in rs.op_type:
                    station = rs
                    break
        
        if station is None and instruction.op != "NOP":
            return False  
        
        rob_entry = self.rob.add_instruction(instruction)
        
        instruction.issue_cycle = self.cycle
        instruction.status = "Issued"
        
        if instruction.op != "NOP":
            station.busy = True
            station.op = instruction.op
            station.instruction_index = self.pc
            station.remaining_cycles = instruction.get_latency()
            
            if instruction.op == "LD":
                station.op = "LD"
                station.address = instruction.mem_addr
                station.dest = instruction.dst
                self.reg_status.regs[instruction.dst] = station.name
            elif instruction.op == "ST":
                station.op = "ST"
                station.address = instruction.mem_addr
                if self.reg_status.regs[instruction.src1] is None:
                    station.vj = self.reg_file.values[instruction.src1]
                    station.qj = None
                else:
                    station.vj = None
                    station.qj = self.reg_status.regs[instruction.src1]
            else:
                station.dest = instruction.dst
                
                if self.reg_status.regs[instruction.src1] is None:
                    station.vj = self.reg_file.values[instruction.src1]
                    station.qj = None
                else:
                    station.vj = None
                    station.qj = self.reg_status.regs[instruction.src1]
                
                if self.reg_status.regs[instruction.src2] is None:
                    station.vk = self.reg_file.values[instruction.src2]
                    station.qk = None
                else:
                    station.vk = None
                    station.qk = self.reg_status.regs[instruction.src2]
                
                self.reg_status.regs[instruction.dst] = station.name
        
        self.pc += 1
        return True

    def execute_instructions(self):
        for station_name, station in list(self.reservation_stations.items()) + list(self.load_buffers.items()) + list(self.store_buffers.items()):
            if station.busy:
                instruction = self.program[station.instruction_index]

                ready_to_execute = instruction.execute_start_cycle == -1
                
                if isinstance(station, ReservationStation):
                    ready_to_execute = ready_to_execute and station.qj is None and station.qk is None
                elif isinstance(station, LoadStoreBuffer) and station.op == "ST":
                    ready_to_execute = ready_to_execute and station.qj is None

                if ready_to_execute:
                    instruction.execute_start_cycle = self.cycle
                    instruction.status = "Executing"

                if instruction.execute_start_cycle != -1:
                    station.remaining_cycles -= 1

                    # If execution is complete
                    if station.remaining_cycles <= 0:
                        instruction.execute_complete_cycle = self.cycle
                        instruction.status = "Completed Execution"

                        # Calculate result
                        result = None
                        if instruction.op == "LD":
                            result = self.memory.read(station.address)
                        elif instruction.op == "ST":
                            result = station.vj  # Value to store
                        elif instruction.op == "IADD":
                            result = station.vj + station.vk
                        elif instruction.op == "ISUB":
                            result = station.vj - station.vk
                        elif instruction.op == "IMUL":
                            result = station.vj * station.vk
                        elif instruction.op == "FADD":
                            result = station.vj + station.vk
                        elif instruction.op == "FSUB":
                            result = station.vj - station.vk
                        elif instruction.op == "FMUL":
                            result = station.vj * station.vk
                        elif instruction.op == "AND":
                            result = station.vj & station.vk
                        elif instruction.op == "OR":
                            result = station.vj | station.vk
                        elif instruction.op == "XOR":
                            result = station.vj ^ station.vk
                        
                        self.completed_instructions.append({
                            "station": station,
                            "result": result,
                            "instruction": instruction
                        })
                        
        for i, instruction in enumerate(self.program):
            if instruction.op == "NOP" and instruction.issue_cycle != -1 and instruction.execute_start_cycle == -1:
                instruction.execute_start_cycle = self.cycle
                instruction.status = "Executing"
                instruction.execute_complete_cycle = self.cycle
                instruction.write_result_cycle = self.cycle
                instruction.status = "Written Result"
                
                for j in range(self.rob.size):
                    if self.rob.entries[j]["valid"] and self.rob.entries[j]["instruction"] is instruction:
                        self.rob.update_state(j, "completed", 0)
                        break

    def write_result(self):
        if not self.completed_instructions:
            return
        
        completed = self.completed_instructions.pop(0)
        station = completed["station"]
        result = completed["result"]
        instruction = completed["instruction"]
        
        instruction.write_result_cycle = self.cycle
        instruction.status = "Written Result"
        
        rob_index = None
        for i in range(self.rob.size):
            if self.rob.entries[i]["valid"] and self.rob.entries[i]["instruction"] is instruction:
                self.rob.update_state(i, "completed", result)
                rob_index = i
                break
        
        station.busy = False
        
        for rs_name, rs in self.reservation_stations.items():
            if rs.busy:
                if rs.qj == station.name:
                    rs.qj = None
                    rs.vj = result
                if rs.qk == station.name:
                    rs.qk = None
                    rs.vk = result
        
        for buf in list(self.load_buffers.values()) + list(self.store_buffers.values()):
            if buf.busy and buf.qj == station.name:
                buf.qj = None
                buf.vj = result
                
        if instruction.dst is not None and instruction.op != "ST":
            if self.reg_status.regs[instruction.dst] == station.name:
                self.reg_status.regs[instruction.dst] = None

    def commit_instructions(self):
        committed_instr = self.rob.commit(self.reg_file, self.memory)
        if committed_instr:
            print(f"Committed: {committed_instr}")
            return True
        return False

    def print_status(self):
        print(f"Cycle {self.cycle}:")
        print("Register File:", self.reg_file)
        print("Reservation Stations:")
        for rs_name, rs in self.reservation_stations.items():
            print(rs)
        print("Load Buffers:")
        for buf_name, buf in self.load_buffers.items():
            print(buf)
        print("Store Buffers:")
        for buf_name, buf in self.store_buffers.items():
            print(buf)
        print("Reorder Buffer:", self.rob)
        print("Completed Instructions:", len(self.completed_instructions))
        print("\n")

    def run(self, max_cycles=100):
        theoretical_cycles = self.calculate_theoretical_cycles()
        print(f"Theoretical minimum cycles (with unlimited resources): {theoretical_cycles}")
        
        print_frequency = 10 
        
        while (self.pc < len(self.program) or 
               any(rs.busy for rs in self.reservation_stations.values()) or 
               any(buf.busy for buf in self.load_buffers.values()) or 
               any(buf.busy for buf in self.store_buffers.values()) or 
               not self.rob.is_empty() or 
               self.completed_instructions) and self.cycle < max_cycles:
            
            if self.cycle % print_frequency == 0:
                self.print_status()
                
            for _ in range(2):  # Allow issuing up to 2 instructions per cycle
                if not self.issue_instruction():
                    break
                    
            # Execute all instructions that are ready
            self.execute_instructions()
            
            # Process all completed instructions in write_result()
            while self.completed_instructions:
                self.write_result()
                
            for _ in range(2):  # Allow committing up to 2 instructions per cycle
                committed = self.commit_instructions()
                if not committed:
                    break
                    
            self.cycle += 1
            
        # Print final state
        self.print_status()
            
        if self.cycle >= max_cycles:
            print(f"Reached maximum cycle count of {max_cycles}. Execution terminated.")
        else:
            print(f"Program completed in {self.cycle} cycles.")
            print(f"Theoretical minimum: {theoretical_cycles} cycles")
            print(f"Efficiency ratio: {theoretical_cycles/self.cycle:.2f} (higher is better)")
            
        print("\n===== EXECUTION SUMMARY =====")
        print("Instruction Set Executed:")
        for i, instr in enumerate(self.program):
            print(f"{i}: {instr}")
            
        print("\nFinal Register Values:")
        changed_regs = set()
        for instr in self.program:
            if instr.op != "ST" and instr.op != "NOP" and instr.dst is not None:
                changed_regs.add(instr.dst)
        
        for reg in sorted(changed_regs):
            print(f"R{reg}: {self.reg_file.values[reg]}")
            
        print("\nData Flow Analysis:")
        for i, instr in enumerate(self.program):
            print(f"Instruction {i}: {instr}")
            if instr.op == "LD":
                print(f"  Loaded value {self.reg_file.values[instr.dst]} from memory address {instr.mem_addr}")
            elif instr.op == "ST":
                print(f"  Stored value {self.memory.data[instr.mem_addr]} to memory address {instr.mem_addr}")
            elif instr.op in ["IADD", "IMUL", "FADD", "FMUL", "FSUB", "AND", "OR", "XOR"]:
                src1_val = "unknown" if instr.execute_start_cycle == -1 else "computed"
                src2_val = "unknown" if instr.execute_start_cycle == -1 else "computed"
                print(f"  Operation: {instr.op} using registers R{instr.src1}={src1_val}, R{instr.src2}={src2_val}")
                print(f"  Result: R{instr.dst} = {self.reg_file.values[instr.dst]}")
                
        print("\nExecution Timeline:")
        print("Instruction | Issue | Execute Start | Execute Complete | Write Result")
        print("-" * 70)
        for i, instr in enumerate(self.program):
            issue = instr.issue_cycle if instr.issue_cycle != -1 else "N/A"
            exec_start = instr.execute_start_cycle if instr.execute_start_cycle != -1 else "N/A"
            exec_complete = instr.execute_complete_cycle if instr.execute_complete_cycle != -1 else "N/A"
            write = instr.write_result_cycle if instr.write_result_cycle != -1 else "N/A"
            print(f"{i:11d} | {issue:5} | {exec_start:13} | {exec_complete:16} | {write:11}")
        
        print("\nInstruction Latencies:")
        for i, instr in enumerate(self.program):
            if instr.execute_complete_cycle != -1 and instr.execute_start_cycle != -1:
                latency = instr.execute_complete_cycle - instr.execute_start_cycle + 1
                print(f"Instruction {i}: {instr.op} - {latency} cycles")
            else:
                print(f"Instruction {i}: {instr.op} - not executed")
        
        print("===============================")

    def calculate_theoretical_cycles(self):
        reg_ready_cycle = {i: 0 for i in range(32)}
        
        max_cycle = 0
        for idx, instr in enumerate(self.program):
            ready_cycle = idx  # In-order issue
            
            # Check when source registers are ready
            if instr.op != "LD" and instr.op != "NOP":
                if instr.src1 is not None:
                    ready_cycle = max(ready_cycle, reg_ready_cycle.get(instr.src1, 0))
                if instr.src2 is not None and instr.op != "ST":
                    ready_cycle = max(ready_cycle, reg_ready_cycle.get(instr.src2, 0))
            
            # Calculate when instruction finishes
            finish_cycle = ready_cycle + instr.get_latency()
            
            # Update destination register availability
            if instr.dst is not None and instr.op != "ST":
                reg_ready_cycle[instr.dst] = finish_cycle
            
            max_cycle = max(max_cycle, finish_cycle)
        
        return max_cycle + 1 


processor = TomasuloProcessor()

for i in range(32):
    processor.reg_file.values[i] = i + 5

for i in range(200):
    processor.memory.data[i] = i * 2 + 10

processor.memory.data[38] = 45 
processor.memory.data[41] = 72  
processor.memory.data[53] = 120  
processor.memory.data[38 + 44] = 200  

program = [
    # load,r0,32,r2 -> r0 = MEM[32 + value_in_r2]
    Instruction('LD', dst=0, mem_addr=32 + processor.reg_file.values[2]),
    
    # load,r4,32,r2 -> r4 = MEM[32 + value_in_r2]
    Instruction('LD', dst=4, mem_addr=32 + processor.reg_file.values[2]),
    
    # load,r2,44,r3 -> r2 = MEM[44 + value_in_r3]
    Instruction('LD', dst=2, mem_addr=44 + processor.reg_file.values[3]),
    
    # imul,r0,r2,r4 -> r0 = r2 * r4
    Instruction('IMUL', dst=0, src1=2, src2=4),
    
    # iadd,r8,r2,r6 -> r8 = r2 + r6
    Instruction('IADD', dst=8, src1=2, src2=6),
    
    # fmul,r10,r0,r6 -> r10 = r0 * r6
    Instruction('FMUL', dst=10, src1=0, src2=6),
    
    # fadd,r6,r8,r2 -> r6 = r8 + r2
    Instruction('FADD', dst=6, src1=8, src2=2),
]

print("===== INITIAL MEMORY STATE =====")
print(f"Memory[{32 + processor.reg_file.values[2]}] = {processor.memory.data[32 + processor.reg_file.values[2]]}")
print(f"Memory[{44 + processor.reg_file.values[3]}] = {processor.memory.data[44 + processor.reg_file.values[3]]}")

processor.load_program(program)

processor.run(max_cycles=100)
