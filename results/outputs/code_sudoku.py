def solve(board):
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    empties = []

    for r in range(9):
        for c in range(9):
            ch = board[r][c]
            if ch == '.':
                empties.append((r, c))
            else:
                d = ch
                b = (r // 3) * 3 + c // 3
                if d in rows[r] or d in cols[c] or d in boxes[b]:
                    raise ValueError("Invalid board")
                rows[r].add(d)
                cols[c].add(d)
                boxes[b].add(d)

    # candidates for each empty cell
    cand = {}
    for (r, c) in empties:
        b = (r // 3) * 3 + c // 3
        cand[(r, c)] = [d for d in "123456789"
                        if d not in rows[r] and d not in cols[c] and d not in boxes[b]]

    grid = [list(row) for row in board]
    all_units = []
    for i in range(9):
        all_units.append([(i, c) for c in range(9)])
        all_units.append([(r, i) for r in range(9)])
    for br in range(3):
        for bc in range(3):
            all_units.append([(br * 3 + r, bc * 3 + c) for r in range(3) for c in range(3)])

    cell_units = {}
    for r in range(9):
        for c in range(9):
            b = (r // 3) * 3 + c // 3
            cell_units[(r, c)] = [u for u in all_units if (r, c) in u]

    peers = {}
    for r in range(9):
        for c in range(9):
            s = set()
            for u in cell_units[(r, c)]:
                s.update(u)
            s.discard((r, c))
            peers[(r, c)] = s

    def assign(r, c, d):
        b = (r // 3) * 3 + c // 3
        rows[r].add(d)
        cols[c].add(d)
        boxes[b].add(d)
        grid[r][c] = d

    def unassign(r, c, d):
        b = (r // 3) * 3 + c // 3
        rows[r].discard(d)
        cols[c].discard(d)
        boxes[b].discard(d)
        grid[r][c] = '.'

    def propagate(queue):
        while queue:
            cell = queue.pop()
            r, c = cell
            b = (r // 3) * 3 + c // 3
            used = rows[r] | cols[c] | boxes[b]
            if grid[r][c] != '.':
                # fixed cell: remove its digit from peers
                d = grid[r][c]
                for p in peers[cell]:
                    pr, pc = p
                    if grid[pr][pc] == '.':
                        if d in cand.get(p, []):
                            cand[p].remove(d)
                            if not cand[p]:
                                return False
                            if len(cand[p]) == 1:
                                queue.append(p)
            else:
                # recompute candidates
                avail = [d for d in "123456789" if d not in used]
                cand[cell] = avail
                if not avail:
                    return False
                if len(avail) == 1 and cell not in fixed_done:
                    queue.append(cell)
        return True

    # Simpler approach: use candidate sets with unit-based propagation
    cand_sets = {}
    for (r, c) in empties:
        b = (r // 3) * 3 + c // 3
        cand_sets[(r, c)] = set(d for d in "123456789"
                                 if d not in rows[r] and d not in cols[c] and d not in boxes[b])

    def eliminate(cell, d, trail):
        """Remove digit d from cell's candidates. Returns True if ok, False if contradiction."""
        s = cand_sets.get(cell)
        if s is None or d not in s:
            return True
        s.discard(d)
        trail.append((cell, d))
        if not s:
            return False
        if len(s) == 1:
            # assign this digit; eliminate from peers
            (only,) = s
            r, c = cell
            b = (r // 3) * 3 + c // 3
            rows[r].add(only)
            cols[c].add(only)
            boxes[b].add(only)
            grid[r][c] = only
            trail.append((cell, None))  # marker for assignment
            for p in peers[cell]:
                if grid[p[0]][p[1]] == '.':
                    if not eliminate(p, only, trail):
                        return False
        # check units: digit d must appear somewhere
        return True

    def unit_check(cell, trail):
        """For each unit containing cell, ensure each digit has a place."""
        for u in cell_units[cell]:
            for d in "123456789":
                places = [p for p in u if grid[p[0]][p[1]] == '.' and d in cand_sets.get(p, set())]
                if not places:
                    if not any(grid[p[0]][p[1]] == d for p in u):
                        return False
                elif len(places) == 1:
                    p = places[0]
                    if d not in cand_sets[p]:
                        continue
                    # assign p = d
                    s2 = cand_sets[p]
                    for other in list(s2):
                        if other != d:
                            if not eliminate(p, other, trail):
                                return False
        return True

    def full_propagate(trail):
        queue = list(empties)
        i = 0
        while i < len(queue):
            cell = queue[i]
            i += 1
            if not unit_check(cell, trail):
                return False
        return True

    # Backtracking search with MRV
    def search(trail):
        # find unsolved cell with fewest candidates
        best = None
        best_opts = 10
        for (r, c) in empties:
            s = cand_sets.get((r, c))
            if s is None:
                continue
            n = len(s)
            if n == 0:
                return False
            if n > 1 and n < best_opts:
                best_opts = n
                best = (r, c)
                if n == 2:
                    break
        if best is None:
            return True  # solved
        r, c = best
        for d in sorted(cand_sets[best]):
            trail = []
            ok = True
            # assign best = d
            s = cand_sets[best]
            for other in list(s):
                if other != d:
                    if not eliminate(best, other, trail):
                        ok = False
                        break
            if ok:
                if grid[r][c] == '.':
                    # elimination should have assigned it
                    ok = False
            if ok:
                if not unit_check(best, trail):
                    ok = False
            if ok:
                if search(trail):
                    return True
            # undo trail
            for item in reversed(trail):
                cell, dd = item
                if dd is None:
                    rr, cc = cell
                    b = (rr // 3) * 3 + cc // 3
                    dv = grid[rr][cc]
                    rows[rr].discard(dv)
                    cols[cc].discard(dv)
                    boxes[b].discard(dv)
                    grid[rr][cc] = '.'
                else:
                    cand_sets[cell].add(dd)
        return False

    empties_sorted = empties
    trail = []
    if not full_propagate(trail):
        raise ValueError("Unsolvable")
    if search([]):
        return [''.join(row) for row in grid]
    raise ValueError("Unsolvable")
