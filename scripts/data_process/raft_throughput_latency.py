# # Save the figure
# plt.savefig('loadbalance.png', dpi=300)
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os
if not os.path.exists('data/csv/raftThroughputLatency'):
    os.makedirs('data/csv/raftThroughputLatency')
plt.rcParams.update({'font.size': 24})


def process_log_files(paths):
    data = {}
    for path in paths:
        df = pd.read_csv(path, header=None, names=[
                         'Threads', 'Throughput', 'Latency', 'ValueSize', 'Ratio'])
        df = df[(df['ValueSize'] == 1024) & (df['Ratio'] == 0.05)]

        def remove_extremes(group):
            if len(group) > 2:
                return group.drop(group['Throughput'].idxmax()).drop(group['Throughput'].idxmin())
            return group
        grouped = df.groupby(['Threads', 'ValueSize', 'Ratio']).apply(
            remove_extremes).reset_index(drop=True)
        data[path] = grouped.groupby(
            ['Threads', 'ValueSize', 'Ratio']).mean().reset_index()
    return data


log_file_paths = ['/root/workspace/deploy/profile/profile/shell/log/raft/profile/profile.log',
                  '/root/workspace/deploy/profile/profile/shell/log/raft/pgo/pgo.log',
                  '/root/workspace/deploy/profile/profile/shell/log/raft/etcd/etcd.log']
labels = ['PerfCal-RaftKV', 'PGo-RaftKV', 'etcd']
grouped_data = process_log_files(log_file_paths)

plt.figure(figsize=(12, 6))

colors = ['blue', 'red', 'green', 'orange', 'purple']
markers = ['s', 'x', '^', 'o', 'd']


for i, (path, grouped) in enumerate(grouped_data.items()):
    plt.scatter(grouped['Throughput'], grouped['Latency'], color=colors[i % len(
        colors)], label=labels[i % len(labels)], marker=markers[i % len(markers)],  s=100)
    grouped.to_csv(
        f'data/csv/raftThroughputLatency/{labels[i % len(labels)]}.csv')
plt.xlabel('Throughput (op/s)', fontsize=30)
plt.ylabel('Latency (ms)', fontsize=30)
plt.tick_params(axis='both')
plt.xscale("log")
plt.yscale("log")
plt.legend(loc='upper center', bbox_to_anchor=(
    0.43, 1.25), ncol=3, frameon=False, fontsize=30)
plt.grid(True)

plt.tight_layout()

plt.subplots_adjust(top=0.8, bottom=0.2, left=0.12, right=0.98)

plt.savefig('data/raftThroughputLatency.pdf', dpi=300)
