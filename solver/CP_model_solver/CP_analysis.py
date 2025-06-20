from ortools.sat.python import cp_model
import sys
import psutil
import os
import csv
import glob
import time

def input_data(file_path):
    """Đọc dữ liệu đầu vào từ file."""
    data = {}
    try:
        with open(file_path, 'r') as f:
            # Đọc số lượng vật phẩm (n) và hộp (k)
            n, k = map(int, f.readline().split())
            data['size_item'] = []
            data['size_truck'] = []
            data['cost'] = []

            # Đọc kích thước các vật phẩm
            for _ in range(n):
                w, l = map(int, f.readline().split())
                data['size_item'].append([w, l])

            # Đọc kích thước và chi phí các hộp
            for _ in range(k):
                w, l, c = map(int, f.readline().split())
                data['size_truck'].append([w, l])
                data['cost'].append(c)

        W_truck = [data['size_truck'][i][0] for i in range(k)]
        H_truck = [data['size_truck'][i][1] for i in range(k)]
        return n, k, data, W_truck, H_truck
    except Exception as e:
        print(f"Lỗi khi đọc file {file_path}: {e}")
        return None

def solve_bin_packing(file_path, time_limit=300):
    """Giải bài toán đóng gói hộp cho một file đầu vào."""
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024  # Bộ nhớ trước, tính bằng MB
    start_time = time.time()  # Thời gian bắt đầu

    # Đọc dữ liệu
    result = input_data(file_path)
    if result is None:
        return {
            'file_name': os.path.basename(file_path),
            'n': -1,
            'k': -1,
            'cost': -1,
            'running_time': 0,
            'mem_cost': 0
        }

    n, k, data, W_truck, H_truck = result
    max_W = max(W_truck)
    max_H = max(H_truck)

    # Tạo mô hình CP
    model = cp_model.CpModel()

    # Hằng số big-M
    M = 1000000

    # Biến
    x = {}  # x[(i,m)] = 1 nếu vật phẩm i được đặt trong hộp m
    Ro = {}  # Ro[i] = 1 nếu vật phẩm i được xoay 90 độ
    l = {}  # Tọa độ trái
    r = {}  # Tọa độ phải
    t = {}  # Tọa độ trên
    b = {}  # Tọa độ dưới

    for i in range(n):
        Ro[i] = model.NewBoolVar(f'Ro[{i}]')
        l[i] = model.NewIntVar(0, max_W, f'l[{i}]')
        r[i] = model.NewIntVar(0, max_W, f'r[{i}]')
        t[i] = model.NewIntVar(0, max_H, f't[{i}]')
        b[i] = model.NewIntVar(0, max_H, f'b[{i}]')

        # Ràng buộc tọa độ dựa trên xoay
        model.Add(r[i] == l[i] + (1 - Ro[i]) * data['size_item'][i][0] + Ro[i] * data['size_item'][i][1])
        model.Add(t[i] == b[i] + (1 - Ro[i]) * data['size_item'][i][1] + Ro[i] * data['size_item'][i][0])

        for m in range(k):
            x[(i, m)] = model.NewBoolVar(f'x_[{i}]_[{m}]')
            # Vật phẩm không được vượt quá kích thước hộp
            model.Add(r[i] <= (1 - x[(i, m)]) * M + W_truck[m])
            model.Add(l[i] <= (1 - x[(i, m)]) * M + W_truck[m])
            model.Add(t[i] <= (1 - x[(i, m)]) * M + H_truck[m])
            model.Add(b[i] <= (1 - x[(i, m)]) * M + H_truck[m])

    # Mỗi vật phẩm chỉ được đặt trong một hộp
    for i in range(n):
        model.Add(sum(x[(i, m)] for m in range(k)) == 1)

    # Ràng buộc không chồng lấn
    for i in range(n - 1):
        for j in range(i + 1, n):
            for m in range(k):
                e = model.NewBoolVar(f'e[{i}][{j}]')
                model.Add(e >= x[(i, m)] + x[(j, m)] - 1)
                model.Add(e <= x[(i, m)])
                model.Add(e <= x[(j, m)])
                c1 = model.NewBoolVar(f'c1[{i}][{j}]')
                c2 = model.NewBoolVar(f'c2[{i}][{j}]')
                c3 = model.NewBoolVar(f'c3[{i}][{j}]')
                c4 = model.NewBoolVar(f'c4[{i}][{j}]')
                model.Add(r[i] <= l[j] + M * (1 - c1))
                model.Add(r[j] <= l[i] + M * (1 - c2))
                model.Add(t[i] <= b[j] + M * (1 - c3))
                model.Add(t[j] <= b[i] + M * (1 - c4))
                model.Add(c1 + c2 + c3 + c4 + (1 - e) * M >= 1)
                model.Add(c1 + c2 + c3 + c4 <= e * M)

    # Xác định hộp được sử dụng
    z = {}
    for m in range(k):
        z[m] = model.NewBoolVar(f'z[{m}]')
        q = model.NewIntVar(0, n, f'q[{m}]')
        model.Add(q == sum(x[(i, m)] for i in range(n)))
        model.Add(z[m] <= q * M)
        model.Add(q <= z[m] * M)

    # Hàm mục tiêu: Tối thiểu hóa chi phí
    cost = sum(z[m] * data['cost'][m] for m in range(k))
    model.Minimize(cost)

    # Tạo solver và giải
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    status = solver.Solve(model)

    # Tính thời gian chạy và bộ nhớ tiêu thụ
    running_time = time.time() - start_time
    mem_after = process.memory_info().rss / 1024 / 1024
    mem_cost = mem_after - mem_before

    # Chuẩn bị kết quả
    result = {
        'file_name': os.path.basename(file_path),
        'n': n,
        'k': k,
        'cost': -1,
        'running_time': running_time,
        'mem_cost': mem_cost
    }

    # Xử lý kết quả
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        result['cost'] = solver.ObjectiveValue()
        print('--------------Solution Found--------------')
        for i in range(n):
            truck = None
            for m in range(k):
                if solver.Value(x[(i, m)]) == 1:
                    truck = m + 1
                    break
            print(f"{i + 1} {truck} {solver.Value(l[i])} {solver.Value(b[i])} {int(solver.Value(Ro[i]))}")
        print('----------------Statistics----------------')
        print('Status              :', 'OPTIMAL' if status == cp_model.OPTIMAL else 'FEASIBLE')
        print(f'Time limit          : {time_limit}')
        print(f'Running time        : {running_time:.3f} seconds')
        print(f'Memory consumed     : {mem_cost:.2f} MB')
        print(f'Total cost          : {solver.ObjectiveValue()}')
    else:
        print(f'No solution found for {file_path}')

    return result

if __name__ == '__main__':
    # Cấu hình
    input_folder = '/home/ad/PycharmProjects/TULKH/2D-bin-packing-problem/input_hust'  # Thay đổi đường dẫn nếu cần
    output_csv = 'results_cp_huststack_ver1.csv'
    time_limit = 300

    # Kiểm tra thư mục đầu vào
    if not os.path.exists(input_folder):
        print(f"Thư mục {input_folder} không tồn tại")
        sys.exit(1)

    # Lấy danh sách file .txt
    input_files = glob.glob(os.path.join(input_folder, '*.txt'))
    if not input_files:
        print(f"Không tìm thấy file .txt nào trong {input_folder}")
        sys.exit(1)

    # Ghi kết quả vào file CSV
    with open(output_csv, 'w', newline='') as csvfile:
        fieldnames = ['file_name', 'n', 'k', 'cost', 'running_time', 'mem_cost']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # Xử lý từng file
        for file_path in input_files:
            print(f'\nProcessing file: {file_path}')
            result = solve_bin_packing(file_path, time_limit)
            writer.writerow(result)