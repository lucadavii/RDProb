import clingo
import math
import time

def solve(n, file_handle=None):
    sizes = list(range(1, n+1))
    w_max = sum(sizes)
    h_max = w_max

    ctl=clingo.Control(["0",
        f"-c n={n}",
        f"-c wmax={w_max}",
        f"-c hmax={h_max}"
    ])
    ctl.load("square_packing_min.lp")

    t0 = time.time()
    ctl.ground([("base", [])])
    ground_time = time.time() - t0

    solution = None
    W_opt, H_opt = None, None
    t1 = time.time()

    with ctl.solve(yield_ = True) as handle:
        for model in handle:
            solution = {}
            W_opt, H_opt = None, None
            for atom in model.symbols(shown=True):
                if atom.name == "width":
                    W_opt = atom.arguments[0].number
                elif atom.name == "height":
                    H_opt = atom.arguments[0].number
                elif atom.name == "pos_X":
                    i = atom.arguments[0].number
                    v = atom.arguments[1].number
                    solution.setdefault(i, {})["x"] = v
                elif atom.name == "pos_Y":
                    i = atom.arguments[0].number
                    v = atom.arguments[1].number
                    solution.setdefault(i, {})["y"] = v
            print(f"Found solution with area {W_opt * H_opt} (W={W_opt}, H={H_opt})", file=file_handle)

    solve_time = time.time() - t1
    s = ctl.statistics["solving"]["solvers"]
    stats = {
        "ground_time": ground_time,
        "solve_time": solve_time,
        "choices": s["choices"],
        "conflicts": s["conflicts"],
        "restarts": s["restarts"]
    }

    if solution is None:
        return None, None, None, stats
    
    return  W_opt, H_opt, { i : (d["x"], d["y"]) for i, d in solution.items() }, stats


def print_stats(stats, file_handle=None):
    print("\n=== Search Statistics ===", file=file_handle)
    print(f"  conflicts={stats['conflicts']:.0f}  choices={stats['choices']:.0f}"
              f"  ground={stats['ground_time']:.3f}s  solve={stats['solve_time']:.3f}s", file=file_handle)

def visualize(n, W, H, solution, file_handle=None):
    grid = [['.' for _ in range(W)] for _ in range(H)]

    for square, (x, y) in solution.items():
        s = square  # square i has size i
        for row in range(y, y + s):
            for col in range(x, x + s):
                grid[row][col] = str(square)

    print(f"\n{W}x{H} rectangle:\n", file=file_handle)
    for row in reversed(grid):
        print(' '.join(row), file=file_handle)
    print("\n", file=file_handle)

if __name__ == "__main__":
    for n in range(5,11):
        with open("asp_min_results.txt", "a") as f:
            print(f"Finding minimum rectangle to pack squares of sizes 1 to {n}...", file=f)
            W,H,solution, stats = solve(n, file_handle=f)
            if solution:
                print(f"Best solution found: {W}x{H} rectangle with area {W*H}", file=f)
                visualize(n, W, H, solution, file_handle=f)
                for square, (x,y) in solution.items():
                    print(f"Square {square} (size {square}) is at ({x}, {y})", file=f)
            else:
                print("No solution found.", file=f)
            print_stats(stats, file_handle=f)

