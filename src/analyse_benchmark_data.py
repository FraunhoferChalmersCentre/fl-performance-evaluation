'''
    Analysis of benchmark data
'''

import csv
import glob
import re
from collections import namedtuple

def read_data(file_name):
    Errors = []
    Accs = []
    VerificationRecord = namedtuple('VerificationRecord', 'error, accuracy')

    with open(file_name) as csvfile:
        readCSV = map(VerificationRecord._make, csv.reader(csvfile, delimiter=','))
        for row in readCSV:
            Errors.append(float(row.error))
            Accs.append(float(row.accuracy))
    return (Errors, Accs)


def mean(values):
    return sum(values)/len(values)


def sum_drops(vals):
    drop_sum = 0
    prev_val = vals[0]
    for index in range(1, len(vals)):
        val = vals[index]
        diff = prev_val - val
        if diff > 0:
            drop_sum += diff
        prev_val = val

    return drop_sum


def analyse(file_name, communication_rounds=1201):
    analyse_data = dict()

    errs, accs = read_data(file_name)[:communication_rounds]
    # Best
    analyse_data['min_errs'] = min(errs)
    analyse_data['max_accs'] = max(accs)
    # Average
    analyse_data['avg_accs'] = mean(accs)
    # Sum of drops
    analyse_data['drop_sum'] = sum_drops(accs)

    #print("avg:", avg_accs, "max:", max_accs, "max_drop:", drop_accs)

    return analyse_data


def write_latex_lines(file_name, data):
    with open(file_name, 'w') as f:
        f.write("$\\eta$ & max(acc) & min(err) & avg(acc) & sum(drop) \\\\ \hline\n")
        for dictionary in data:
            lr = dictionary['lr']
            min_err = dictionary['min_errs']
            max_acc = dictionary['max_accs']
            avg_acc = dictionary['avg_accs']
            drop_sum = dictionary['drop_sum']
            # 0.02   & 0.9537   & 0.1651 & 0.9502 & 4.234 \\ \hline
            latex_str = "{:.2} & {:.4} & {:.4} & {:.4} & {:.4} \\\\ \hline".format(lr, max_acc, min_err, avg_acc, drop_sum)
            f.write(latex_str + '\n')


def get_lr(file_name):
    match = re.search(r'(?<=_lr_)\d+.\d+', file_name)
    lr = float(match.group(0))
    return lr


def analyse_lr():
    # Read data
    reg_file_names = '../benchmark_results/fedavg/learning_rates/verification_log_lr*.csv'
    file_names = sorted(glob.glob(reg_file_names))

    data = []

    for file_name in file_names:
        print(file_name)
        lr = get_lr(file_name)
        result = analyse(file_name)
        result['lr'] = lr
        data.append(result)

    write_latex_lines('../benchmark_results/latex_lr_table_rows.txt', data)


def write_latex_lines_with_decay(file_name, data):
    with open(file_name, 'w') as f:
        f.write("$\\eta$ & $\\lambda$ & max(acc) & min(err) & avg(acc) & sum(drop) \\\\ \hline\n")
        for dictionary in data:
            lr = dictionary['lr']
            decay = dictionary['decay']
            min_err = dictionary['min_errs']
            max_acc = dictionary['max_accs']
            avg_acc = dictionary['avg_accs']
            drop_sum = dictionary['drop_sum']
            # 0.02   & 0.9537   & 0.1651 & 0.9502 & 4.234 \\ \hline
            latex_str = "{:.2} & {:.1e} & {:.4} & {:.4} & {:.4} & {:.4} \\\\ \hline".format(lr, decay, max_acc, min_err, avg_acc, drop_sum)
            f.write(latex_str + '\n')


def write_latex_lines_with_h(file_name, data):
    with open(file_name, 'w') as f:
        f.write("$h$ & max(acc) & min(err) & avg(acc) & sum(drop) \\\\ \hline\n")
        for dictionary in data:
            h = dictionary['h']
            min_err = dictionary['min_errs']
            max_acc = dictionary['max_accs']
            avg_acc = dictionary['avg_accs']
            drop_sum = dictionary['drop_sum']
            # 0.02   & 0.9537   & 0.1651 & 0.9502 & 4.234 \\ \hline
            latex_str = "{} & {:.4} & {:.4} & {:.4} & {:.4} \\\\ \hline".format(h, max_acc, min_err, avg_acc, drop_sum)
            f.write(latex_str + '\n')


def get_lr_decay(string):
    lr_match = re.search(r'(?<=_LR)\d+.\d+', string)
    decay_match = re.search(r'(?<=_Decay)\d+(.\d+)?(e-?\d+)?', string)

    lr = float(lr_match.group(0))
    decay = float(decay_match.group(0))

    return (lr, decay)


def extract_h(string):
    h_match = re.search(r'(?<=_h)\d+(.\d+)*', string)
    h = h_match.group(0)
    h = float(h)
    return h


def analyse_lr_decay():
    # Read data
    reg_file_names = '../benchmark_results/fedavg/lr_decay/verification_log_MNIST_nonIID_2NN_C10_E5_B20_LR*variant1.csv'
    file_names = sorted(glob.glob(reg_file_names))

    data = []

    for file_name in file_names:
        print(file_name)
        lr, decay = get_lr_decay(file_name)
        result = analyse(file_name)
        result['lr'] = lr
        result['decay'] = decay
        data.append(result)

    write_latex_lines_with_decay('../benchmark_results/latex_lr_decay_table_rows.txt', data)


def analyse_coop_lr_decay():
    # Read data
    reg_file_names = '../benchmark_results/coop/lr_decay/*.csv'
    file_names = sorted(glob.glob(reg_file_names))

    data = []

    for file_name in file_names:
        print(file_name)
        lr, decay = get_lr_decay(file_name)
        result = analyse(file_name, 5000)
        # Add more information to print
        result['lr'] = lr
        result['decay'] = decay
        data.append(result)

    write_latex_lines_with_decay('../benchmark_results/latex_coop_lr_decay_table_rows.txt', data)

def analyse_fsvrg():
    # Read data
    reg_file_names = '../benchmark_results/fsvrg/*.csv'
    file_names = sorted(glob.glob(reg_file_names))

    data = []

    for file_name in file_names:
        print(file_name)
        h = extract_h(file_name)
        result = analyse(file_name, 400)
        # Add more information to print
        result['h'] = h
        data.append(result)

    write_latex_lines_with_h('../benchmark_results/latex_fsvrg_h_table_rows.txt', data)


if __name__ == '__main__':
    analyse_coop_lr_decay()
    analyse_fsvrg()