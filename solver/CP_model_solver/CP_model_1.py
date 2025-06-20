from ortools.sat.python import cp_model
import sys


def input_data():
    '''
        Return number of items (n); number of bins (k);
        and a dictionary containing item sizes, truck sizes, and costs.
        Reads input from standard input (keyboard).
    '''
    data = {}
    # Read first line: N and K
    n, k = map(int, input().split())
    data['size_item'] = []
    data['size_truck'] = []
    data['cost'] = []

    # Read N lines for item sizes
    for _ in range(n):
        w, l = map(int, input().split())
        data['size_item'].append([w, l])

    # Read K lines for truck sizes and costs
    for _ in range(k):
        w, l, c = map(int, input().split())
        data['size_truck'].append([w, l])
        data['cost'].append(c)

    W_truck = [data['size_truck'][i][0] for i in range(k)]
    H_truck = [data['size_truck'][i][1] for i in range(k)]
    return n, k, data, W_truck, H_truck


def main_solver(time_limit: int = 300):
    n, k, data, W_truck, H_truck = input_data()

    max_W = max(W_truck)
    max_H = max(H_truck)

    # Creates the model
    model = cp_model.CpModel()

    # Constant for big-M method
    M = 1000000

    # Variables
    x = {}  # x[(i,m)] = 1 iff item i is packed in bin m
    Ro = {}  # Ro[i] = 1 if item i is rotated 90 degrees
    l = {}  # left coordinate of item
    r = {}  # right coordinate of item
    t = {}  # top coordinate of item
    b = {}  # bottom coordinate of item

    for i in range(n):
        Ro[i] = model.NewBoolVar(f'Ro[{i}]')
        l[i] = model.NewIntVar(0, max_W, f'l[{i}]')
        r[i] = model.NewIntVar(0, max_W, f'r[{i}]')
        t[i] = model.NewIntVar(0, max_H, f't[{i}]')
        b[i] = model.NewIntVar(0, max_H, f'b[{i}]')

        # Coordinate constraints based on rotation
        model.Add(r[i] == l[i] + (1 - Ro[i]) * data['size_item'][i][0] + Ro[i] * data['size_item'][i][1])
        model.Add(t[i] == b[i] + (1 - Ro[i]) * data['size_item'][i][1] + Ro[i] * data['size_item'][i][0])

        for m in range(k):
            x[(i, m)] = model.NewBoolVar(f'x_[{i}]_[{m}]')

            # Item must not exceed bin area
            model.Add(r[i] <= (1 - x[(i, m)]) * M + W_truck[m])
            model.Add(l[i] <= (1 - x[(i, m)]) * M + W_truck[m])
            model.Add(t[i] <= (1 - x[(i, m)]) * M + H_truck[m])
            model.Add(b[i] <= (1 - x[(i, m)]) * M + H_truck[m])

    # Each item must be packed in exactly one bin
    for i in range(n):
        model.Add(sum(x[(i, m)] for m in range(k)) == 1)

    # If two items are in the same bin, they must not overlap
    for i in range(n - 1):
        for j in range(i + 1, n):
            for m in range(k):
                e = model.NewBoolVar(f'e[{i}][{j}]')
                model.Add(e >= x[(i, m)] + x[(j, m)] - 1)
                model.Add(e <= x[(i, m)])
                model.Add(e <= x[(j, m)])

                # Binary variables for each non-overlap constraint
                c1 = model.NewBoolVar(f'c1[{i}][{j}]')
                c2 = model.NewBoolVar(f'c2[{i}][{j}]')
                c3 = model.NewBoolVar(f'c3[{i}][{j}]')
                c4 = model.NewBoolVar(f'c4[{i}][{j}]')

                # Non-overlap constraints using big-M
                model.Add(r[i] <= l[j] + M * (1 - c1))
                model.Add(r[j] <= l[i] + M * (1 - c2))
                model.Add(t[i] <= b[j] + M * (1 - c3))
                model.Add(t[j] <= b[i] + M * (1 - c4))

                model.Add(c1 + c2 + c3 + c4 + (1 - e) * M >= 1)
                model.Add(c1 + c2 + c3 + c4 <= e * M)

    # Determine which bins are used
    z = {}
    for m in range(k):
        z[m] = model.NewBoolVar(f'z[{m}]')
        q = model.NewIntVar(0, n, f'q[{m}]')
        model.Add(q == sum(x[(i, m)] for i in range(n)))
        model.Add(z[m] <= q * M)
        model.Add(q <= z[m] * M)

    # Objective function
    cost = sum(z[m] * data['cost'][m] for m in range(k))
    model.Minimize(cost)

    # Create a solver and solve the model
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    status = solver.Solve(model)

    # Print the results in the required format
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for i in range(n):
            truck = None
            for m in range(k):
                if solver.Value(x[(i, m)]) == 1:
                    truck = m + 1  # Truck numbers are 1-based
                    break
            print(f"{i + 1} {truck} {solver.Value(l[i])} {solver.Value(b[i])} {int(solver.Value(Ro[i]))}")
        print(f'  - branches        : {solver.NumBranches()}')
    else:
        print("NO SOLUTIONS")


if __name__ == "__main__":
    try:
        time_limit = int(sys.argv[1])
    except IndexError:
        time_limit = 300

    main_solver(time_limit)