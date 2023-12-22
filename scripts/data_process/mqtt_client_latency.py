import os
import pandas as pd
import matplotlib.pyplot as plt


def process_log_files(paths):
    data = {}
    for path in paths:
        df = pd.read_csv(path, header=None, names=[
                         'ValueSize', 'Threads', 'SubNumber', 'QoS', 'Latency'])
        df_filtered = df[(df['ValueSize'] == 1024) & (df['QoS'] == 1)]

        def remove_extremes(group):
            if len(group) > 2:
                group = group.drop(group['Latency'].idxmax()).drop(
                    group['Latency'].idxmin())
            return group
        grouped = df_filtered.groupby(
            'Threads', as_index=False).apply(remove_extremes)
        data[path] = grouped.groupby('Threads', as_index=False).mean()

    return data


log_file_paths = ['/root/workspace/deploy/perfcal/perfcal/shell/log/mqtt/perfcal/latency.log',
                  '/root/workspace/deploy/perfcal/perfcal/shell/log/mqtt/pgo/latency.log',
                  '/root/workspace/deploy/perfcal/perfcal/shell/log/mqtt/emqx/latency.log']
labels = ['PerfCal-MQ', 'PGo-MQ', 'emqx']

grouped_data = process_log_files(log_file_paths)

plt.figure(figsize=(10, 6))
colors = ['blue', 'red', 'green', 'orange', 'purple']
markers = ['s', 'x', 'o', '^', 'd']

if not os.path.exists('data/csv/MQClientLatency'):
    os.makedirs('data/csv/MQClientLatency')
for i, (path, grouped) in enumerate(grouped_data.items()):
    plt.plot(grouped['Threads'], grouped['Latency'], color=colors[i % len(colors)], label=labels[i % len(
        labels)], marker=markers[i % len(markers)], linestyle='-', linewidth=2, markersize=8)
    grouped.to_csv(f'data/csv/MQClientLatency/{labels[i % len(labels)]}.csv')
plt.xlabel('Number of Publishers', fontsize=16)
plt.ylabel('Latency (ms)', fontsize=16)
plt.xscale("log")
plt.yscale("log")
plt.tick_params(axis='both', labelsize=16)
plt.legend(fontsize=16)
plt.grid(True)
plt.savefig('data/MQClientLatency.pdf', dpi=300)
