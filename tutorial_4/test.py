from main import Processor

def test_vliw_processor():
    """
    Test function to check different hazards and register overflow conditions
    in the VLIW processor implementation.
    """
    print("\n=== VLIW PROCESSOR HAZARD TESTING ===\n")
    
    
    # 1. WAW (Write After Write) Hazard Test
    with open("test_waw_hazard.txt", "w") as f:
        f.write("LD R1 M0\n")      
        f.write("ADD R1 R2 R3\n")   
        f.write("MUL R4 R5 R6\n")   
        f.write("LD R7 M1\n")       

    # 2. RAW (Read After Write) Hazard Test
    with open("test_raw_hazard.txt", "w") as f:
        f.write("ADD R1 R2 R3\n")   
        f.write("MUL R4 R1 R5\n")   
        f.write("LD R6 M0\n")       
        f.write("AND R7 R8 R9\n")   

    # 3. WAR (Write After Read) Hazard Test
    with open("test_war_hazard.txt", "w") as f:
        f.write("MUL R4 R1 R2\n")   
        f.write("LD R1 M0\n")       
        f.write("AND R5 R6 R7\n")   
        f.write("LD R8 M1\n")       

    # 4. Multiple Hazards Test
    with open("test_multiple_hazards.txt", "w") as f:
        f.write("LD R1 M0\n")        
        f.write("ADD R2 R1 R3\n")     
        f.write("MUL R1 R4 R5\n")    
        f.write("FADD F1 F2 F3\n")    
        f.write("AND R6 R2 R7\n")     
        f.write("FMUL F4 F1 F5\n")    
        f.write("LD R2 M1\n")        

    # 5. Register Type Conflicts (INT vs FP)
    with open("test_register_types.txt", "w") as f:
        f.write("LD R1 M0\n")        
        f.write("LD F1 M1\n")       
        f.write("ADD R2 F1 R3\n")    
        f.write("FADD F2 R1 F3\n")    
        f.write("MUL R4 R1 R3\n")     
        f.write("FMUL F4 F1 F3\n")   

    # 6. Functional Unit Contention Test
    with open("test_functional_unit.txt", "w") as f:
        f.write("ADD R1 R2 R3\n")     
        f.write("ADD R4 R5 R6\n")     
        f.write("MUL R7 R8 R9\n")    
        f.write("FADD F1 F2 F3\n")  
        f.write("FMUL F4 F5 F6\n")   
        f.write("LD R10 M0\n")       
        f.write("AND R11 R12 R13\n")  

    # 7. Long Execution Test (for checking execution timing)
    with open("test_execution_timing.txt", "w") as f:
        f.write("FMUL F1 F2 F3\n")    
        f.write("FADD F4 F5 F6\n")    
        f.write("MUL R1 R2 R3\n")
        f.write("ADD R4 R5 R6\n")     
        f.write("LD R7 M0\n")    
        f.write("AND R8 R9 R10\n")    

    # Run tests
    test_files = [
        "test_waw_hazard.txt", 
        "test_raw_hazard.txt", 
        "test_war_hazard.txt",
        "test_multiple_hazards.txt", 
        "test_register_types.txt",
        "test_functional_unit.txt", 
        "test_execution_timing.txt"
    ]
    
    processor = Processor()
    
    for test_file in test_files:
        print(f"\n\n{'='*80}")
        print(f"TESTING: {test_file}")
        print(f"{'='*80}")
        
        try:
            processor = Processor()
            processor.load_program(test_file)
            processor.simulate()
        except Exception as e:
            print(f"Error in test {test_file}: {e}")
    
    print("\n=== COMPLETED ALL HAZARD TESTS ===")

def enhance_processor_validation():
    # Store the original parse_instruction method
    original_parse = Processor.parse_instruction
    
    # Define the enhanced parse_instruction method
    def enhanced_parse_instruction(self, line):
        parts = line.strip().split()
        if not parts:
            return None
        
        # Basic validation checks
        if parts[0] not in ['LD', 'SD', 'ADD', 'FADD', 'MUL', 'FMUL', 'AND', 'OR', 'NOP']:
            print(f"ERROR: Invalid opcode {parts[0]}")
            return None
        
        # Register type validation
        def validate_register(reg):
            if reg is None:
                return True
            
            if reg.startswith('R'):
                try:
                    num = int(reg[1:])
                    if num < 0 or num > 15:
                        print(f"ERROR: Integer register {reg} out of range (0-15)")
                        return False
                    return 'INT'
                except ValueError:
                    print(f"ERROR: Invalid register format {reg}")
                    return False
            elif reg.startswith('F'):
                try:
                    num = int(reg[1:])
                    if num < 0 or num > 15:
                        print(f"ERROR: FP register {reg} out of range (0-15)")
                        return False
                    return 'FP'
                except ValueError:
                    print(f"ERROR: Invalid register format {reg}")
                    return False
            elif reg.startswith('M'):
                try:
                    num = int(reg[1:])
                    if num < 0 or num > 9:
                        print(f"ERROR: Memory address {reg} out of range (0-9)")
                        return False
                    return 'MEM'
                except ValueError:
                    print(f"ERROR: Invalid memory address format {reg}")
                    return False
            else:
                print(f"ERROR: Unknown register/memory type {reg}")
                return False
        
        # Call the original method to get the instruction
        instruction = original_parse(self, line)
        
        # Additional validation for register types
        if instruction and instruction.opcode != 'NOP':
            dest_type = validate_register(instruction.dest)
            src1_type = validate_register(instruction.src1)
            src2_type = validate_register(instruction.src2)
            
            if not all(x for x in [dest_type, src1_type, src2_type] if x is not False):
                return None  # Invalid register format
            
            # Check for register type consistency
            if instruction.opcode in ['ADD', 'MUL', 'AND', 'OR']:
                if dest_type != 'INT' or (src1_type != 'INT' and src1_type != 'MEM') or (src2_type != 'INT' and src2_type != 'MEM'):
                    print(f"ERROR: Integer operation {instruction.opcode} requires INT registers")
                    return None
            elif instruction.opcode in ['FADD', 'FMUL']:
                if dest_type != 'FP' or (src1_type != 'FP' and src1_type != 'MEM') or (src2_type != 'FP' and src2_type != 'MEM'):
                    print(f"ERROR: FP operation {instruction.opcode} requires FP registers")
                    return None
            elif instruction.opcode == 'LD':
                if (dest_type == 'INT' and src1_type != 'MEM') or (dest_type == 'FP' and src1_type != 'MEM'):
                    print(f"ERROR: Load operation requires memory source")
                    return None
            elif instruction.opcode == 'SD':
                if src1_type != 'MEM' or (dest_type != 'INT' and dest_type != 'FP'):
                    print(f"ERROR: Store operation requires memory destination")
                    return None
        
        return instruction
    
    Processor.parse_instruction = enhanced_parse_instruction
    print("Enhanced processor validation capabilities installed.")


if __name__ == "__main__":
    print("Starting VLIW processor hazard and validation tests...")

    test_vliw_processor()
