import pandas as pd
import matplotlib.pyplot as plt
import os
plt.rcParams.update({'font.size': 24})

if not os.path.exists('data/csv/MQmaxLatencyBarChart'):
    os.makedirs('data/csv/MQmaxLatencyBarChart')


def process_log_files(paths):
    data = {}
    for path in paths:
        df = pd.read_csv(path, header=None, names=[
                         'ValueSize', 'Threads', 'SubNumber', 'QoS', 'Latency'])

        def remove_extremes(group):
            if len(group) > 2:
                group = group.drop(group['Latency'].idxmax()).drop(
                    group['Latency'].idxmin())
            return group

        grouped = df.groupby(['Threads', 'ValueSize', 'QoS']).apply(
            remove_extremes).reset_index(drop=True)
        avg_latency = grouped.groupby(
            ['Threads', 'ValueSize', 'QoS']).mean().reset_index()
        min_latency = avg_latency[['ValueSize', 'QoS', 'Latency']].groupby(
            ['ValueSize', 'QoS']).min().reset_index()
        data[path] = min_latency
    return data


log_file_paths = ['/root/workspace/deploy/perfcal/perfcal/shell/log/mqtt/perfcal/latency1.log',
                  '/root/workspace/deploy/perfcal/perfcal/shell/log/mqtt/pgo/latency1.log',
                  '/root/workspace/deploy/perfcal/perfcal/shell/log/mqtt/emqx/latency1.log']
grouped_data = process_log_files(log_file_paths)
plt.figure(figsize=(12, 5))
colors = ['blue', 'green']
labels = ['PerfCal-MQ', 'PGo-MQ', 'EMQX']
width = 0.25
allHatch = ['/', '-', '*', '\\', '+', 'o', 'O', '.',
            '**', 'OO', 'oo', 'xx', '++', '||', '\\', '//']
cmap = plt.get_cmap("tab10")

allColor = cmap(range(10))
config_labels = []


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


for i, (path, df) in enumerate(grouped_data.items()):
    config_label = df.apply(
        lambda row: f'{convertValueSize(int(row["ValueSize"]))}-{int(row["QoS"])}', axis=1)
    config_labels.append(config_label)
    df['Latency'] = df['Latency'].apply(lambda x: x / 1000)
    print(df['Latency'])

    plt.bar(df.index + width*i, df['Latency'],
            color=allColor[i], width=width, label=labels[i])
    df.to_csv(f'data/csv/MQmaxLatencyBarChart/{labels[i % len(labels)]}.csv')

plt.xlabel('Payload Size (Bytes) - QoS', fontsize=30)
plt.ylabel('Latency (ms)', fontsize=30)
plt.xticks(range(len(config_labels[0])), labels=config_labels[0], rotation=45)

plt.legend(loc='upper center', bbox_to_anchor=(
    0.5, 1.3), ncol=3, frameon=False, fontsize=30)
plt.subplots_adjust(top=0.85, bottom=0.3, left=0.1, right=0.98)

plt.savefig('data/MQLatency.pdf', dpi=300)

plt.show()
