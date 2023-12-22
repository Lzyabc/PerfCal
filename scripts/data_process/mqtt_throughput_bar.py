import pandas as pd
import matplotlib.pyplot as plt
import os

plt.rcParams.update({'font.size': 24})

if not os.path.exists('data/csv/MQmaxThroughputBarChart'):
    os.makedirs('data/csv/MQmaxThroughputBarChart')


def process_log_files(paths):
    data = {}
    for path in paths:
        df = pd.read_csv(path, header=None, names=[
                         'Requests', 'Threads', 'SubNumber', 'ValueSize', 'QoS', 'Throughput'])

        def remove_extremes(group):
            if len(group) > 2:
                group = group.drop(group['Throughput'].idxmax()).drop(
                    group['Throughput'].idxmin())
            return group
        grouped = df.groupby(['Threads', 'ValueSize', 'QoS']).apply(
            remove_extremes).reset_index(drop=True)
        avg_throughput = grouped.groupby(
            ['Threads', 'ValueSize', 'QoS']).mean().reset_index()
        max_throughput = avg_throughput[['ValueSize', 'QoS', 'Throughput']].groupby(
            ['ValueSize', 'QoS']).max().reset_index()
        data[path] = max_throughput

    return data


log_file_paths = ['/root/workspace/deploy/profile/profile/shell/log/mqtt/profile/throughput.log',
                  '/root/workspace/deploy/profile/profile/shell/log/mqtt/pgo/throughput.log',
                  '/root/workspace/deploy/profile/profile/shell/log/mqtt/emqx/throughput.log']

log_file_paths = ['/root/workspace/deploy/profile/profile/shell/log/mqtt/profile/throughput.log',
                  '/root/workspace/deploy/profile/profile/shell/log/mqtt/pgo/throughput.log']

grouped_data = process_log_files(log_file_paths)

plt.figure(figsize=(12, 7))

colors = ['blue', 'green']
labels = ['PerfCal-MQ', 'PGo-MQ']

allHatch = ['/', '-', '*', '\\', '+', 'o', 'O', '.',
            '**', 'OO', 'oo', 'xx', '++', '||', '\\', '//']
cmap = plt.get_cmap("tab10")

allColor = cmap(range(10))

num_files = len(grouped_data)
bar_width = 0.4
group_width = num_files * bar_width
second_bar_center_offset = bar_width * 0.5
config_labels = []
second_bar_centers = []

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

    config_label = df.apply(
        lambda row: f'{convertValueSize(int(row["ValueSize"]))}-{int(row["QoS"])}', axis=1)
    config_labels.append(config_label)
    center_positions = df.index + second_bar_center_offset
    second_bar_centers.append(center_positions)
    plt.bar(df.index + bar_width * i,
            df['Throughput'], color=allColor[i], width=bar_width, label=labels[i])
    df.to_csv(f'data/csv/MQmaxThroughputBarChart/{labels[i]}.csv')

plt.xticks(second_bar_centers[0], labels=config_labels[0], rotation=45)

# plt.legend(frameon=False, fontsize=30)
plt.legend(loc='upper center', bbox_to_anchor=(
    0.5, 1.2), ncol=3, frameon=False, fontsize=30)

# plt.grid(True)
# plt.yscale("log")
plt.ylabel('Throughput (op/s)', fontsize=30)
plt.xlabel('Payload Size (Bytes) - QoS', fontsize=30)

plt.tight_layout()

plt.subplots_adjust(top=0.9, bottom=0.25, left=0.15, right=0.98)

plt.savefig('data/MQThroughput.pdf', dpi=300)

plt.show()
