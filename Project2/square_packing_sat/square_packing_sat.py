from pysat.solvers import Glucose42
from pysat.formula import CNF, IDPool
from itertools import combinations

def build_cnf(n, W, H):
    # A square has variables x,y fot the bottom left corner,
    # each with domain 0..N-s_i where s_i is the size of the square
    # Square i has size s_i = i, for i = 1..N

    # The domain implies that x_i + s_i <= W and y_i + s_i <= H, so we can encode the domain as:
    # x_i <= W - s_i and y_i <= H - s_i

    # Each square doesn't overlap with any other square, so one must hold between
    # x_i + s_i <= x_j or x_j + s_j <= x_i or y_i + s_i <= y_j or y_j + s_j <= y_i

    #For symmetry breaking, the largest square is placed in the bottom left corner, so x_N = 0 and y_N = 0
    
    sizes = list(range(1, n+1))
    
    vpool = IDPool()
    cnf = CNF()

    def ox(i,v): return vpool.id(f"ox_{i}_{v}") #ordering variable for x_i <= v
    def oy(i,v): return vpool.id(f"oy_{i}_{v}") #ordering variable for y_i <= v
    def dv(i,j,d): return vpool.id(f"dv_{i}_{j}_{d}") #indicator direction variable for the disjunction of non-overlapping conditions between square i and j, d is up down left right

    #upper bounds for x_i and y_i
    def max_x(i): return W - sizes[i]
    def max_y(i): return H - sizes[i]

    #consistency chain for ordering variables:
    for i in range(n):
        cnf.append([ox(i,max_x(i))]) #x_i <= max_x(i)
        cnf.append([oy(i,max_y(i))]) #y_i <= max_y(i)
        for v in range(1, max_x(i)+1):
            cnf.append([-ox(i,v-1), ox(i,v)]) # x_i <= v-1 implies x_i <= v
        for v in range(1, max_y(i)+1):
            cnf.append([-oy(i,v-1), oy(i,v)]) # y_i <= v-1 implies y_i <= v

    #non-overlapping conditions:
    for i,j in combinations(range(n), 2):
        s_i, s_j = sizes[i], sizes[j]

        #left, right, bottom, top indicator variables
        l,r,b,t = dv(i,j,'l'), dv(i,j,'r'), dv(i,j,'b'), dv(i,j,'t')
        cnf.append([l,r,b,t]) #at least one of the non-overlapping conditions must hold

        #l -> x_i +s_i <= x_j  <->  l -> x_i <= x_j - s_i
        for v in range(W-s_j +1): #we only need to consider v up to W-s_j because x_j cannot be greater than W-s_j
            clause = [-l, -ox(j,v)]
            if v-s_i < 0: cnf.append(clause) #if v-s_i < 0 then x_i <= v is always true
            elif v-s_i < max_x(i): cnf.append(clause + [ox(i,v-s_i)]) #if v-s_i >= 0 then x_i <= v-s_i must hold for l to hold

        #r -> x_j +s_j <= x_i  <->  r -> x_j <= x_i - s_j
        for v in range(W-s_i +1): #we only need to consider v up to W-s_i because x_i cannot be greater than W-s_i
            clause = [-r, -ox(i,v)]
            if v-s_j < 0: cnf.append(clause) #if v-s_j < 0 then x_j <= v is always true
            elif v-s_j < max_x(j): cnf.append(clause + [ox(j,v-s_j)]) #if v-s_j >= 0 then x_j <= v-s_j must hold for r to hold

        #b -> y_i +s_i <= y_j  <->  b -> y_i <= y_j - s_i
        for v in range(H-s_j +1):
            clause = [-b, -oy(j,v)]
            if v-s_i < 0: cnf.append(clause) #if v-s_i < 0 then y_i <= v is always true
            elif v-s_i < max_y(i): cnf.append(clause + [oy(i,v-s_i)]) #if v-s_i >= 0 then y_i <= v-s_i must hold for b to hold

        #t -> y_j +s_j <= y_i  <->  t -> y_j <= y_i - s_j
        for v in range(H-s_i +1):
            clause = [-t, -oy(i,v)]
            if v-s_j < 0: cnf.append(clause) #if v-s_j < 0 then y_j <= v is always true
            elif v-s_j < max_y(j): cnf.append(clause + [oy(j,v-s_j)]) #if v-s_j >= 0 then y_j <= v-s_j must hold for t to hold

    #symmetry breaking for the largest square:
    cnf.append([ox(n-1,0)]) #x_N <= 0
    cnf.append([oy(n-1,0)]) #y_N <= 0

    return cnf, vpool, sizes

def solve(n,W,H):
    cnf, vpool, sizes = build_cnf(n,W,H)

    with Glucose42(bootstrap_with=cnf) as solver:
        sat = solver.solve()
        accum = solver.accum_stats()

        if not sat:
            return None, accum
        model = set(solver.get_model())

    def decode_x(i):
        for v in range(W - sizes[i]):
            if vpool.id(f"ox_{i}_{v}") in model:
                return v #if x_i <= v and x_i > v-1 then x_i = v, so we return the smallest v for which ox(i,v) is true
        return W - sizes[i] #if no ordering variable is true, then x_i is at its maximum value
    
    def decode_y(i):
        for v in range(H - sizes[i]):
            if vpool.id(f"oy_{i}_{v}") in model:
                return v #if y_i <= v and y_i > v-1 then y_i = v, so we return the smallest v for which oy(i,v) is true
        return H - sizes[i] #if no ordering variable is true, then y_i is at its maximum value
    
    return{i+1: (decode_x(i), decode_y(i)) for i in range(n)}, accum #return a dictionary mapping each square to its coordinates of the bottom left corner

def visualize(n, W, H, solution, file_handle):
    # Create empty grid
    grid = [['.' for _ in range(W)] for _ in range(H)]

    # Place each square on the grid
    for square, (x, y) in solution.items():
        s = square  # size of square equals its number
        for row in range(y, y + s):
            for col in range(x, x + s):
                grid[row][col] = str(square)

    # Print top to bottom (row H-1 is the top)
    print(f"\n{W}x{H} rectangle:\n", file=file_handle)
    for row in reversed(grid):
        print(' '.join(row), file=file_handle)
    print("\n", file=file_handle)

def find_min_rectangle(n, file_handle=None):
    import math
    import time

    sizes = list(range(1, n+1))
    total_area = sum(s**2 for s in sizes)

    W_lb = n #lower bound on width is the size of the largest square
    W_ub = sum(sizes) #upper bound on width is the sum of all square sizes (if we place them all in a row)

    best_area, best = math.inf, None

    stats = {
        "rectangles_tried":0,
        "sat_calls":0,
        "unsat_calls":0,
        "total_conflicts":0,
        "total_decisions":0,
        "total_propagations":0,
        "total_restarts":0,
        "candidates": []
    }
    total_start = time.time()
    for W in range(W_lb, W_ub + 1):
        if W * n >= best_area: break #H always has to be at least n, so if W*n is already greater than the best area found, we can stop

        H_lb = max(n, math.ceil(total_area / W)) #lower bound on height is the size of the largest square and also total_area / W
        H_ub = min(W, (best_area-1)//W)# require a strict improvement
        
        if H_lb > H_ub: continue #if the lower bound on height is greater than the upper bound, there is no point in trying this width
        lo, hi = H_lb, H_ub
        found_H,best_sol = None, None
        while lo <= hi:
            mid = (lo + hi) // 2
            stats["rectangles_tried"] += 1

            t0 = time.time()
            solution, accum = solve(n, W, mid)
            elapsed = time.time() - t0

            stats['total_conflicts'] += accum.get('conflicts', 0)
            stats['total_decisions'] += accum.get('decisions', 0)
            stats['total_propagations'] += accum.get('propagations', 0)
            stats['total_restarts'] += accum.get('restarts', 0)

            sat = solution is not None
            stats["sat_calls" if sat else "unsat_calls"] += 1
            stats["candidates"].append((W, mid, sat, elapsed))

            if sat:
                found_H = mid
                best_sol = solution
                hi = mid - 1
            else:
                lo = mid + 1
        if found_H is not None and W * found_H < best_area:
            best_area = W * found_H
            best = (W, found_H, best_sol)
            print(f"Found better solution with area {best_area} for W={W} and H={found_H}", file=file_handle)
    stats['total_time'] = time.time() - total_start
    return best, stats

def print_stats(stats, file_handle=None):
    print("=" * 50, file=file_handle)
    print("SEARCH STATISTICS", file=file_handle)
    print("=" * 50, file=file_handle)
    print(f"  Rectangles tried : {stats['rectangles_tried']}", file=file_handle)
    print(f"  SAT calls        : {stats['sat_calls']}", file=file_handle)
    print(f"  UNSAT calls      : {stats['unsat_calls']}", file=file_handle)
    print(f"  Total conflicts  : {stats['total_conflicts']}", file=file_handle)
    print(f"  Total decisions  : {stats['total_decisions']}", file=file_handle)
    print(f"  Total propagations: {stats['total_propagations']}", file=file_handle)
    print(f"  Total restarts   : {stats['total_restarts']}", file=file_handle)
    print(f"  Total time       : {stats['total_time']:.3f}s", file=file_handle)
    print("\n", file=file_handle)
    print(f"  {'W':>4} {'H':>4} {'Result':>6} {'Time':>8}  Conflicts / Decisions", file=file_handle)
    print(f"  {'-'*4} {'-'*4} {'-'*6} {'-'*8}  {'---'}", file=file_handle)
    for W, H, sat, t in stats['candidates']:
        print(f"  {W:4d} {H:4d} {'SAT' if sat else 'UNSAT':>6} {t:7.3f}s", file=file_handle)
    print("=" * 50, file=file_handle)


if __name__ == "__main__":
    for n in range(5, 21):
        with open("sat_results.txt", "a") as f:
            print(f"\n\nSolving for n={n} squares", file=f)
            result, stats = find_min_rectangle(n, file_handle=f)
            print_stats(stats, file_handle=f)
            if result:
                W, H, solution = result
                print(f"Best solution found: {W}x{H} rectangle with area {W*H}", file=f)
                visualize(n, W, H, solution, file_handle=f)
                for square, (x,y) in solution.items():
                    print(f"Square {square} (size {square}) is at ({x}, {y})", file=f)