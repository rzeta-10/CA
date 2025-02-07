import tkinter as tk
from tkinter import ttk, scrolledtext
import random
from collections import deque
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

class CacheLine:
    def __init__(self, tag=None, valid=False, dirty=False, lru_counter=0):
        self.tag = tag
        self.valid = valid
        self.dirty = dirty
        self.lru_counter = lru_counter

    def __str__(self):
        if self.valid:
            return f"Tag:{self.tag}"
        return ""

class FullyAssociativeCache:
    def __init__(self, cache_size_lines, replacement_policy='LRU'):
        self.cache_size_lines = cache_size_lines
        self.replacement_policy = replacement_policy
        self.cache = [CacheLine() for _ in range(self.cache_size_lines)]
        self.cache_lines_used = 0
        self.misses = 0
        self.searches = 0
        self.hits = 0
        self.lru_counter = 0

    def address_breakdown(self, address):
        block_offset_bits = 4
        block_offset_mask = (1 << block_offset_bits) - 1
        block_offset = address & block_offset_mask
        tag = address >> block_offset_bits
        return tag

    def search_cache(self, tag, access_index):
        self.searches += 1
        for i in range(len(self.cache)):
            line = self.cache[i]
            if line.valid and line.tag == tag:
                self.hits += 1
                if self.replacement_policy == 'LRU':
                    self.cache[i].lru_counter = self.lru_counter
                    self.lru_counter += 1
                return True
        return False

    def add_to_cache(self, tag):
        for i in range(self.cache_size_lines):
            if not self.cache[i].valid:
                self.cache[i] = CacheLine(tag=tag, valid=True, dirty=False)
                if self.replacement_policy == 'LRU':
                    self.cache[i].lru_counter = self.lru_counter
                    self.lru_counter += 1
                self.cache_lines_used += 1
                return

        if self.replacement_policy == 'FIFO':
            self._replace_fifo(tag)
        elif self.replacement_policy == 'LRU':
            self._replace_lru(tag)
        elif self.replacement_policy == 'Random':
            self._replace_random(tag)

    def _replace_fifo(self, tag):
        replaced_line = self.cache.pop(0)
        if replaced_line.dirty:
            pass

        self.cache.append(CacheLine(tag=tag, valid=True, dirty=False))
        if self.replacement_policy == 'LRU':
            self.cache[-1].lru_counter = self.lru_counter
            self.lru_counter += 1

    def _replace_lru(self, tag):
        lru_index = 0
        min_lru_counter = self.cache[0].lru_counter
        for i in range(1, self.cache_size_lines):
            if self.cache[i].lru_counter < min_lru_counter:
                min_lru_counter = self.cache[i].lru_counter
                lru_index = i

        if self.cache[lru_index].dirty:
            pass

        self.cache[lru_index] = CacheLine(tag=tag, valid=True, dirty=False)
        self.cache[lru_index].lru_counter = self.lru_counter
        self.lru_counter += 1

    def _replace_random(self, tag):
        replace_index = random.randint(0, self.cache_size_lines - 1)
        if self.cache[replace_index].dirty:
            pass
        self.cache[replace_index] = CacheLine(tag=tag, valid=True, dirty=False)
        if self.replacement_policy == 'LRU':
            self.cache[replace_index].lru_counter = self.lru_counter
            self.lru_counter += 1

    def access_memory(self, address, access_index, operation_type='read'):
        tag = self.address_breakdown(address)
        is_hit = self.search_cache(tag, access_index)
        if operation_type == 'write' and is_hit:
            for line in self.cache:
                if line.valid and line.tag == tag:
                    line.dirty = True
                    break
        if not is_hit:
            self.misses += 1
            self.add_to_cache(tag)
        return "Hit" if is_hit else "Miss"

    def simulate_accesses(self, access_sequence, operation_sequence=None):
        results = []
        if operation_sequence is None:
            operation_sequence = ['read'] * len(access_sequence)
        for i in range(len(access_sequence)):
            address = access_sequence[i]
            operation = operation_sequence[i]
            result = self.access_memory(address, i, operation)
            results.append((address, operation, result))
        return results

    def get_performance_metrics(self):
        searches = self.searches
        misses = self.misses
        hits = self.hits
        hit_ratio = (hits / searches) * 100 if searches else 0
        miss_ratio = (misses / searches) * 100 if searches else 0
        return {
            "searches": searches,
            "misses": misses,
            "hits": hits,
            "hit_ratio": hit_ratio,
            "miss_ratio": miss_ratio
        }

    def reset_metrics(self):
        self.misses = 0
        self.searches = 0
        self.hits = 0
        self.lru_counter = 0
        self.cache = [CacheLine() for _ in range(self.cache_size_lines)]
        self.cache_lines_used = 0

    def __str__(self):
        metrics = self.get_performance_metrics()
        cache_state_str = "Cache State:\n"
        for i in range(len(self.cache)):
            line = self.cache[i]
            cache_state_str += f"Line {i}: {line}, Valid={line.valid}, Dirty={line.dirty}, LRU Counter={line.lru_counter}\n"
        metrics_str = (
            "--- Performance Metrics ---\n"
            f"Searches: {metrics['searches']}\n"
            f"Misses: {metrics['misses']}\n"
            f"Hits: {metrics['hits']}\n"
            f"Hit Ratio: {metrics['hit_ratio']:.2f}%\n"
            f"Miss Ratio: {metrics['miss_ratio']:.2f}%\n"
            "--- Cache Content ---\n"
            f"{cache_state_str}"
        )
        return metrics_str

class CacheSimulatorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cache & Main Memory Simulation")
        self.geometry("1100x750")
        self.create_widgets()
        self.cache = FullyAssociativeCache(CAPACITY, replacement_policy="LRU")
        self.current_block_request = None

        self.visual_accesses = []
        self.current_step = 0

    def create_widgets(self):
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Label(top_frame, text="Test Type:").grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        self.test_type = tk.StringVar(value="spatial")
        test_types = ["spatial", "temporal", "random", "visual"]
        self.test_menu = ttk.Combobox(top_frame, textvariable=self.test_type, values=test_types, state="readonly", width=12) # Removed command causing error
        self.test_menu.bind("<<ComboboxSelected>>", self.test_type_changed) # Correct event binding
        self.test_menu.grid(column=1, row=0, padx=5, pady=5)

        ttk.Label(top_frame, text="Replacement Policy:").grid(column=2, row=0, padx=5, pady=5, sticky=tk.W)
        self.policy = tk.StringVar(value="LRU")
        policies = ["LRU", "FIFO", "Random"]
        self.policy_menu = ttk.Combobox(top_frame, textvariable=self.policy, values=policies, state="readonly", width=12)
        self.policy_menu.grid(column=3, row=0, padx=5, pady=5)

        ttk.Label(top_frame, text="Access Count:").grid(column=4, row=0, padx=5, pady=5, sticky=tk.W)
        self.access_count = tk.IntVar(value=1000)
        self.access_entry = ttk.Entry(top_frame, textvariable=self.access_count, width=10, state=tk.NORMAL)
        self.access_entry.grid(column=5, row=0, padx=5, pady=5)

        ttk.Label(top_frame, text="Processor Request (Block Number):").grid(column=6, row=0, padx=5, pady=5, sticky=tk.W)
        self.processor_request = tk.StringVar()
        self.request_entry = ttk.Entry(top_frame, textvariable=self.processor_request, width=10)
        self.request_entry.grid(column=7, row=0, padx=5, pady=5)

        self.run_test_button = ttk.Button(top_frame, text="Run Test", command=self.run_test)
        self.run_test_button.grid(column=8, row=0, padx=5, pady=5)

        self.processor_button = ttk.Button(top_frame, text="Processor Request", command=self.processor_request_step)
        self.processor_button.grid(column=9, row=0, padx=5, pady=5)

        self.run_visual_button = ttk.Button(top_frame, text="Run Visual Simulation", command=self.run_visual_simulation)
        self.run_visual_button.grid(column=10, row=0, padx=5, pady=5)

        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill=tk.X, padx=10, pady=5)

        self.output_area = scrolledtext.ScrolledText(self, width=130, height=10)
        self.output_area.pack(side=tk.TOP, padx=10, pady=5)

        sim_frame = ttk.Frame(self)
        sim_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        left_frame = ttk.Frame(sim_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.processor_label = ttk.Label(left_frame, text="Processor", font=("Arial", 14, "bold"))
        self.processor_label.pack(pady=5)

        self.mm_canvas = tk.Canvas(left_frame, width=300, height=300, bg="white", highlightthickness=2, highlightbackground="red")
        self.mm_canvas.pack(pady=10)
        ttk.Label(left_frame, text="Main Memory (Sample View)").pack()

        self.mm_cell_width = 60
        self.mm_cell_height = 60
        self.mm_cell_rects = {}
        self.create_mm_grid()

        right_frame = ttk.Frame(sim_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.cache_canvas = tk.Canvas(right_frame, width=500, height=300, bg="white")
        self.cache_canvas.pack(pady=10)
        ttk.Label(right_frame, text="Cache Memory").pack()

        self.cache_cell_width = 500 / 16
        self.cache_cell_height = 300 / 8
        self.cache_cols = 16
        self.cache_rows = 8
        self.cache_cell_rects = {}
        self.create_cache_grid()

        self.current_access_label = ttk.Label(self, text="Current Memory Access: N/A", font=("Arial", 12))
        self.current_access_label.pack(pady=5)

    def test_type_changed(self, event=None):
        test_type = self.test_menu.get()
        if test_type in ["temporal", "random"]:
            self.access_entry.config(state=tk.NORMAL)
        else:
            self.access_entry.config(state=tk.DISABLED)

    def create_mm_grid(self):
        self.mm_canvas.delete("all")
        self.mm_cell_rects = {}
        for r in range(MM_ROWS):
            for c in range(MM_COLS):
                x1 = c * self.mm_cell_width + 10
                y1 = r * self.mm_cell_height + 10
                x2 = x1 + self.mm_cell_width
                y2 = y1 + self.mm_cell_height
                idx = r * MM_COLS + c
                rect = self.mm_canvas.create_rectangle(x1, y1, x2, y2, fill="lightblue", outline="black")
                self.mm_canvas.create_text(x1 + self.mm_cell_width/2, y1 + self.mm_cell_height/2, text=str(idx), font=("Arial", 10), tags=(f"mm_text{idx}",))
                self.mm_cell_rects[idx] = rect

    def create_cache_grid(self):
        self.cache_canvas.delete("all")
        self.cache_cell_rects = {}
        for r in range(self.cache_rows):
            for c in range(self.cache_cols):
                x1 = c * self.cache_cell_width
                y1 = r * self.cache_cell_height + 10
                x2 = x1 + self.cache_cell_width
                y2 = y1 + self.cache_cell_height
                idx = r * self.cache_cols + c
                rect = self.cache_canvas.create_rectangle(x1, y1, x2, y2, fill="lightgray", outline="black")
                self.cache_canvas.create_text(x1 + self.cache_cell_width/2, y1 + self.cache_cell_height/2, text="", font=("Arial", 8), tags=(f"cache_text{idx}",), width=self.cache_cell_width - 5)
                self.cache_cell_rects[idx] = rect

    def update_cache_grid(self, highlight_idx=None):
        for idx in range(CAPACITY):
            self.cache_canvas.itemconfigure(f"cache_text{idx}", text="")
            self.cache_canvas.itemconfig(self.cache_cell_rects[idx], fill="lightgray")

        for idx, cache_line in enumerate(self.cache.cache):
            if cache_line.valid:
                self.cache_canvas.itemconfigure(f"cache_text{idx}", text=str(cache_line))
                if highlight_idx is not None and idx == highlight_idx:
                     self.cache_canvas.itemconfig(self.cache_cell_rects[idx], fill="yellow")

    def highlight_mm_block(self, block_number):
        cell_idx = block_number % MM_SAMPLE_BLOCKS
        for idx in range(MM_SAMPLE_BLOCKS):
            self.mm_canvas.itemconfig(self.mm_cell_rects[idx], fill="lightblue")
        self.mm_canvas.itemconfig(self.mm_cell_rects[cell_idx], fill="red")

    def run_test(self):
        test = self.test_type.get()
        policy = self.policy.get()
        count = self.access_count.get()
        self.cache.reset_metrics()
        self.cache.replacement_policy = policy
        self.output_area.delete("1.0", tk.END)
        self.output_area.insert(tk.END, f"Running {test} test with {policy} replacement policy...\n")
        self.output_area.insert(tk.END, "-" * 60 + "\n")

        access_sequence = []
        if test == "spatial":
            total_blocks = MEMORY_SIZE // BLOCK_SIZE
            access_sequence = generate_spatial_accesses(total_blocks)
            self.output_area.insert(tk.END, f"Spatial Test - Accessing blocks sequentially.\n")
        elif test == "temporal":
            access_sequence = generate_temporal_accesses(count)
            self.output_area.insert(tk.END, f"Temporal Test - Repeatedly accessing base blocks for {count} times.\n")
        elif test == "random":
            total_blocks = MEMORY_SIZE // BLOCK_SIZE
            access_sequence = generate_random_accesses(count, total_blocks)
            self.output_area.insert(tk.END, f"Random Test - Performing {count} random accesses.\n")

        results = self.cache.simulate_accesses(access_sequence)
        self.output_area.insert(tk.END, "-" * 60 + "\n")
        self.output_area.insert(tk.END, str(self.cache) + "\n")
        self.output_area.insert(tk.END, "-" * 60 + "\n")
        self.update_cache_grid()

    def processor_request_step(self):
        policy = self.policy.get()
        self.cache.replacement_policy = policy
        req_str = self.processor_request.get().strip()
        total_blocks = MEMORY_SIZE // BLOCK_SIZE
        if req_str:
            try:
                block_number = int(req_str)
            except ValueError:
                self.output_area.insert(tk.END, "Invalid block number entered. Using random request.\n")
                block_number = random.randint(0, total_blocks - 1)
        else:
            block_number = random.randint(0, total_blocks - 1)

        self.current_block_request = block_number
        self.current_access_label.config(text=f"Current Memory Access: Block {block_number}")
        self.output_area.insert(tk.END, f"Processor Request: Block {block_number}\n")

        access_result = self.cache.access_memory(block_number, 0)
        if access_result == "Miss":
            self.output_area.insert(tk.END, "Cache miss! Accessing Main Memory...\n")
            self.highlight_mm_block(block_number)
        else:
            self.output_area.insert(tk.END, "Cache hit!\n")

        self.output_area.insert(tk.END, str(self.cache) + "\n")
        self.output_area.insert(tk.END, "-" * 60 + "\n")
        self.update_cache_grid(highlight_idx=0)

    def run_visual_simulation(self):
        policy = self.policy.get()
        self.cache.reset_metrics()
        self.cache.replacement_policy = policy
        total_blocks = MEMORY_SIZE // BLOCK_SIZE
        self.visual_accesses = [random.randint(0, total_blocks - 1) for _ in range(VISUAL_SIM_STEPS)]
        self.current_step = 0
        self.output_area.delete("1.0", tk.END)
        self.output_area.insert(tk.END, f"Starting visual simulation with {VISUAL_SIM_STEPS} processor requests...\n")
        self.after(ACCESS_DELAY, self.visual_step)

    def visual_step(self):
        if self.current_step >= len(self.visual_accesses):
            self.output_area.insert(tk.END, "Visual simulation completed.\n")
            self.current_access_label.config(text="Visual Simulation Completed")
            return

        block_number = self.visual_accesses[self.current_step]
        self.current_access_label.config(text=f"Current Memory Access: Block {block_number}")
        self.output_area.insert(tk.END, f"Request {self.current_step+1}/{VISUAL_SIM_STEPS}: Block {block_number}\n")

        access_result = self.cache.access_memory(block_number, self.current_step)

        if access_result == "Miss":
            self.output_area.insert(tk.END, "Cache miss! Loading from Main Memory...\n")
            self.highlight_mm_block(block_number)
        else:
            self.output_area.insert(tk.END, "Cache hit!\n")

        self.update_cache_grid(highlight_idx=0)
        self.current_step += 1
        self.after(ACCESS_DELAY, self.visual_step)


def generate_spatial_accesses(num_accesses, start_address=0, step=1):
    total_blocks = MEMORY_SIZE // BLOCK_SIZE
    return list(range(0, total_blocks))

def generate_temporal_accesses(num_accesses, base_addresses_blocks=[0, 1, 2], repeat_pattern=[1, 1, 1, 2, 2, 3]):
    access_sequence = []
    pattern_len = len(repeat_pattern)
    base_len = len(base_addresses_blocks)
    for i in range(num_accesses):
        base_index = repeat_pattern[i % pattern_len] - 1
        access_sequence.append(base_addresses_blocks[base_index % base_len])
    return access_sequence

def generate_random_accesses(num_accesses, total_blocks):
    return [random.randint(0, total_blocks - 1) for _ in range(num_accesses)]


MEMORY_SIZE = 64 * 1024
BLOCK_SIZE = 16
CACHE_SIZE_WORDS = 2 * 1024
CAPACITY = CACHE_SIZE_WORDS // BLOCK_SIZE

VISUAL_SIM_STEPS = 100
ACCESS_DELAY = 500
MM_SAMPLE_BLOCKS = 16
MM_COLS = 4
MM_ROWS = 4


if __name__ == "__main__":
    app = CacheSimulatorGUI()
    app.mainloop()