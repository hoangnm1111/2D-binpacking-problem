import sys
import psutil
import os
import csv
import glob
import time

# Constants
MAXN = 10007
INF = float('inf')

# Global variables
N_items = 0
N_bins = 0
bin_used = 0
total_cost = 0
check_algorithm = False


# Item structure
class Item:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.area = 0
        self.corner_x = 0
        self.corner_y = 0
        self.id = 0
        self.pos_bin = 0
        self.rotated = False


# Free Rectangle structure
class FreeRectangle:
    def __init__(self):
        self.corner_x = 0
        self.corner_y = 0
        self.width = 0
        self.height = 0
        self.area = 0

    def __eq__(self, other):
        return (self.corner_x == other.corner_x and
                self.corner_y == other.corner_y and
                self.width == other.width and
                self.height == other.height)


# Bin structure
class Bin:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.area = 0
        self.free_area = 0
        self.cost = 0
        self.id = 0
        self.list_of_free_rec = []
        self.list_of_items = []


# Initialize arrays
item = [Item() for _ in range(MAXN)]
item_guillotine = [Item() for _ in range(MAXN)]
bin = [Bin() for _ in range(MAXN)]


# Comparison functions
def compare_item_by_longer_side(a, b):
    if a.height == b.height:
        return a.width > b.width
    return a.height > b.height


def compare_reset_item(a, b):
    return a.id < b.id


def compare_bin_by_density(a, b):
    density_a = a.cost / (a.width * a.height)
    density_b = b.cost / (b.width * b.height)
    if density_a == density_b:
        max_a = max(a.width, a.height)
        max_b = max(b.width, b.height)
        if max_a == max_b:
            return min(a.width, a.height) > min(b.width, b.height)
        return max_a > max_b
    return density_a < density_b


# Rotate item
def rotate_item(pack):
    pack.rotated = not pack.rotated
    pack.width, pack.height = pack.height, pack.width


# Check if item fits in a free rectangle
def check_fit_rec(rec, pack, rotated):
    if not rotated and pack.width <= rec.width and pack.height <= rec.height:
        return True
    if rotated and pack.width <= rec.height and pack.height <= rec.width:
        return True
    return False


# Add item to bin
def add_item(car, pack, rotated, x, y):
    if rotated:
        rotate_item(pack)
    pack.corner_x = x
    pack.corner_y = y
    car.list_of_items.append(pack)
    car.free_area -= pack.area


# Score calculation for ranking
def compare_ranking_rec_BSS(a, b):
    if a[0] == b[0]:
        return a[1] < b[1]
    return a[0] < b[0]


def score_rec(rec, pack, rotated):
    if rotated:
        short_side = min(rec.width - pack.height, rec.height - pack.width)
        long_side = max(rec.width - pack.height, rec.height - pack.width)
    else:
        short_side = min(rec.width - pack.width, rec.height - pack.height)
        long_side = max(rec.width - pack.width, rec.height - pack.height)
    return (short_side, long_side)


# Find best free rectangle for item
def best_ranking(car, pack):
    rotated = False
    best_rec = FreeRectangle()
    best_pos = 0
    check_exist = False
    best_score = (INF, INF)

    for i, rec in enumerate(car.list_of_free_rec):
        if check_fit_rec(rec, pack, False):
            score = score_rec(rec, pack, False)
            if compare_ranking_rec_BSS(score, best_score):
                best_score = score
                best_rec = rec
                best_pos = i
                rotated = False
                check_exist = True
        if check_fit_rec(rec, pack, True):
            score = score_rec(rec, pack, True)
            if compare_ranking_rec_BSS(score, best_score):
                best_score = score
                best_rec = rec
                best_pos = i
                rotated = True
                check_exist = True

    return ((best_rec, best_pos), (rotated, check_exist))


# Calculate solution
def calculate_solution():
    global total_cost, bin_used
    total_cost = 0
    bin_used = 0

    for j in range(1, N_bins + 1):
        if len(bin[j].list_of_items) > 0:
            total_cost += bin[j].cost
            bin_used += 1

    return (total_cost, bin_used)


# Check status (output results)
def checking_status(algorithm):
    if algorithm:
        sorted_items = sorted(item[1:N_items + 1], key=lambda x: x.id)
        for pack in sorted_items:
            print(f"{pack.id} {pack.pos_bin} {pack.corner_x} {pack.corner_y} {int(pack.rotated)}")
    else:
        sorted_items = sorted(item_guillotine[1:N_items + 1], key=lambda x: x.id)
        for pack in sorted_items:
            print(f"{pack.id} {pack.pos_bin} {pack.corner_x} {pack.corner_y} {int(pack.rotated)}")


# Guillotine Algorithm
def spliting_process_guillotine(horizontal, rec, pack):
    list_of_free_rec = []
    new_free_rec = FreeRectangle()

    right_x = rec.corner_x + pack.width
    right_y = rec.corner_y
    right_width = rec.width - pack.width
    top_x = rec.corner_x
    top_y = rec.corner_y + pack.height
    top_height = rec.height - pack.height

    right_height = pack.height if horizontal else rec.height
    top_width = rec.width if horizontal else pack.width

    if right_width > 0 and right_height > 0:
        new_free_rec.corner_x = right_x
        new_free_rec.corner_y = right_y
        new_free_rec.width = right_width
        new_free_rec.height = right_height
        list_of_free_rec.append(new_free_rec)

    new_free_rec = FreeRectangle()
    if top_width > 0 and top_height > 0:
        new_free_rec.corner_x = top_x
        new_free_rec.corner_y = top_y
        new_free_rec.width = top_width
        new_free_rec.height = top_height
        list_of_free_rec.append(new_free_rec)

    return list_of_free_rec


def spliting_guillotine(rec, pack):
    return spliting_process_guillotine(rec.width <= rec.height, rec, pack)


def merge_rec_guillotine(car):
    i = 0
    while i < len(car.list_of_free_rec):
        first = car.list_of_free_rec[i]
        check_exist_width = False
        check_exist_height = False
        pos_check_width = 0
        pos_check_height = 0

        for j in range(len(car.list_of_free_rec)):
            if j == i:
                continue
            second = car.list_of_free_rec[j]
            if (first.width == second.width and first.corner_x == second.corner_x and
                    second.corner_y == first.corner_y + first.height):
                check_exist_width = True
                pos_check_width = j
                break
            if (first.height == second.height and first.corner_y == second.corner_y and
                    second.corner_x == first.corner_x + first.width):
                check_exist_height = True
                pos_check_height = j
                break

        if check_exist_width:
            merged_rec = FreeRectangle()
            merged_rec.width = first.width
            merged_rec.height = first.height + car.list_of_free_rec[pos_check_width].height
            merged_rec.area = merged_rec.width * merged_rec.height
            merged_rec.corner_x = first.corner_x
            merged_rec.corner_y = first.corner_y
            del car.list_of_free_rec[pos_check_width]
            if pos_check_width < i:
                i -= 1
            del car.list_of_free_rec[i]
            i -= 1
            car.list_of_free_rec.append(merged_rec)

        elif check_exist_height:
            merged_rec = FreeRectangle()
            merged_rec.width = first.width + car.list_of_free_rec[pos_check_height].width
            merged_rec.height = first.height
            merged_rec.area = merged_rec.width * merged_rec.height
            merged_rec.corner_x = first.corner_x
            merged_rec.corner_y = first.corner_y
            del car.list_of_free_rec[pos_check_height]
            if pos_check_height < i:
                i -= 1
            del car.list_of_free_rec[i]
            i -= 1
            car.list_of_free_rec.append(merged_rec)

        i += 1


def insert_item_guillotine(car, pack):
    best_ranking_return = best_ranking(car, pack)

    if not best_ranking_return[1][1]:
        return False

    pack.pos_bin = car.id
    best_rec = best_ranking_return[0][0]
    best_pos = best_ranking_return[0][1]
    rotated = best_ranking_return[1][0]

    add_item(car, pack, rotated, best_rec.corner_x, best_rec.corner_y)
    del car.list_of_free_rec[best_pos]

    new_rec = spliting_guillotine(best_rec, pack)
    car.list_of_free_rec.extend(new_rec)

    merge_rec_guillotine(car)
    return True


def solve_guillotine():
    for i in range(1, N_items + 1):
        for j in range(1, N_bins + 1):
            if insert_item_guillotine(bin[j], item[i]):
                break


# Maximal Rectangles Algorithm
def spliting_process_maxrec(rec, pack):
    list_of_free_rec = []
    new_free_rec = FreeRectangle()

    if pack.width < rec.width:
        new_free_rec.width = rec.width - pack.width
        new_free_rec.height = rec.height
        new_free_rec.corner_x = rec.corner_x + pack.width
        new_free_rec.corner_y = rec.corner_y
        list_of_free_rec.append(new_free_rec)

    new_free_rec = FreeRectangle()
    if pack.height < rec.height:
        new_free_rec.width = rec.width
        new_free_rec.height = rec.height - pack.height
        new_free_rec.corner_x = rec.corner_x
        new_free_rec.corner_y = rec.corner_y + pack.height
        list_of_free_rec.append(new_free_rec)

    return list_of_free_rec


def check_intersec_maxrec(rec, pack):
    if pack.corner_x >= rec.corner_x + rec.width:
        return False
    if pack.corner_y >= rec.corner_y + rec.height:
        return False
    if pack.corner_x + pack.width <= rec.corner_x:
        return False
    if pack.corner_y + pack.height <= rec.corner_y:
        return False
    return True


def find_overlap_maxrec(rec, pack):
    overlap_rec = FreeRectangle()
    overlap_rec.corner_x = max(rec.corner_x, pack.corner_x)
    overlap_rec.corner_y = max(rec.corner_y, pack.corner_y)
    overlap_rec.width = min(rec.corner_x + rec.width, pack.corner_x + pack.width) - overlap_rec.corner_x
    overlap_rec.height = min(rec.corner_y + rec.height, pack.corner_y + pack.height) - overlap_rec.corner_y
    return overlap_rec


def split_intersect_maxrec(initial_rec, overlap_rec):
    list_of_free_rec = []
    new_free_rec = FreeRectangle()

    if overlap_rec.corner_x > initial_rec.corner_x:
        new_free_rec.corner_x = initial_rec.corner_x
        new_free_rec.corner_y = initial_rec.corner_y
        new_free_rec.width = overlap_rec.corner_x - new_free_rec.corner_x
        new_free_rec.height = initial_rec.height
        list_of_free_rec.append(new_free_rec)

    new_free_rec = FreeRectangle()
    if overlap_rec.corner_x + overlap_rec.width < initial_rec.corner_x + initial_rec.width:
        new_free_rec.corner_x = overlap_rec.corner_x + overlap_rec.width
        new_free_rec.corner_y = initial_rec.corner_y
        new_free_rec.width = initial_rec.corner_x + initial_rec.width - new_free_rec.corner_x
        new_free_rec.height = initial_rec.height
        list_of_free_rec.append(new_free_rec)

    new_free_rec = FreeRectangle()
    if overlap_rec.corner_y > initial_rec.corner_y:
        new_free_rec.corner_x = initial_rec.corner_x
        new_free_rec.corner_y = initial_rec.corner_y
        new_free_rec.width = initial_rec.width
        new_free_rec.height = overlap_rec.corner_y - new_free_rec.corner_y
        list_of_free_rec.append(new_free_rec)

    new_free_rec = FreeRectangle()
    if overlap_rec.corner_y + overlap_rec.height < initial_rec.corner_y + initial_rec.height:
        new_free_rec.corner_x = initial_rec.corner_x
        new_free_rec.corner_y = overlap_rec.corner_y + overlap_rec.height
        new_free_rec.width = initial_rec.width
        new_free_rec.height = initial_rec.corner_y + initial_rec.height - new_free_rec.corner_y
        list_of_free_rec.append(new_free_rec)

    return list_of_free_rec


def check_covered_maxrec(rec_covering, rec_covered):
    if (rec_covered.corner_x > rec_covering.corner_x + rec_covering.width or
            rec_covered.corner_y > rec_covering.corner_y + rec_covering.height or
            rec_covered.corner_x + rec_covered.width < rec_covering.corner_x or
            rec_covered.corner_y + rec_covered.height < rec_covering.corner_y):
        return False

    if (rec_covered.corner_x < rec_covering.corner_x or
            rec_covered.corner_y < rec_covering.corner_y or
            rec_covered.corner_x + rec_covered.width > rec_covering.corner_x + rec_covering.width or
            rec_covered.corner_y + rec_covered.height > rec_covering.corner_y + rec_covering.height):
        return False

    return True


def remove_covered_rec_maxrec(car):
    i = 0
    while i < len(car.list_of_free_rec):
        first = car.list_of_free_rec[i]
        j = i + 1
        while j < len(car.list_of_free_rec):
            second = car.list_of_free_rec[j]
            if check_covered_maxrec(first, second):
                del car.list_of_free_rec[j]
                continue
            if check_covered_maxrec(second, first):
                del car.list_of_free_rec[i]
                i -= 1
                break
            j += 1
        i += 1


def remove_overlap_maxrec(car, pack):
    i = 0
    while i < len(car.list_of_free_rec):
        rec = car.list_of_free_rec[i]
        if check_intersec_maxrec(rec, pack):
            overlap_rec = find_overlap_maxrec(rec, pack)
            new_rec = split_intersect_maxrec(rec, overlap_rec)
            del car.list_of_free_rec[i]
            car.list_of_free_rec.extend(new_rec)
            i -= 1
        i += 1
    remove_covered_rec_maxrec(car)


def insert_item_maxrec(car, pack):
    best_ranking_return = best_ranking(car, pack)

    if not best_ranking_return[1][1]:
        return False

    pack.pos_bin = car.id
    best_rec = best_ranking_return[0][0]
    best_pos = best_ranking_return[0][1]
    rotated = best_ranking_return[1][0]

    add_item(car, pack, rotated, best_rec.corner_x, best_rec.corner_y)
    del car.list_of_free_rec[best_pos]

    new_rec = spliting_process_maxrec(best_rec, pack)
    car.list_of_free_rec.extend(new_rec)

    remove_overlap_maxrec(car, pack)
    return True


def solve_maxrec():
    for i in range(1, N_items + 1):
        for j in range(1, N_bins + 1):
            if insert_item_maxrec(bin[j], item[i]):
                break


# Main program
def enter(file_path):
    global N_items, N_bins
    with open(file_path, 'r') as f:
        # Đọc dòng đầu tiên: N_items và N_bins
        N_items, N_bins = map(int, f.readline().split())

        # Đọc thông tin các vật phẩm
        for i in range(1, N_items + 1):
            item[i].width, item[i].height = map(int, f.readline().split())
            if item[i].width > item[i].height:
                rotate_item(item[i])
            item[i].area = item[i].width * item[i].height
            item[i].id = i

        # Đọc thông tin các hộp
        for j in range(1, N_bins + 1):
            bin[j].width, bin[j].height, bin[j].cost = map(int, f.readline().split())
            bin[j].area = bin[j].width * bin[j].height
            bin[j].id = j
            bin[j].free_area = bin[j].area
            first_rec = FreeRectangle()
            first_rec.width = bin[j].width
            first_rec.height = bin[j].height
            first_rec.corner_x = 0
            first_rec.corner_y = 0
            first_rec.area = first_rec.width * first_rec.height
            bin[j].list_of_free_rec.append(first_rec)

    # Sắp xếp các vật phẩm và hộp (giữ nguyên logic ban đầu)
    item[1:N_items + 1] = sorted(item[1:N_items + 1], key=lambda x: (-x.height, -x.width))
    bin[1:N_bins + 1] = sorted(bin[1:N_bins + 1], key=lambda x: (
        x.cost / (x.width * x.height), -max(x.width, x.height), -min(x.width, x.height)))


def reset():
    global total_cost
    total_cost = 0

    for i in range(1, N_items + 1):
        item_guillotine[i] = Item()
        item_guillotine[i].width = item[i].width
        item_guillotine[i].height = item[i].height
        item_guillotine[i].area = item[i].area
        item_guillotine[i].corner_x = item[i].corner_x
        item_guillotine[i].corner_y = item[i].corner_y
        item_guillotine[i].id = item[i].id
        item_guillotine[i].pos_bin = item[i].pos_bin
        item_guillotine[i].rotated = item[i].rotated
        item[i].corner_x = 0
        item[i].corner_y = 0

    for j in range(1, N_bins + 1):
        bin[j].free_area = bin[j].area
        bin[j].list_of_items = []
        bin[j].list_of_free_rec = []
        first_rec = FreeRectangle()
        first_rec.width = bin[j].width
        first_rec.height = bin[j].height
        first_rec.corner_x = 0
        first_rec.corner_y = 0
        first_rec.area = first_rec.width * first_rec.height
        bin[j].list_of_free_rec.append(first_rec)


def solve(file_path):
    """Chạy thuật toán cho một file đầu vào và trả về kết quả."""
    global check_algorithm, total_cost, bin_used, N_items, N_bins
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024  # Bộ nhớ trước, tính bằng MB
    start_time = time.time()  # Thời gian bắt đầu

    # Chạy thuật toán
    enter(file_path)
    solve_guillotine()
    guillotine_result = calculate_solution()

    reset()

    solve_maxrec()
    maxrec_result = calculate_solution()

    # So sánh kết quả
    if guillotine_result[0] < maxrec_result[0]:
        total_cost = guillotine_result[0]
        bin_used = guillotine_result[1]
        check_algorithm = False
    else:
        total_cost = maxrec_result[0]
        bin_used = maxrec_result[1]
        check_algorithm = True

    # Tính thời gian và bộ nhớ
    running_time = time.time() - start_time
    mem_after = process.memory_info().rss / 1024 / 1024
    mem_cost = mem_after - mem_before

    # In kết quả
    print(f"File: {os.path.basename(file_path)}")
    print(f"Total cost: {total_cost}")
    checking_status(check_algorithm)

    return {
        'file_name': os.path.basename(file_path),
        'n': N_items,
        'k': N_bins,
        'cost': total_cost,
        'running_time': running_time,
        'mem_cost': mem_cost
    }

def print_output():
    checking_status(check_algorithm)


def main():
    # Cấu hình
    input_folder = '/home/ad/PycharmProjects/TULKH/2D-bin-packing-problem/input'  # Thay đổi đường dẫn nếu cần
    output_csv = 'results_heuristic.csv'

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
            try:
                result = solve(file_path)
                writer.writerow(result)
                print_output()
            except Exception as e:
                print(f"Lỗi khi xử lý file {file_path}: {e}")
                # Ghi kết quả mặc định nếu có lỗi
                writer.writerow({
                    'file_name': os.path.basename(file_path),
                    'n': -1,
                    'k': -1,
                    'cost': -1,
                    'running_time': 0,
                    'mem_cost': 0
                })



if __name__ == "__main__":
    main()
