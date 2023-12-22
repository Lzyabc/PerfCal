import os
import pandas as pd
import matplotlib.pyplot as plt
if not os.path.exists('data/csv/RaftMaxThroughputBarChart'):
    os.makedirs('data/csv/RaftMaxThroughputBarChart')

plt.rcParams.update({'font.size': 24})


def process_log_files(paths):
    data = {}
    for path in paths:
        df = pd.read_csv(path, header=None, names=[
                         'Threads', 'Throughput', 'Latency', 'ValueSize', 'Ratio'])

        def remove_extremes(group):
            if len(group) > 2:
                group = group.drop(group['Throughput'].idxmax()).drop(
                    group['Throughput'].idxmin())
            return group
        grouped = df.groupby(['Threads', 'ValueSize', 'Ratio']).apply(
            remove_extremes).reset_index(drop=True)
        avg_throughput = grouped.groupby(
            ['Threads', 'ValueSize', 'Ratio']).mean().reset_index()

        max_throughput = avg_throughput[['ValueSize', 'Ratio', 'Throughput']].groupby(
            ['ValueSize', 'Ratio']).max().reset_index()
        data[path] = max_throughput
    return data


log_file_paths = ['/root/workspace/deploy/perfcal/perfcal/shell/log/raft/perfcal/perfcal.log',
                  '/root/workspace/deploy/perfcal/perfcal/shell/log/raft/pgo/pgo.log']

grouped_data = process_log_files(log_file_paths)

plt.figure(figsize=(12, 6))

colors = ['blue', 'green']
labels = ['PerfCal-RaftKV', 'PGo-RaftKV']
allHatch = ['/', '-', '*', '\\', '+', 'o', 'O', '.',
            '**', 'OO', 'oo', 'xx', '++', '||', '\\', '//']
cmap = plt.get_cmap("tab10")

allColor = cmap(range(10))

config_labels = []
ticks = []
bar_width = 0.4

for i, (path, df) in enumerate(grouped_data.items()):
    def convertValueSize(valueSize):
        if valueSize == 1024:
            return '1K'
        elif valueSize == 10240:
            return '10K'
        elif valueSize == 102400:
            return '100K'
        elif valueSize == 1024000:
            return '1M'
        else:
            return str(valueSize)

    ticks.append(df.index + bar_width/2)
    config_label = df.apply(
        lambda row: f'{convertValueSize(int(row["ValueSize"]))}-{row["Ratio"]}', axis=1)
    config_labels.append(config_label)
    plt.bar(df.index + bar_width*i,
            df['Throughput'], color=allColor[i], width=bar_width, label=labels[i])
    # export data
    df.to_csv(f'data/csv/RaftMaxThroughputBarChart/{labels[i]}.csv')

plt.xlabel('Payload Size (Bytes) - Write Ratio', fontsize=30)
plt.ylabel('Throughput (op/s)', fontsize=30)

plt.xticks(ticks[0], labels=config_labels[0], rotation=45)

# plt.legend(fontsize=18)
plt.legend(loc='upper center', bbox_to_anchor=(
    0.5, 1.25), ncol=2, frameon=False, fontsize=30)

plt.tight_layout()

plt.subplots_adjust(top=0.85, bottom=0.35, left=0.12, right=0.98)

plt.savefig('data/raftThroughput.pdf', dpi=300)

plt.show()
