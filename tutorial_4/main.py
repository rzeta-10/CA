class Instruction:
    def __init__(self, opcode, dest=None, src1=None, src2=None):
        self.opcode = opcode
        self.dest = dest
        self.src1 = src1
        self.src2 = src2
        self.issue_cycle = None
        self.execute_start = None
        self.execute_complete = None
        self.commit_cycle = None
        
        # Set latency based on opcode
        self.latency = {
            'LD': 1,
            'SD': 1,
            'ADD': 6,
            'FADD': 18,
            'MUL': 12,
            'FMUL': 30,
            'AND': 1,
            'OR': 1,
            'NOP': 1
        }[opcode]

class Processor:
    def __init__(self):
        self.instructions = []
        self.registers = {}
        for i in range(32):
            if i < 16:  # INT REGISTERS
                self.registers[f'R{i}'] = None
            else:  # FP REGISTERS
                self.registers[f'F{i-16}'] = None
        self.memory = {f'M{i}': None for i in range(10)}
        self.current_cycle = 1
        self.executing = []
        self.completed = []
        
        # VLIW functional units
        self.functional_units = {
            'INT_ALU': 1,  # Integer ALU (ADD, SUB)
            'INT_MUL': 1,  # Integer Multiply
            'FP_ALU': 1,   # FP Add/Sub
            'FP_MUL': 1,   # FP Multiply
            'MEM': 1,      # Load/Store unit
            'LOGIC': 1     # Logic unit (AND/OR/XOR)
        }
        
    def get_functional_unit(self, opcode):
        if opcode in ['ADD', 'SUB']:
            return 'INT_ALU'
        elif opcode == 'MUL':
            return 'INT_MUL'
        elif opcode == 'FADD':
            return 'FP_ALU'
        elif opcode == 'FMUL':
            return 'FP_MUL'
        elif opcode in ['LD', 'SD']:
            return 'MEM'
        elif opcode in ['AND', 'OR', 'XOR']:
            return 'LOGIC'
        return None

    def parse_instruction(self, line):
        parts = line.strip().split()
        if not parts:
            return None
            
        instruction = None
        if parts[0] == 'NOP':
            instruction = Instruction('NOP')
            print(f"Parsed NOP instruction")
        elif len(parts) == 4:  # Three operand instruction
            opcode = parts[0]
            dest = parts[1].strip(',')
            src1 = parts[2].strip(',')
            src2 = parts[3].strip(',')
            instruction = Instruction(opcode, dest, src1, src2)
            print(f"Parsed {opcode} instruction: {dest} ← {src1}, {src2} (ALU/Compute)")
        elif len(parts) == 3:  # Load/Store instruction
            opcode = parts[0]
            if opcode == 'LD':
                dest = parts[1].strip(',')
                src1 = parts[2]
                instruction = Instruction(opcode, dest, src1)
                print(f"Parsed LD instruction: {dest} ← {src1} (Memory Load)")
            else:  # Store
                dest = parts[1].strip(',')
                src1 = parts[2]
                instruction = Instruction(opcode, dest, src1)
                print(f"Parsed SD instruction: {dest} → {src1} (Memory Store)")
        
        if instruction:
            unit = self.get_functional_unit(instruction.opcode)
            if unit:
                print(f"  → Assigned to functional unit: {unit}")
        
        return instruction

    def load_program(self, filename):
        print("\n=== INSTRUCTION PARSING ===")
        with open(filename, 'r') as f:
            for line in f:  
                if line.strip():
                    inst = self.parse_instruction(line)
                    if inst:
                        self.instructions.append(inst)
        print("===========================\n")

    def can_issue(self, inst):
        # Check for WAW and WAR hazards
        if inst.dest:
            for ex_inst in self.executing:
                if ex_inst.dest == inst.dest:  # WAW 
                    return False
                if inst.src1 and ex_inst.dest == inst.src1:  # RAW
                    return False
                if inst.src2 and ex_inst.dest == inst.src2:  # RAW
                    return False
        return True

    def format_instruction(self, inst):
        if inst.opcode == 'NOP':
            return "NOP"
        elif inst.opcode in ['LD', 'SD']:
            return f"{inst.opcode} {inst.dest or ''} {inst.src1 or ''}"
        else:
            return f"{inst.opcode} {inst.dest or ''} {inst.src1 or ''} {inst.src2 or ''}"

    def simulate(self):
        print("=== CYCLE-BY-CYCLE EXECUTION ===")
        instruction_queue = self.instructions.copy()
        
        # Track used functional units per cycle
        used_units = {unit: False for unit in self.functional_units}
        
        while instruction_queue or self.executing:
            print(f"╔════════════════════════════════════════════════════════════════╗")
            print(f"║ CYCLE {self.current_cycle:<57}║")
            print(f"╠════════════════════════════════════════════════════════════════╣")
            
            # Reset functional unit usage for new cycle
            used_units = {unit: False for unit in self.functional_units}
            
            # Try to issue instructions in parallel (VLIW packet)
            issued_this_cycle = []
            remaining_queue = instruction_queue.copy()
            
            issued_packet = False
            if remaining_queue:
                print(f"║ INSTRUCTION PACKET:                                            ║")
                print(f"╠════════════════════════════════════════════════════════════════╣")
                issued_packet = True
            
            while remaining_queue:
                inst = remaining_queue[0]
                unit = self.get_functional_unit(inst.opcode)
                
                if (unit is None or not used_units[unit]) and self.can_issue(inst):
                    inst.issue_cycle = self.current_cycle
                    inst.execute_start = self.current_cycle + 1  # Start execution next cycle
                    inst.execute_complete = inst.execute_start + inst.latency  # Complete after latency cycles
                    self.executing.append(inst)
                    issued_this_cycle.append(inst)
                    if unit:
                        used_units[unit] = True
                    formatted_inst = self.format_instruction(inst)
                    unit_str = f"[{unit}]" if unit else " "
                    if unit_str != " ":
                        print(f"║ {formatted_inst:<48} {unit_str:<10}    ║")
                    else:
                        print(f"║ {formatted_inst:<58} {unit_str:<10}    ║")
                else:
                    # Add NOP for unused functional units
                    if not any(used_units.values()):
                        nop = Instruction('NOP')
                        nop.issue_cycle = self.current_cycle
                        nop.execute_start = self.current_cycle + 1  # Even NOPs have 1 cycle delay
                        nop.execute_complete = nop.execute_start + nop.latency
                        nop.commit_cycle = nop.execute_complete
                        print(f"║ NOP                                                [NONE]      ║")
                    break
                
                remaining_queue.pop(0)
                instruction_queue.pop(0)
            
            # Check for completing instructions
            completed_this_cycle = []
            for inst in self.executing:
                if inst.execute_complete == self.current_cycle:
                    inst.commit_cycle = self.current_cycle
                    completed_this_cycle.append(inst)
            
            # Print completed instructions
            if completed_this_cycle:
                if issued_packet:
                    print(f"╠════════════════════════════════════════════════════════════════╣")
                print(f"║ COMPLETED INSTRUCTIONS:                                        ║")
                print(f"╠════════════════════════════════════════════════════════════════╣")
                for inst in completed_this_cycle:
                    formatted_inst = self.format_instruction(inst)
                    print(f"║ {formatted_inst:<58}     ║")
            
            # Remove completed instructions
            for inst in completed_this_cycle:
                self.executing.remove(inst)
                self.completed.append(inst)
            
            if not instruction_queue and not self.executing:
                break
                
            self.current_cycle += 1
            print(f"╚════════════════════════════════════════════════════════════════╝")
        
        print(f"╚════════════════════════════════════════════════════════════════╝")
        print("\n=== FINAL EXECUTION SUMMARY ===")
        print("╔════════════════════════════════════════════════════════════════════════════════╗")
        print("║ Instruction         │ Issue │ Start │ Complete │ Commit │ Latency │ Unit       ║")
        print("╠════════════════════════════════════════════════════════════════════════════════╣")
        for inst in self.completed:
            formatted_inst = self.format_instruction(inst)
            unit = self.get_functional_unit(inst.opcode) or "NONE"
            print(f"║ {formatted_inst:<18} │ {inst.issue_cycle:^5} │ {inst.execute_start:^5} │ {inst.execute_complete:^8} │ {inst.commit_cycle:^6} │ {inst.latency:^7} │ {unit:<10}  ║")
        print("╚════════════════════════════════════════════════════════════════════════════════╝")
        print(f"\nTotal cycles: {self.current_cycle - 1}")

if __name__ == "__main__":
    processor = Processor()
    processor.load_program("instructions.txt")
    processor.simulate()