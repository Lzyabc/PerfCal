import pandas as pd
import matplotlib.pyplot as plt
import os
if not os.path.exists('data/csv/raftClientThroughput'):
    os.makedirs('data/csv/raftClientThroughput')
plt.rcParams.update({'font.size': 24})


def process_log_files(paths):
    data = {}
    for path in paths:
        df = pd.read_csv(path, header=None, names=[
                         'Threads', 'Throughput', 'Latency', 'Request', 'ReadWrite'])
        df = df[df['Threads'] <= 900]

        df_filtered = df[(df['Request'] == 1024) & (df['ReadWrite'] == 0.05)]

        def remove_extremes(group):
            if len(group) > 2:
                group = group.drop(group['Throughput'].idxmax()).drop(
                    group['Throughput'].idxmin())
            return group
        grouped = df_filtered.groupby('Threads').apply(
            remove_extremes).reset_index(drop=True)
        data[path] = grouped.groupby('Threads').mean().reset_index()
    return data


log_file_paths = ['/root/workspace/deploy/perfcal/perfcal/shell/log/raft/perfcal/perfcal.log',
                  '/root/workspace/deploy/perfcal/perfcal/shell/log/raft/pgo/pgox.log',
                  '/root/workspace/deploy/perfcal/perfcal/shell/log/raft/etcd/etcd.log']
labels = ['PerfCal-RaftKV', 'PGo-RaftKV', 'etcd']
grouped_data = process_log_files(log_file_paths)
plt.figure(figsize=(12, 6))
colors = ['blue', 'red', 'green', 'orange', 'purple']
markers = ['s', 'x', 'o', '^', 'd']
for i, (path, grouped) in enumerate(grouped_data.items()):
    plt.plot(grouped['Threads'], grouped['Throughput'], color=colors[i % len(colors)], label=labels[i % len(
        labels)], marker=markers[i % len(markers)], linestyle='-', linewidth=2, markersize=12)
    grouped.to_csv(
        f'data/csv/raftClientThroughput/{labels[i % len(labels)]}.csv')

plt.xlabel('Number of Clients', fontsize=30)
plt.ylabel('Throughput (op/s)', fontsize=30)
plt.xscale("log")
plt.yscale("log")

plt.tick_params(axis='both')
plt.legend(loc='upper center', bbox_to_anchor=(
    0.43, 1.25), ncol=3, frameon=False, fontsize=30)
plt.grid(True)

plt.tight_layout()
plt.subplots_adjust(top=0.85, bottom=0.15, left=0.12, right=0.98)
plt.savefig('data/raftClientThroughput.pdf', dpi=300)
