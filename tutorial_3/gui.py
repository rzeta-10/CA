import tkinter as tk
from tkinter import ttk, scrolledtext
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

########################################
# GLOBAL CONSTANTS
########################################
MEMORY_SIZE = 64 * 1024      # 64K words (not directly visualized)
BLOCK_SIZE = 16            # Block size: 16 words
CACHE_SIZE_WORDS = 2 * 1024  # L1: 2K words
L1_LINES = CACHE_SIZE_WORDS // BLOCK_SIZE  # = 128 lines

# For L2:
L2_SIZE_WORDS = 16 * 1024  # 16K words
TOTAL_L2_BLOCKS = L2_SIZE_WORDS // BLOCK_SIZE  # 1024 blocks
L2_WAYS = 4
L2_SETS = TOTAL_L2_BLOCKS // L2_WAYS  # 256 sets (we display sample of first 8 sets)

# Victim Cache capacity:
VICTIM_CAPACITY = 4

# Auto-run delay (milliseconds) between simulation steps
AUTO_DELAY = 100

########################################
# EXTENDED MULTI-LEVEL CACHE SIMULATOR
########################################

# CacheBlock for L1 and L2
class CacheBlock:
    def __init__(self, block_addr=None, valid=False, dirty=False):
        self.block_addr = block_addr  # base address (aligned to block; lower 4 bits are 0)
        self.valid = valid
        self.dirty = dirty

    def __str__(self):
        if self.valid:
            return f"{self.block_addr}"
        return ""

# L1: Direct-Mapped Cache
class DirectMappedCache:
    def __init__(self, size_words, block_size):
        self.block_size = block_size
        self.num_lines = size_words // block_size  # e.g., 2048/16 = 128
        self.lines = [CacheBlock() for _ in range(self.num_lines)]
        self.hits = 0
        self.misses = 0
        self.accesses = 0

    def index_for_block(self, block_addr):
        return (block_addr // self.block_size) % self.num_lines

    def lookup(self, block_addr):
        self.accesses += 1
        idx = self.index_for_block(block_addr)
        block = self.lines[idx]
        if block.valid and block.block_addr == block_addr:
            self.hits += 1
            return True
        else:
            self.misses += 1
            return False

    def insert(self, block_addr, operation='read'):
        idx = self.index_for_block(block_addr)
        old_block = self.lines[idx]
        evicted = None
        if old_block.valid:
            evicted = (old_block.block_addr, old_block.dirty)
        self.lines[idx] = CacheBlock(block_addr=block_addr, valid=True, dirty=(operation=='write'))
        return evicted

    def update_write(self, block_addr):
        idx = self.index_for_block(block_addr)
        self.lines[idx].dirty = True

# L2: 4-Way Set-Associative Cache
class SetAssociativeCache:
    def __init__(self, size_words, block_size, ways):
        self.block_size = block_size
        total_blocks = size_words // block_size
        self.num_sets = total_blocks // ways  # e.g., 1024/4 = 256
        self.ways = ways
        self.sets = [[CacheBlock() for _ in range(ways)] for _ in range(self.num_sets)]
        self.lru_counters = [[0]*ways for _ in range(self.num_sets)]
        self.global_counter = 0
        self.hits = 0
        self.misses = 0
        self.accesses = 0

    def index_for_block(self, block_addr):
        return (block_addr // self.block_size) % self.num_sets

    def lookup(self, block_addr, operation='read'):
        self.accesses += 1
        set_idx = self.index_for_block(block_addr)
        for j, block in enumerate(self.sets[set_idx]):
            if block.valid and block.block_addr == block_addr:
                self.hits += 1
                self.lru_counters[set_idx][j] = self.global_counter
                self.global_counter += 1
                if operation == 'write':
                    block.dirty = True
                return True
        self.misses += 1
        return False

    def insert(self, block_addr, operation='read'):
        set_idx = self.index_for_block(block_addr)
        for j, block in enumerate(self.sets[set_idx]):
            if not block.valid:
                self.sets[set_idx][j] = CacheBlock(block_addr=block_addr, valid=True, dirty=(operation=='write'))
                self.lru_counters[set_idx][j] = self.global_counter
                self.global_counter += 1
                return None
        # Use LRU replacement:
        lru_index = 0
        min_val = self.lru_counters[set_idx][0]
        for j in range(1, self.ways):
            if self.lru_counters[set_idx][j] < min_val:
                min_val = self.lru_counters[set_idx][j]
                lru_index = j
        evicted_block = self.sets[set_idx][lru_index]
        evicted = (evicted_block.block_addr, evicted_block.dirty)
        self.sets[set_idx][lru_index] = CacheBlock(block_addr=block_addr, valid=True, dirty=(operation=='write'))
        self.lru_counters[set_idx][lru_index] = self.global_counter
        self.global_counter += 1
        return evicted

# Victim Cache (Fully-Associative, 4 Blocks)
class VictimCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.blocks = []  # list of (block_addr, dirty)
        self.hits = 0
        self.misses = 0

    def lookup(self, block_addr):
        for i, (b_addr, dirty) in enumerate(self.blocks):
            if b_addr == block_addr:
                self.hits += 1
                victim_block = self.blocks.pop(i)
                return victim_block, True
        self.misses += 1
        return None, False

    def insert(self, block_addr, dirty):
        if len(self.blocks) >= self.capacity:
            self.blocks.pop(0)
        self.blocks.append((block_addr, dirty))

# Extended Multi-Level Cache Simulator
class MultiLevelCacheSimulator:
    def __init__(self):
        self.L1 = DirectMappedCache(size_words=2048, block_size=BLOCK_SIZE)
        self.L2 = SetAssociativeCache(size_words=L2_SIZE_WORDS, block_size=BLOCK_SIZE, ways=L2_WAYS)
        self.victim = VictimCache(capacity=VICTIM_CAPACITY)
        # For simplicity, write buffer and prefetch caches are not visualized.
        self.main_memory_accesses = 0
        self.L1_hits = 0
        self.victim_hits = 0
        self.L2_hits = 0
        self.total_accesses = 0

    def access(self, address, operation='read'):
        self.total_accesses += 1
        # Align the address to block boundary (clear lower 4 bits)
        block_addr = address & ~0xF
        # Check L1:
        if self.L1.lookup(block_addr):
            self.L1_hits += 1
            if operation == 'write':
                self.L1.update_write(block_addr)
            return "Hit in L1"
        # Check Victim Cache:
        victim_block, found = self.victim.lookup(block_addr)
        if found:
            self.victim_hits += 1
            self.L1.insert(block_addr, operation)
            return "Hit in Victim Cache"
        # Check L2:
        if self.L2.lookup(block_addr, operation):
            self.L2_hits += 1
            evicted = self.L1.insert(block_addr, operation)
            if evicted is not None:
                evicted_block, dirty = evicted
                self.victim.insert(evicted_block, dirty)
            return "Hit in L2"
        # Miss: fetch from Main Memory:
        self.main_memory_accesses += 1
        _ = self.L2.insert(block_addr, operation)
        evicted = self.L1.insert(block_addr, operation)
        if evicted is not None:
            evicted_block, dirty = evicted
            self.victim.insert(evicted_block, dirty)
        return "Miss – Fetched from Memory"

    def get_performance(self):
        total_hits = self.L1_hits + self.victim_hits + self.L2_hits
        hit_ratio = (total_hits / self.total_accesses) * 100 if self.total_accesses else 0
        miss_ratio = (self.main_memory_accesses / self.total_accesses) * 100 if self.total_accesses else 0
        return {
            "Total Accesses": self.total_accesses,
            "L1 Hits": self.L1_hits,
            "Victim Hits": self.victim_hits,
            "L2 Hits": self.L2_hits,
            "Main Memory Accesses": self.main_memory_accesses,
            "Hit Ratio (%)": hit_ratio,
            "Miss Ratio (%)": miss_ratio
        }

    def reset(self):
        self.__init__()

########################################
# GUI FOR EXTENDED MULTI-LEVEL CACHE SIMULATOR
########################################

class ExtendedCacheSimulatorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Extended Multi-Level Cache Simulator")
        self.geometry("1200x800")
        self.simulator = MultiLevelCacheSimulator()
        self.auto_samples_remaining = 0
        self.create_widgets()

    def create_widgets(self):
        # Top frame: Controls
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Label(top_frame, text="Access Count:").grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        self.access_count = tk.IntVar(value=20)
        self.access_entry = ttk.Entry(top_frame, textvariable=self.access_count, width=10)
        self.access_entry.grid(column=1, row=0, padx=5, pady=5)

        self.run_test_button = ttk.Button(top_frame, text="Run Random Access Test", command=self.run_test)
        self.run_test_button.grid(column=2, row=0, padx=5, pady=5)

        ttk.Label(top_frame, text="Auto Run Samples:").grid(column=3, row=0, padx=5, pady=5, sticky=tk.W)
        self.auto_samples = tk.IntVar(value=50)
        self.auto_entry = ttk.Entry(top_frame, textvariable=self.auto_samples, width=10)
        self.auto_entry.grid(column=4, row=0, padx=5, pady=5)

        self.run_auto_button = ttk.Button(top_frame, text="Run Auto Simulation", command=self.run_auto_simulation)
        self.run_auto_button.grid(column=5, row=0, padx=5, pady=5)

        self.reset_button = ttk.Button(top_frame, text="Reset Simulator", command=self.reset_simulator)
        self.reset_button.grid(column=6, row=0, padx=5, pady=5)

        # Display frame:
        display_frame = ttk.Frame(self)
        display_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # L1 Cache display:
        l1_frame = ttk.LabelFrame(display_frame, text="L1 Cache (Direct Mapped)")
        l1_frame.grid(column=0, row=0, padx=5, pady=5, sticky="nsew")
        self.l1_canvas = tk.Canvas(l1_frame, width=500, height=300, bg="white")
        self.l1_canvas.pack(fill=tk.BOTH, expand=True)
        self.l1_cols = 16
        self.l1_rows = 8
        self.l1_cell_width = 500 / self.l1_cols
        self.l1_cell_height = 300 / self.l1_rows

        # L2 Cache display (Sample: first 8 sets, 4 ways per set):
        l2_frame = ttk.LabelFrame(display_frame, text="L2 Cache (4-Way Set Associative, First 8 Sets)")
        l2_frame.grid(column=1, row=0, padx=5, pady=5, sticky="nsew")
        self.l2_canvas = tk.Canvas(l2_frame, width=400, height=300, bg="white")
        self.l2_canvas.pack(fill=tk.BOTH, expand=True)
        self.l2_rows = 8
        self.l2_cols = 4
        self.l2_cell_width = 400 / self.l2_cols
        self.l2_cell_height = 300 / self.l2_rows

        # Victim Cache display:
        victim_frame = ttk.LabelFrame(display_frame, text="Victim Cache (4 Blocks)")
        victim_frame.grid(column=2, row=0, padx=5, pady=5, sticky="nsew")
        self.victim_canvas = tk.Canvas(victim_frame, width=200, height=100, bg="white")
        self.victim_canvas.pack(fill=tk.BOTH, expand=True)
        self.victim_cols = 4
        self.victim_cell_width = 200 / self.victim_cols
        self.victim_cell_height = 100

        display_frame.columnconfigure(0, weight=1)
        display_frame.columnconfigure(1, weight=1)
        display_frame.columnconfigure(2, weight=1)

        # Metrics display:
        self.metrics_area = scrolledtext.ScrolledText(self, width=130, height=8)
        self.metrics_area.pack(side=tk.BOTTOM, padx=10, pady=5)

        # Draw initial grids:
        self.draw_l1_grid()
        self.draw_l2_grid()
        self.draw_victim_grid()

    def draw_l1_grid(self):
        self.l1_canvas.delete("all")
        self.l1_cells = {}
        for r in range(self.l1_rows):
            for c in range(self.l1_cols):
                x1 = c * self.l1_cell_width
                y1 = r * self.l1_cell_height
                x2 = x1 + self.l1_cell_width
                y2 = y1 + self.l1_cell_height
                idx = r * self.l1_cols + c
                rect = self.l1_canvas.create_rectangle(x1, y1, x2, y2, fill="lightgray", outline="black")
                self.l1_canvas.create_text(x1+self.l1_cell_width/2, y1+self.l1_cell_height/2, text="", font=("Arial", 8), tags=(f"l1_text{idx}",))
                self.l1_cells[idx] = rect

    def draw_l2_grid(self):
        self.l2_canvas.delete("all")
        self.l2_cells = {}
        for r in range(self.l2_rows):
            for c in range(self.l2_cols):
                x1 = c * self.l2_cell_width
                y1 = r * self.l2_cell_height
                x2 = x1 + self.l2_cell_width
                y2 = y1 + self.l2_cell_height
                idx = r * self.l2_cols + c
                rect = self.l2_canvas.create_rectangle(x1, y1, x2, y2, fill="lightyellow", outline="black")
                self.l2_canvas.create_text(x1+self.l2_cell_width/2, y1+self.l2_cell_height/2, text="", font=("Arial", 8), tags=(f"l2_text{idx}",))
                self.l2_cells[(r, c)] = rect

    def draw_victim_grid(self):
        self.victim_canvas.delete("all")
        self.victim_cells = {}
        for c in range(self.victim_cols):
            x1 = c * self.victim_cell_width
            y1 = 0
            x2 = x1 + self.victim_cell_width
            y2 = self.victim_cell_height
            rect = self.victim_canvas.create_rectangle(x1, y1, x2, y2, fill="lightgreen", outline="black")
            self.victim_canvas.create_text(x1+self.victim_cell_width/2, y1+self.victim_cell_height/2, text="", font=("Arial", 10), tags=(f"victim_text{c}",))
            self.victim_cells[c] = rect

    def update_l1_display(self):
        for idx in range(L1_LINES):
            block = self.simulator.L1.lines[idx]
            text = str(block) if block.valid else ""
            self.l1_canvas.itemconfigure(f"l1_text{idx}", text=text)

    def update_l2_display(self):
        # Display only first 8 sets (rows 0 to 7) and 4 ways per set.
        for r in range(self.l2_rows):
            for c in range(self.l2_cols):
                if r < self.simulator.L2.num_sets:
                    block = self.simulator.L2.sets[r][c]
                    text = str(block) if block.valid else ""
                else:
                    text = ""
                self.l2_canvas.itemconfigure(f"l2_text{r*self.l2_cols+c}", text=text)

    def update_victim_display(self):
        victim_list = self.simulator.victim.blocks
        for i in range(self.victim_cols):
            if i < len(victim_list):
                block_addr, dirty = victim_list[i]
                text = f"{block_addr}"
            else:
                text = ""
            self.victim_canvas.itemconfigure(f"victim_text{i}", text=text)

    def update_metrics_display(self):
        perf = self.simulator.get_performance()
        metrics_text = "\n".join([f"{key}: {value}" for key, value in perf.items()])
        self.metrics_area.delete("1.0", tk.END)
        self.metrics_area.insert(tk.END, metrics_text)

    def run_test(self):
        try:
            count = int(self.access_count.get())
        except ValueError:
            count = 20
        total_blocks = MEMORY_SIZE // BLOCK_SIZE
        access_sequence = [random.randint(0, total_blocks - 1) for _ in range(count)]
        for addr in access_sequence:
            self.simulator.access(addr, "read")
        self.update_l1_display()
        self.update_l2_display()
        self.update_victim_display()
        self.update_metrics_display()

    def run_auto_simulation(self):
        try:
            self.auto_samples_remaining = int(self.auto_samples.get())
        except ValueError:
            self.auto_samples_remaining = 50
        self.run_auto_step()

    def run_auto_step(self):
        if self.auto_samples_remaining <= 0:
            self.update_metrics_display()
            return
        total_blocks = MEMORY_SIZE // BLOCK_SIZE
        addr = random.randint(0, total_blocks - 1)
        self.simulator.access(addr, "read")
        self.auto_samples_remaining -= 1
        self.update_l1_display()
        self.update_l2_display()
        self.update_victim_display()
        self.update_metrics_display()
        self.after(AUTO_DELAY, self.run_auto_step)

    def reset_simulator(self):
        self.simulator.reset()
        self.update_l1_display()
        self.update_l2_display()
        self.update_victim_display()
        self.metrics_area.delete("1.0", tk.END)
        self.metrics_area.insert(tk.END, "Simulator reset.\n")

if __name__ == "__main__":
    app = ExtendedCacheSimulatorGUI()
    app.mainloop()
