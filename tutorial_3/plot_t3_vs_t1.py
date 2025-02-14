import matplotlib.pyplot as plt
import numpy as np

# Given data for Exp01 (Fully Associative Cache) and Multi-Level Cache (Enhanced Implementation)
num_accesses_list = [100, 500, 1000, 2000, 5000, 10000, 50000, 100000]

# Exp01 Results (Fully Associative Cache)
exp01_hit_ratios = [50, 55, 60, 65, 70, 75, 80, 85]
exp01_miss_ratios = [50, 45, 40, 35, 30, 25, 20, 15]

# Enhanced Multi-Level Cache Results (Direct Mapped + 4-Way Set Associative + Write Buffer + Victim Cache + Prefetch)
multi_level_hit_ratios = [60, 68, 74, 79, 83, 86, 89, 92]
multi_level_miss_ratios = [40, 32, 26, 21, 17, 14, 11, 8]

# Plot Hit Ratio Comparison
plt.figure(figsize=(8, 6))
plt.plot(num_accesses_list, exp01_hit_ratios, marker='o', linestyle='-', label='Exp01 (Single Level Cache)')
plt.plot(num_accesses_list, multi_level_hit_ratios, marker='s', linestyle='--', label='Multi-Level Cache')
plt.xscale('log')
plt.title('Comparison of Hit Ratios')
plt.xlabel('Number of Accesses (log scale)')
plt.ylabel('Hit Ratio (%)')
plt.grid(True, which="both", ls="--")
plt.legend()
plt.tight_layout()
plt.savefig('comparison_hit_ratio.png')
plt.show()

# Plot Miss Ratio Comparison
plt.figure(figsize=(8, 6))
plt.plot(num_accesses_list, exp01_miss_ratios, marker='o', linestyle='-', label='Exp01 (Single Level Cache)')
plt.plot(num_accesses_list, multi_level_miss_ratios, marker='s', linestyle='--', label='Multi-Level Cache')
plt.xscale('log')
plt.title('Comparison of Miss Ratios')
plt.xlabel('Number of Accesses (log scale)')
plt.ylabel('Miss Ratio (%)')
plt.grid(True, which="both", ls="--")
plt.legend()
plt.tight_layout()
plt.savefig('comparison_miss_ratio.png')
plt.show()
