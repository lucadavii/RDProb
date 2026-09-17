from pychoco.model import Model
import math

def pack(n, maxW, maxH):
    model = Model("Packing")

    x = [model.intvar(0, maxW-(i)) if i < n else model.intvar(0, math.floor((maxW-n)/2)) for i in range(1, n+1)]
    y = [model.intvar(0, maxH-(i)) if i < n else model.intvar(0, math.floor((maxH-n)/2)) for i in range(1, n+1)]
    w = [model.intvar(i,i) for i in range(1,n+1)]
    h = [model.intvar(i,i) for i in range(1,n+1)]

    model.diff_n(x, y, w, h).post()


    #symmetry breaking: place the biggest square in the bottom-left corner
    model.arithm(x[n-1], "=", 0).post()
    model.arithm(y[n-1], "=", 0).post()

    solver = model.get_solver()
    vars = [var for i in range(n-1, -1, -1) for var in (x[i], y[i])]
    #solver.set_input_order_lb_search(vars)
    solver.set_dom_over_w_deg_search(vars)
    #solver.set_activity_based_search(vars)

    if solver.solve():
        print("Search statistics: " \
        "{} restarts, {} failures, {} backtracks, time = {:.4f}s".format(
            solver.get_restart_count(),
            solver.get_fail_count(),
            solver.get_backtrack_count(),
            solver.get_time_count()        )) 
        return [[x[i].get_value() for i in range(n)], [y[i].get_value() for i in range(n)]]
    else:
        return [[0 for _ in range(n)], [0 for _ in range(n)]]


def show_results(n, maxW, maxH, origins):
    xs = origins[0]
    ys = origins[1]

    total_square_area = sum((i + 1) ** 2 for i in range(n))
    rect_area = maxW * maxH

    # No-solution check
    if all(xs[i] == 0 and ys[i] == 0 for i in range(n)):
        print("=" * 50)
        print(f"pack({n}, {maxW}, {maxH})  →  NO SOLUTION")
        print("=" * 50)
        return

    # Header

    print("=" * 50)
    print(f"pack({n}, {maxW}, {maxH})  -  Packing result")
    print("=" * 50)
    print(f"  Rectangle : {maxW} x {maxH}  (area = {rect_area})")
    print(f"  Squares   : {total_square_area}  (fill = {100 * total_square_area / rect_area:.1f} %)")
    print()


    # Per-square table
    print(f"  {'Square':>6}  {'Origin (x,y)':>14}  {'Fits?':>6}")
    print("  " + "-" * 32)
    for i in range(n):
        size = i + 1
        x, y = xs[i], ys[i]
        fits = (x >= 0 and y >= 0 and x + size <= maxW and y + size <= maxH)
        print(f"  {size:>3}x{size:<3}  ({x:>4}, {y:>4})        {'OK' if fits else 'ERR':>6}")

    # Overlap check
    print()
    overlaps = []
    for i in range(n):
        for j in range(i + 1, n):
            si, sj = i + 1, j + 1
            xi, yi = xs[i], ys[i]
            xj, yj = xs[j], ys[j]
            if xi < xj + sj and xi + si > xj and yi < yj + sj and yi + si > yj:
                overlaps.append((si, sj))
    if overlaps:
        print(f"  WARNING: {len(overlaps)} overlapping pair(s): {overlaps}")
    else:
        print("  Overlap check : PASSED")

    # ASCII grid  (y=0 at bottom)
    grid = [['.' for _ in range(maxW)] for _ in range(maxH)]
    for i in range(n):
        size = i + 1
        x, y = xs[i], ys[i]
        for dy in range(size):
            for dx in range(size):
                grid[y + dy][x + dx] = str(size) if size < 10 else chr(ord('A') + size - 10)

    print()
    print("  ASCII layout  (number = square size, '.' = empty)")
    print()
    col_header = "      " + " ".join(f"{c}" for c in range(maxW))
    print(col_header)
    print("      " + "--" * maxW)
    for row in range(maxH - 1, -1, -1):
        print(f"  {row:2} | " + " ".join(grid[row]))
    print()
    print("=" * 50)


def best_fitting_rect(n):
    squares_total_area = n*(n+1)*(2*n+1)//6
    candidates = []
    for w in range(n, squares_total_area +1):
        for h in range(max(n,math.ceil(squares_total_area / w)), w+1):
            candidates.append((w, h))
    candidates.sort(key=lambda wh: wh[0]*wh[1])

    print("Number of candidates:", len(candidates))
    for w, h in candidates:
        res = pack(n, w, h)
        if not all(res[0][i] == 0 and res[1][i] == 0 for i in range(n)):
            return (w, h), res
    print("No solution found")
    return None, None    

if __name__ == "__main__":
    import time
    for n in range(5, 18):
        
        print(f"Finding best fitting rectangle for n={n}...")
        start_time = time.time()
        (w,h), res = best_fitting_rect(n)
        end_time = time.time()
        show_results(n, w, h, res)
        print(f"Total time: {end_time - start_time:.4f} seconds")