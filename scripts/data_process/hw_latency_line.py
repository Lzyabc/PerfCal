import os
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 24})


def plot_combined_latency_distributions(filenames, threads_question_combinations, labels):
    plt.figure(figsize=(12, 8))

    colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k']
    markers = ['o', 's', '^', 'D', 'v', '<', '>']
    linestyles = ['-', '--', '-.', ':',
                  (0, (3, 5, 1, 5)), (0, (3, 1, 1, 1)), (0, (1, 10))]
    if len(colors) < len(threads_question_combinations) or len(markers) < len(filenames):
        raise ValueError(
            "Not enough colors or markers for the number of configurations/files.")

    if not os.path.exists('data/csv/HWLatencyDistribution'):
        os.makedirs('data/csv/HWLatencyDistribution')

    def convert(threads, _):
        if threads == 1000:
            return "High"
        else:
            return "Low"

    for file_idx, filename in enumerate(filenames):
        for config_idx, (threads, question_number) in enumerate(threads_question_combinations):
            df = pd.read_csv(filename)
            filtered_df = df[(df['Threads'] == threads) & (
                df['Question Number'] == question_number)]
            if filtered_df.empty:
                continue

            latency_data = filtered_df.iloc[:, -10:].mean() / 1000
            label = f'{labels[file_idx]}-{convert(threads, question_number)}'
            plt.plot(range(10, 110, 10), latency_data,
                     color=colors[file_idx], marker=markers[config_idx], linestyle=linestyles[config_idx],  markersize=12, label=label)
            latency_data.to_csv(
                f'data/csv/HWLatencyDistribution/{labels[file_idx]}_Threads{threads}_QN{question_number}.csv')

    plt.xlabel('Percentile', fontsize=30)
    plt.ylabel('Tail Latency (ms)', fontsize=30)
    # plt.title('Latency Distributions', fontsize=30)
    plt.yscale('log')
    plt.grid(True)
    plt.tight_layout()
    plt.legend(loc='upper center', bbox_to_anchor=(
        0.43, 1.3), ncol=3, frameon=False, fontsize=30)
    plt.subplots_adjust(top=0.82, bottom=0.13, left=0.12, right=0.98)
    plt.grid(True)
    plt.savefig('data/HWLatencyDistribution.pdf', dpi=300)


file_path = ['../log/hw/perfcal/details_new.log',
             '../log/hw/pgo/details_new.log',
             '../log/hw/manual/details_new.log']

labels = ['PF', 'PG', 'ML']


combinations = [(50, 5), (1000, 100)]
plot_combined_latency_distributions(file_path, combinations, labels=labels)
