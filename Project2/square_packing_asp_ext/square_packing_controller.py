import clingo
import math
import time

class Solver:
    def __init__(self,n):
        self.n = n
        self.sizes = list(range(1, n+1))
        self.wmax = sum(self.sizes)
        self.hmax = self.wmax
        self.cur_w = None
        self.cur_h = None

        self.ctl = clingo.Control(["1",
            f"-c n={n}",
            f"-c wmax={self.wmax}",
            f"-c hmax={self.hmax}"
        ])
        self.ctl.load("square_packing_asp.lp")
        self.ctl.ground([("base", [])])
    def solve(self,W,H):

        if self.cur_w is not None:
            self.ctl.assign_external(clingo.Function("ext_w", [clingo.Number(self.cur_w)]), False)
        if self.cur_h is not None:
            self.ctl.assign_external(clingo.Function("ext_h", [clingo.Number(self.cur_h)]), False)
        
        self.ctl.assign_external(clingo.Function("ext_w", [clingo.Number(W)]), True)
        self.ctl.assign_external(clingo.Function("ext_h", [clingo.Number(H)]), True)
        self.cur_w, self.cur_h = W, H

        before = {k: self.ctl.statistics["solving"]["solvers"][k] for k in ["choices", "conflicts", "restarts"]}


        solution = None
        t0 = time.time()

        with self.ctl.solve(yield_ = True) as handle:
            for model in handle:
                solution = {}
                for atom in model.symbols(shown=True):
                    i = atom.arguments[0].number
                    v = atom.arguments[1].number
                    if atom.name == "pos_X":
                        solution.setdefault(i, {})["x"] = v
                    elif atom.name == "pos_Y":
                        solution.setdefault(i, {})["y"] = v
                break
        solve_time = time.time() - t0
        after = {k: self.ctl.statistics["solving"]["solvers"][k] for k in ["choices", "conflicts", "restarts"]}

        stats = {
            "solve_time": solve_time,
            "choices": after["choices"] - before["choices"],
            "conflicts": after["conflicts"] - before["conflicts"],
            "restarts": after["restarts"] - before["restarts"]
        }

        if solution is None:
            return None, stats
        
        return{ i : (d["x"], d["y"]) for i, d in solution.items() }, stats

def find_min_rectangle(n, file_handle=None):
    sizes = list(range(1, n+1))
    total_area = sum(s**2 for s in sizes)

    W_lb = n #lower bound on width is the size of the largest square
    W_ub = sum(sizes) #upper bound on width is the sum of all square sizes (if we place them all in a row)

    best_area, best = math.inf, None
    solver = Solver(n)
    agg = {
        "rectangles_tried":0,
        "sat_calls":0,
        "unsat_calls":0,
        "total_conflicts":0,
        "total_choices":0,
        "total_restarts":0,
        "candidates": []
    }

    total_start = time.time()
    for W in range(W_lb, W_ub + 1):
        if W * n >= best_area: break #H always has to be at least n, so if W*n is already greater than the best area found, we can stop

        H_lb = max(n, math.ceil(total_area / W)) #lower bound on height is the size of the largest square and also total_area / W
        H_ub = min(W, (best_area-1)//W)# require a strict improvement
        
        if H_lb > H_ub:continue #if the lower bound on height is greater than the upper bound, there is no point in trying this width

        lo, hi = H_lb, H_ub
        found_H,best_sol = None, None
        while lo <= hi:
            mid = (lo + hi) // 2
            agg["rectangles_tried"] += 1
            solution, solve_stats = solver.solve(W, mid)
            sat = solution is not None


            agg["total_conflicts"] += solve_stats.get('conflicts', 0)
            agg["total_choices"] += solve_stats.get('choices', 0)
            agg["total_restarts"] += solve_stats.get('restarts', 0)
            agg["sat_calls" if sat else "unsat_calls"] += 1
            agg["candidates"].append((W, mid, sat, solve_stats))

            print(f"Trying {W}x{mid} rectangle: {'SAT' if sat else 'UNSAT'} (conflicts={solve_stats.get('conflicts', 0)}, choices={solve_stats.get('choices', 0)}, time={solve_stats.get('solve_time', 0):.2f}s)", file=file_handle)

            if sat:
                found_H, best_sol = mid, solution
                hi = mid - 1
            else:
                lo = mid + 1
        if found_H is not None and W * found_H < best_area:
            best_area = W * found_H
            best = (W, found_H, best_sol)
            print(f"Found better solution with area {best_area} for W={W} and H={found_H}", file=file_handle)
    agg['total_time'] = time.time() - total_start
    return best, agg

def print_stats(stats, file_handle=None):
    print("\n=== Search Statistics ===", file=file_handle)
    print(f"Total rectangles tried: {stats['rectangles_tried']}", file=file_handle)
    print(f"SAT calls: {stats['sat_calls']}", file=file_handle)
    print(f"UNSAT calls: {stats['unsat_calls']}", file=file_handle)
    print(f"Total conflicts: {stats['total_conflicts']}", file=file_handle)
    print(f"Total choices: {stats['total_choices']}", file=file_handle)
    print(f"Total restarts: {stats['total_restarts']}", file=file_handle)
    print(f"Total time: {stats['total_time']:.2f} seconds", file=file_handle)
    print("\nCandidates tried (W, H, SAT, time):", file=file_handle)
    for W, H, sat, solve_stats in stats['candidates']:
        print(f"  {W}x{H}: {'SAT' if sat else 'UNSAT'} (conflicts={solve_stats.get('conflicts', 0)}, choices={solve_stats.get('choices', 0)}, time={solve_stats.get('solve_time', 0):.2f}s)", file=file_handle)

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
    print('\n', file=file_handle)

if __name__ == "__main__":
    for n in range(5, 12):
        with open("asp_ext_results.txt", "a") as f:
            print(f"Finding minimum rectangle to pack squares of sizes 1 to {n}...", file=f)
            result, stats = find_min_rectangle(n, file_handle=f)
            print_stats(stats, file_handle=f)

            if result:
                W, H, solution = result
                print(f"Best solution found: {W}x{H} rectangle with area {W*H}", file=f)
                visualize(n, W, H, solution, file_handle=f)
                for square, (x,y) in solution.items():
                    print(f"Square {square} (size {square}) is at ({x}, {y})", file=f)