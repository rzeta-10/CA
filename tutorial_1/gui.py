# gui.py
import tkinter as tk
from tkinter import ttk, scrolledtext
import random
from cache_simulator import FullyAssociativeCache

# Constants for simulation
MEMORY_SIZE = 64 * 1024      # 64K words (real memory)
BLOCK_SIZE = 16              # 16 words per block
CAPACITY = 128               # Cache capacity (128 blocks)

# For visual simulation of processor requests:
VISUAL_SIM_STEPS = 100       # Number of accesses to animate (for auto-simulation)
ACCESS_DELAY = 500           # Delay in milliseconds between simulation steps

# For main memory visual simulation (sample view)
MM_SAMPLE_BLOCKS = 16        # We'll show 16 blocks (a 4x4 grid)
MM_COLS = 4
MM_ROWS = 4

class CacheSimulatorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cache & Main Memory Simulation")
        self.geometry("1100x750")
        self.create_widgets()
        self.cache = FullyAssociativeCache(CAPACITY, replacement_policy="LRU")
        self.current_block_request = None  # The block number requested by the processor

        # For visual simulation steps:
        self.visual_accesses = [] 
        self.current_step = 0

    def create_widgets(self):
        # Top control frame: processor & test options.
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # Test Type Dropdown (for non-visual tests)
        ttk.Label(top_frame, text="Test Type:").grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        self.test_type = tk.StringVar(value="spatial")
        test_types = ["spatial", "temporal", "random", "visual"]
        self.test_menu = ttk.Combobox(top_frame, textvariable=self.test_type, values=test_types, state="readonly", width=12)
        self.test_menu.grid(column=1, row=0, padx=5, pady=5)

        # Replacement Policy Dropdown
        ttk.Label(top_frame, text="Replacement Policy:").grid(column=2, row=0, padx=5, pady=5, sticky=tk.W)
        self.policy = tk.StringVar(value="LRU")
        policies = ["LRU", "FIFO", "Random"]
        self.policy_menu = ttk.Combobox(top_frame, textvariable=self.policy, values=policies, state="readonly", width=12)
        self.policy_menu.grid(column=3, row=0, padx=5, pady=5)

        # Access Count for temporal/random tests
        ttk.Label(top_frame, text="Access Count:").grid(column=4, row=0, padx=5, pady=5, sticky=tk.W)
        self.access_count = tk.IntVar(value=1000)
        self.access_entry = ttk.Entry(top_frame, textvariable=self.access_count, width=10)
        self.access_entry.grid(column=5, row=0, padx=5, pady=5)

        # Processor Request Field (optional: you can type a block number)
        ttk.Label(top_frame, text="Processor Request (Block Number):").grid(column=6, row=0, padx=5, pady=5, sticky=tk.W)
        self.processor_request = tk.StringVar()
        self.request_entry = ttk.Entry(top_frame, textvariable=self.processor_request, width=10)
        self.request_entry.grid(column=7, row=0, padx=5, pady=5)

        # Run Buttons:
        self.run_test_button = ttk.Button(top_frame, text="Run Test", command=self.run_test)
        self.run_test_button.grid(column=8, row=0, padx=5, pady=5)

        self.processor_button = ttk.Button(top_frame, text="Processor Request", command=self.processor_request_step)
        self.processor_button.grid(column=9, row=0, padx=5, pady=5)

        self.run_visual_button = ttk.Button(top_frame, text="Run Visual Simulation", command=self.run_visual_simulation)
        self.run_visual_button.grid(column=10, row=0, padx=5, pady=5)

        # Separator
        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(fill=tk.X, padx=10, pady=5)

        # Output text area for logs
        self.output_area = scrolledtext.ScrolledText(self, width=130, height=10)
        self.output_area.pack(side=tk.TOP, padx=10, pady=5)

        # Main simulation area: split into two frames (Main Memory and Cache)
        sim_frame = ttk.Frame(self)
        sim_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left frame: Processor and Main Memory
        left_frame = ttk.Frame(sim_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Processor label (above main memory)
        self.processor_label = ttk.Label(left_frame, text="Processor", font=("Arial", 14, "bold"))
        self.processor_label.pack(pady=5)

        # Main Memory Canvas (sample view) with a red border
        self.mm_canvas = tk.Canvas(left_frame, width=300, height=300, bg="white", highlightthickness=2, highlightbackground="red")
        self.mm_canvas.pack(pady=10)
        ttk.Label(left_frame, text="Main Memory (Sample View)").pack()

        # Setup main memory grid (4x4 grid representing MM_SAMPLE_BLOCKS blocks)
        self.mm_cell_width = 60
        self.mm_cell_height = 60
        self.mm_cell_rects = {}  # key: cell index, value: rectangle id
        self.create_mm_grid()

        # Right frame: Cache Visualization
        right_frame = ttk.Frame(sim_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.cache_canvas = tk.Canvas(right_frame, width=500, height=300, bg="white")
        self.cache_canvas.pack(pady=10)
        ttk.Label(right_frame, text="Cache Memory").pack()

        # Setup cache grid (16 columns x 8 rows for 128 blocks)
        self.cache_cell_width = 30
        self.cache_cell_height = 30
        self.cache_cols = 16
        self.cache_rows = 8
        self.cache_cell_rects = {}  # key: cell index, value: rectangle id
        self.create_cache_grid()

        # Label to display current main memory access (block number)
        self.current_access_label = ttk.Label(self, text="Current Memory Access: N/A", font=("Arial", 12))
        self.current_access_label.pack(pady=5)

    def create_mm_grid(self):
        """
        Create a grid for main memory simulation (sample view).
        """
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
        """
        Create the grid for cache memory simulation.
        """
        self.cache_canvas.delete("all")
        self.cache_cell_rects = {}
        for r in range(self.cache_rows):
            for c in range(self.cache_cols):
                x1 = c * self.cache_cell_width + 10
                y1 = r * self.cache_cell_height + 10
                x2 = x1 + self.cache_cell_width
                y2 = y1 + self.cache_cell_height
                idx = r * self.cache_cols + c
                rect = self.cache_canvas.create_rectangle(x1, y1, x2, y2, fill="lightgray", outline="black")
                self.cache_canvas.create_text(x1 + self.cache_cell_width/2, y1 + self.cache_cell_height/2, text="", font=("Arial", 8), tags=(f"cache_text{idx}",))
                self.cache_cell_rects[idx] = rect

    def update_cache_grid(self, highlight_idx=None):
        """
        Update the cache grid to reflect current cache contents.
        The cache simulator holds its blocks in a list (cache.cache), with index 0 as MRU.
        If highlight_idx is given, color that cell (the most recently accessed).
        """
        # Clear texts in all cells.
        for idx in range(CAPACITY):
            self.cache_canvas.itemconfigure(f"cache_text{idx}", text="")

        # Update cells with current cache contents.
        for idx, block in enumerate(self.cache.cache):
            self.cache_canvas.itemconfigure(f"cache_text{idx}", text=str(block))
            # Reset cell color.
            self.cache_canvas.itemconfig(self.cache_cell_rects[idx], fill="lightgray")

        # Highlight the most recent access if provided.
        if highlight_idx is not None and highlight_idx < CAPACITY:
            self.cache_canvas.itemconfig(self.cache_cell_rects[highlight_idx], fill="yellow")

    def highlight_mm_block(self, block_number):
        """
        In the main memory sample view, highlight the cell corresponding to the block.
        Since the main memory view is a sample of MM_SAMPLE_BLOCKS blocks, we map the
        block number (mod MM_SAMPLE_BLOCKS) to a cell.
        """
        cell_idx = block_number % MM_SAMPLE_BLOCKS
        # Reset all main memory cells
        for idx in range(MM_SAMPLE_BLOCKS):
            self.mm_canvas.itemconfig(self.mm_cell_rects[idx], fill="lightblue")
        # Highlight the chosen cell in red.
        self.mm_canvas.itemconfig(self.mm_cell_rects[cell_idx], fill="red")

    def run_test(self):
        """
        Run a non-visual test based on the chosen type (spatial, temporal, random).
        This outputs log text in the output_area.
        """
        test = self.test_type.get()
        policy = self.policy.get()
        count = self.access_count.get()
        self.cache = FullyAssociativeCache(CAPACITY, policy)
        self.output_area.delete("1.0", tk.END)
        self.output_area.insert(tk.END, f"Running {test} test with {policy} replacement policy...\n")
        self.output_area.insert(tk.END, "-" * 60 + "\n")
        
        if test == "spatial":
            accessed_blocks = []
            total_blocks = MEMORY_SIZE // BLOCK_SIZE
            for block_number in range(total_blocks):
                if block_number < 10:
                    accessed_blocks.append(block_number)
                self.cache.access(block_number)
            self.output_area.insert(tk.END, f"Spatial Test - Sample first 10 blocks: {accessed_blocks}\n")
        elif test == "temporal":
            self.output_area.insert(tk.END, f"Temporal Test - Repeatedly accessing block 0 for {count} times.\n")
            for _ in range(count):
                self.cache.access(0)
        elif test == "random":
            self.output_area.insert(tk.END, f"Random Test - Performing {count} random accesses.\n")
            sample_accesses = []
            total_blocks = MEMORY_SIZE // BLOCK_SIZE
            for i in range(count):
                block_number = random.randint(0, total_blocks - 1)
                if i < 10:
                    sample_accesses.append(block_number)
                self.cache.access(block_number)
            self.output_area.insert(tk.END, f"Random Test - Sample first 10 random accesses: {sample_accesses}\n")
        else:
            self.output_area.insert(tk.END, "For visual simulation, please use the 'Run Visual Simulation' button.\n")
            return

        self.output_area.insert(tk.END, "-" * 60 + "\n")
        self.output_area.insert(tk.END, str(self.cache) + "\n")
        self.output_area.insert(tk.END, "-" * 60 + "\n")
        self.update_cache_grid()

    def processor_request_step(self):
        """
        Simulate a processor request. The user can either enter a block number
        in the text entry field or leave it blank (in which case a random block is chosen).
        Then, the simulation checks the cache:
          - If the block is in the cache, it is a hit.
          - If not, it highlights the corresponding main memory cell and then
            loads the block into the cache.
        """
        policy = self.policy.get()
        self.cache = FullyAssociativeCache(CAPACITY, policy)
        # Decide on a block number to request.
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

        # Check the cache.
        comparisons = self.cache.access(block_number)
        # If the block was not already in cache, simulate a main memory access.
        if self.cache.cache[0] != block_number or self.cache.miss_count > 0:
            self.output_area.insert(tk.END, "Cache miss! Accessing Main Memory...\n")
            self.highlight_mm_block(block_number)
        else:
            self.output_area.insert(tk.END, "Cache hit!\n")
        self.output_area.insert(tk.END, f"Comparisons made: {comparisons}\n")
        self.output_area.insert(tk.END, str(self.cache) + "\n")
        self.output_area.insert(tk.END, "-" * 60 + "\n")
        self.update_cache_grid(highlight_idx=0)

    def run_visual_simulation(self):
        """
        Run an automated visual simulation.
        For demonstration, we simulate a series of processor requests.
        """
        policy = self.policy.get()
        self.cache = FullyAssociativeCache(CAPACITY, policy)
        total_blocks = MEMORY_SIZE // BLOCK_SIZE
        # For demonstration, generate VISUAL_SIM_STEPS random block requests.
        self.visual_accesses = [random.randint(0, total_blocks - 1) for _ in range(VISUAL_SIM_STEPS)]
        self.current_step = 0
        self.output_area.delete("1.0", tk.END)
        self.output_area.insert(tk.END, f"Starting visual simulation with {VISUAL_SIM_STEPS} processor requests...\n")
        self.after(ACCESS_DELAY, self.visual_step)

    def visual_step(self):
        """
        Process one step of the visual simulation.
        """
        if self.current_step >= len(self.visual_accesses):
            self.output_area.insert(tk.END, "Visual simulation completed.\n")
            return

        block_number = self.visual_accesses[self.current_step]
        self.current_access_label.config(text=f"Current Memory Access: Block {block_number}")
        self.output_area.insert(tk.END, f"Request {self.current_step+1}: Block {block_number}\n")

        # Check if the block is in cache.
        was_hit = block_number in self.cache.cache

        # For a miss, highlight the main memory sample view.
        if not was_hit:
            self.output_area.insert(tk.END, "Cache miss! Loading from Main Memory...\n")
            self.highlight_mm_block(block_number)
        else:
            self.output_area.insert(tk.END, "Cache hit!\n")

        # Access the block (this will update the cache).
        self.cache.access(block_number)
        self.update_cache_grid(highlight_idx=0)

        self.current_step += 1
        self.after(ACCESS_DELAY, self.visual_step)

if __name__ == "__main__":
    app = CacheSimulatorGUI()
    app.mainloop()
